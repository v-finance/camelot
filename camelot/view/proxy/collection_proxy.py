#  ============================================================================
#
#  Copyright (C) 2007-2012 Conceptive Engineering bvba. All rights reserved.
#  www.conceptive.be / project-camelot@conceptive.be
#
#  This file is part of the Camelot Library.
#
#  This file may be used under the terms of the GNU General Public
#  License version 2.0 as published by the Free Software Foundation
#  and appearing in the file license.txt included in the packaging of
#  this file.  Please review this information to ensure GNU
#  General Public Licensing requirements will be met.
#
#  If you are unsure which license is appropriate for your use, please
#  visit www.python-camelot.com or contact project-camelot@conceptive.be
#
#  This file is provided AS IS with NO WARRANTY OF ANY KIND, INCLUDING THE
#  WARRANTY OF DESIGN, MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE.
#
#  For use of this library in commercial applications, please contact
#  project-camelot@conceptive.be
#
#  ============================================================================

"""Proxy representing a collection of entities that live in the model thread.

The proxy represents them in the gui thread and provides access to the data
with zero delay.  If the data is not yet present in the proxy, dummy data is
returned and an update signal is emitted when the correct data is available.
"""

import logging
logger = logging.getLogger( 'camelot.view.proxy.collection_proxy' )

import datetime
import itertools

from PyQt4.QtCore import Qt, QThread
from PyQt4 import QtGui, QtCore

from camelot.core.exception import log_programming_error
from camelot.core.utils import is_deleted, variant_to_pyobject
from camelot.view.art import Icon
from camelot.view.fifo import Fifo
from camelot.view.controls import delegates
from camelot.view.controls.exception import register_exception
from camelot.view.remote_signals import get_signal_handler
from camelot.view.model_thread import object_thread, \
                                      model_function, post

from camelot.core.files.storage import StoredImage

class ProxyDict(dict):
    """Subclass of dictionary to fool the QVariant object and prevent
    it from converting dictionary keys to whatever Qt object, but keep
    everything python"""
    pass

class DelayedProxy( object ):
    """A proxy object needs to be constructed within the GUI thread. Construct
    a delayed proxy when the construction of a proxy is needed within the Model
    thread.  On first occasion the delayed proxy will be converted to a real
    proxy within the GUI thread
    """

    @model_function
    def __init__( self, admin, collection_getter, columns_getter ):
        self._admin = admin
        self._collection_getter = collection_getter
        self._columns_getter = columns_getter

    def __call__( self ):
        return CollectionProxy( self._admin,
                                self._collection_getter,
                                self._columns_getter )

    def __unicode__(self):
        collection = self._collection_getter()
        if collection:
            try:
               return u','.join(list(unicode(o) or '' for o,_i in zip(collection,
                                                                      range(3))))
            except TypeError, e:
               logger.error( 'could not convert object to unicode', exc_info=e )
        return u''

@model_function
def strip_data_from_object( obj, columns ):
    """For every column in columns, get the corresponding value from the
    object.  Getting a value from an object is time consuming, so using
    this function should be minimized.
    :param obj: the object of which to get data
    :param columns: a list of columns for which to get data
    """
    row_data = []

    def create_collection_getter( o, attr ):
        return lambda: getattr( o, attr )

    for _i, col in enumerate( columns ):
        field_attributes = col[1]
        field_value = None
        try:
            getter = field_attributes['getter']
            if field_attributes['python_type'] == list:
                field_value = DelayedProxy( field_attributes['admin'],
                                            create_collection_getter( obj, col[0] ),
                                            field_attributes['admin'].get_columns )
            else:
                field_value = getter( obj )
        except (Exception, RuntimeError, TypeError, NameError), e:
            message = "could not get field '%s' of object of type %s"%(col[0], obj.__class__.__name__)
            log_programming_error( logger, 
                                   message,
                                   exc_info = e )
        finally:
            row_data.append( field_value )
    return row_data

@model_function
def stripped_data_to_unicode( stripped_data, obj, static_field_attributes, dynamic_field_attributes ):
    """Extract for each field in the row data a 'visible' form of
    data"""

    row_data = []

    for field_data, static_attributes, dynamic_attributes in zip( stripped_data, static_field_attributes, dynamic_field_attributes ):
        unicode_data = u''
        try:
            choices = dynamic_attributes.get( 'choices', static_attributes.get('choices', None))
            if 'unicode_format' in static_attributes:
                unicode_format = static_attributes['unicode_format']
                if field_data != None:
                    unicode_data = unicode_format( field_data )
            elif choices:
                unicode_data = field_data
                for key, value in choices:
                    if key == field_data:
                        unicode_data = value
            elif isinstance( field_data, list ):
                unicode_data = u'.'.join( [unicode( e ) for e in field_data] )
            elif isinstance( field_data, datetime.datetime ):
                # datetime should come before date since datetime is a subtype of date
                if field_data.year >= 1900:
                    unicode_data = field_data.strftime( '%d/%m/%Y %H:%M' )
            elif isinstance( field_data, datetime.date ):
                if field_data.year >= 1900:
                    unicode_data = field_data.strftime( '%d/%m/%Y' )
            elif isinstance( field_data, StoredImage):
                unicode_data = field_data.checkout_thumbnail(100, 100)
            elif field_data != None:
                unicode_data = unicode( field_data )
        except (Exception, RuntimeError, TypeError, NameError), e:
            log_programming_error( logger,
                                   "Could not get view data for field '%s' with of object of type %s"%( static_attributes['name'],
                                                                                                        obj.__class__.__name__),
                                   exc_info = e )
        finally:
            row_data.append( unicode_data )

    return row_data

from camelot.view.proxy import ValueLoading

class EmptyRowData( object ):
    def __getitem__( self, column ):
        return ValueLoading

empty_row_data = EmptyRowData()

class SortingRowMapper( dict ):
    """Class mapping rows of a collection 1:1 without sorting
    and filtering, unless a mapping has been defined explicitly"""

    def __getitem__(self, row):
        try:
            return super(SortingRowMapper, self).__getitem__(row)
        except KeyError:
            return row

class CollectionProxy( QtGui.QProxyModel ):
    """The CollectionProxy contains a limited copy of the data in the actual
    collection, usable for fast visualisation in a QTableView

    the CollectionProxy has some class attributes that can be overwritten when
    subclassing it :

    * header_icon : the icon to be used in the vertical header

    """

    _header_font = QtGui.QApplication.font()
    _header_font_required = QtGui.QApplication.font()
    _header_font_required.setBold( True )

    header_icon = Icon( 'tango/16x16/places/folder.png' )

    item_delegate_changed_signal = QtCore.pyqtSignal()
    row_changed_signal = QtCore.pyqtSignal(int)
    exception_signal = QtCore.pyqtSignal(object)
    rows_removed_signal = QtCore.pyqtSignal()

    def __init__( self, 
                  admin, 
                  collection_getter, 
                  columns_getter,
                  max_number_of_rows = 10, 
                  flush_changes = True,
                  cache_collection_proxy = None
                  ):
        """
:param admin: the admin interface for the items in the collection

:param collection_getter: a function that takes no arguments and returns
the collection that will be visualized. This function will be called inside
the model thread, to prevent delays when this function causes the database
to be hit.  If the collection is a list, it should not contain any duplicate
elements.

:param columns_getter: a function that takes no arguments and returns the
columns that will be cached in the proxy. This function will be called
inside the model thread.

:param cache_collection_proxy: the CollectionProxy on which this CollectionProxy
will reuse the cache. Passing a cache has the advantage that objects that were
present in the original cache will remain at the same row in the new cache
This is used when a form is created from a tableview.  Because between the last
query of the tableview, and the first of the form, the object might have changed
position in the query.
"""
        super(CollectionProxy, self).__init__()
        assert object_thread( self )
        from camelot.view.model_thread import get_model_thread
        #
        # The source model will contain the actual data stripped from the
        # objects in the collection.
        #
        self.source_model = QtGui.QStandardItemModel()
        self.setModel( self.source_model )
        
        self.logger = logging.getLogger(logger.name + '.%s'%id(self))
        self.logger.debug('initialize query table for %s' % (admin.get_verbose_name()))
        self._mutex = QtCore.QMutex()
        self.admin = admin
        self.settings = self.admin.get_settings()
        self._horizontal_header_height = QtGui.QFontMetrics( self._header_font_required ).height() + 10
        self._header_font_metrics = QtGui.QFontMetrics( self._header_font )
        vertical_header_font_height = QtGui.QFontMetrics( self._header_font ).height()
        self._vertical_header_height = vertical_header_font_height * self.admin.lines_per_row + 10
        self.iconSize = QtCore.QSize( vertical_header_font_height,
                                      vertical_header_font_height )
        if self.header_icon:
            self.form_icon = QtCore.QVariant( self.header_icon.getQIcon().pixmap( self.iconSize ) )
        else:
            self.form_icon = QtCore.QVariant()
        self.validator = admin.create_validator( self )
        self._collection_getter = collection_getter
        self.flush_changes = flush_changes
        self.delegate_manager = None
        self.mt = get_model_thread()
        # Set database connection and load data
        self._rows = 0
        self._columns = []
        self._static_field_attributes = []
        self._max_number_of_rows = max_number_of_rows
        max_cache = 10 * self.max_number_of_rows
        if cache_collection_proxy:
            cached_entries = len( cache_collection_proxy.display_cache )
            max_cache = max( cached_entries, max_cache )
            self.display_cache = cache_collection_proxy.display_cache.shallow_copy( max_cache )
            self.edit_cache = cache_collection_proxy.edit_cache.shallow_copy( max_cache )
            self.attributes_cache = cache_collection_proxy.attributes_cache.shallow_copy( max_cache )
        else:        
            self.display_cache = Fifo( max_cache )
            self.edit_cache = Fifo( max_cache )
            self.attributes_cache = Fifo( max_cache )
        # The rows in the table for which a cache refill is under request
        self.rows_under_request = set()
        self._update_requests = list()
        # The rows that have unflushed changes
        self.unflushed_rows = set()
        self._sort_and_filter = SortingRowMapper()
        self.row_changed_signal.connect( self._emit_changes )
        self.rsh = get_signal_handler()
        self.rsh.connect_signals( self )

        def get_columns():
            self._columns = columns_getter()
            self._static_field_attributes = list(self.admin.get_static_field_attributes([c[0] for c in self._columns]))
            return self._columns

        post( get_columns, self.setColumns )
#    # the initial collection might contain unflushed rows
        post( self._update_unflushed_rows )
#    # in that way the number of rows is requested as well
        if cache_collection_proxy:
            self.setRowCount( cache_collection_proxy.rowCount() )
        else:
            post( self.getRowCount, self.setRowCount )
        self.logger.debug( 'initialization finished' )

    #
    # Reimplementation of methods of QProxyModel, because for now, we only
    # use the proxy to store header data
    # 
    # Subsequent calls to this function should return the same index
    #
    def index( self, row, col, parent = QtCore.QModelIndex() ):
        assert object_thread( self )
        if self.hasIndex( row, col, parent):
            #
            # indexes are considered equal when their row, column and internal
            # pointer are equal.  therefor set the internal pointer always to 0.
            #
            return self.createIndex( row, col, 0 )
        return QtCore.QModelIndex()
    
    def parent( self, child ):
        assert object_thread( self )
        return QtCore.QModelIndex()
    
    def rowCount( self, index = None ):
        return self._rows
    
    def hasChildren( self, parent ):
        assert object_thread( self )
        return False
    
    #
    # end or reimplementation
    #
    
    #
    # begin functions related to drag and drop
    #
    
    def mimeTypes( self ):
        assert object_thread( self )
        if self.admin.drop_action != None:
            return self.admin.drop_action.drop_mime_types
        
    def supportedDropActions( self ):
        assert object_thread( self )
        if self.admin.drop_action != None:
            return Qt.CopyAction | Qt.MoveAction | Qt.LinkAction
        return None
    
    def dropMimeData( self, mime_data, action, row, column, parent ):
        assert object_thread( self )
        #print mime_data, [unicode(f) for f in mime_data.formats()]
        return True
    
    #
    # end of drag and drop related functions
    #
    
    @property
    def max_number_of_rows(self):
        """The maximum number of rows to be displayed at once"""
        return self._max_number_of_rows

    def get_validator(self):
        return self.validator

    def map_to_source(self, sorted_row_number):
        """Converts a sorted row number to a row number of the source
        collection"""
        return self._sort_and_filter[sorted_row_number]

    @model_function
    def _update_unflushed_rows( self ):
        """Verify all rows to see if some of them should be added to the
        unflushed rows"""
        for i, e in enumerate( self.get_collection() ):
            if hasattr(e, 'id') and not e.id:
                self.unflushed_rows.add( i )

    def hasUnflushedRows( self ):
        """The model has rows that have not been flushed to the database yet,
        because the row is invalid
        """
        has_unflushed_rows = ( len( self.unflushed_rows ) > 0 )
        self.logger.debug( 'hasUnflushed rows : %s' % has_unflushed_rows )
        return has_unflushed_rows

    @model_function
    def getRowCount( self ):
        # make sure we don't count an object twice if it is twice
        # in the list, since this will drive the cache nuts
        rows = len( set( self.get_collection() ) )
        return rows

    def refresh( self ):
        assert object_thread( self )
        post( self.getRowCount, self._refresh_content )

    @QtCore.pyqtSlot(int)
    def _refresh_content(self, rows ):
        assert object_thread( self )
        locker = QtCore.QMutexLocker(self._mutex)
        self.display_cache = Fifo( 10 * self.max_number_of_rows )
        self.edit_cache = Fifo( 10 * self.max_number_of_rows )
        self.attributes_cache = Fifo( 10 * self.max_number_of_rows )
        self.rows_under_request = set()
        self.unflushed_rows = set()
        # once the cache has been cleared, no updates ought to be accepted
        self._update_requests = list()
        locker.unlock()
        self.setRowCount( rows )

    def set_collection_getter( self, collection_getter ):
        self.logger.debug('set collection getter')
        self._collection_getter = collection_getter
        self.refresh()

    @model_function
    def get_collection( self ):
        return self._collection_getter()

    def handleRowUpdate( self, row ):
        """Handles the update of a row when this row might be out of date"""
        assert object_thread( self )
        self.display_cache.delete_by_row( row )
        self.edit_cache.delete_by_row( row )
        self.attributes_cache.delete_by_row( row )
        self.dataChanged.emit( self.index( row, 0 ),
                               self.index( row, self.columnCount() - 1 ) )

    @QtCore.pyqtSlot( object, object )
    def handle_entity_update( self, sender, entity ):
        """Handles the entity signal, indicating that the model is out of
        date"""
        assert object_thread( self )
        self.logger.debug( '%s %s received entity update signal' % \
                     ( self.__class__.__name__, self.admin.get_verbose_name() ) )
        if sender != self:
            try:
                row = self.display_cache.get_row_by_entity( entity )
            except KeyError:
                self.logger.debug( 'entity not in cache' )
                return
            #
            # Because the entity is updated, it might no longer be in our
            # collection, therefore, make sure we don't access the collection
            # to strip data of the entity
            #
            def create_entity_update(row, entity):

                def entity_update():
                    columns = self._columns
                    self._add_data(columns, row, entity)
                    return row

                return entity_update

            post(create_entity_update(row, entity), self._emit_changes)
        else:
            self.logger.debug( 'duplicate update' )

    @QtCore.pyqtSlot( object, object )
    def handle_entity_delete( self, sender, entity ):
        """Handles the entity signal, indicating that the model is out of
        date"""
        assert object_thread( self )
        self.logger.debug( 'received entity delete signal' )
        if sender != self:
            try:
                row = self.display_cache.get_row_by_entity(entity)
            except KeyError:
                self.logger.debug( 'entity not in cache' )
                return
            self.remove_rows( [row], delete = False )

    @QtCore.pyqtSlot( object, object )
    def handle_entity_create( self, sender, entity ):
        """Handles the entity signal, indicating that the model is out of
        date"""
        assert object_thread( self )
        self.logger.debug( 'received entity create signal' )
        # @todo : decide what to do when a new entity has been created,
        #         probably do nothing
        return

    @QtCore.pyqtSlot(int)
    def setRowCount( self, rows ):
        """Callback method to set the number of rows
        @param rows the new number of rows
        """
        assert object_thread( self )
        self._rows = rows
        self.layoutChanged.emit()

    def getItemDelegate( self ):
        """:return: a DelegateManager for this model, or None if no DelegateManager yet available
        a DelegateManager will be available once the item_delegate_changed signal has been emitted"""
        assert object_thread( self )
        self.logger.debug( 'getItemDelegate' )
        return self.delegate_manager

    def getColumns( self ):
        """:return: the columns as set by the setColumns method"""
        return self._columns

    @QtCore.pyqtSlot(object)
    def setColumns( self, columns ):
        """Callback method to set the columns

        :param columns: a list with fields to be displayed of the form [('field_name', field_attributes), ...] as
        returned by the getColumns method of the ElixirAdmin class
        """
        assert object_thread( self )
        self.logger.debug( 'setColumns' )
        self._columns = columns

        delegate_manager = delegates.DelegateManager()
        delegate_manager.set_columns_desc( columns )

        # set a delegate for the vertical header
        delegate_manager.insertColumnDelegate( -1, delegates.PlainTextDelegate( parent = delegate_manager ) )
        index = QtCore.QModelIndex()
        option = QtGui.QStyleOptionViewItem()
        self.settings.beginGroup( 'column_width' )
        self.settings.beginGroup( '0' )

        #
        # this loop can take a while to complete, so processEvents is called regulary
        #
        for i, c in enumerate( columns ):
            #
            # Construct the delegate
            #
            field_name = c[0]
            self.logger.debug( 'creating delegate for %s' % field_name )
            try:
                delegate = c[1]['delegate']( parent = delegate_manager, **c[1] )
            except Exception, e:
                log_programming_error( logger, 
                                       'Could not create delegate for field %s'%field_name,
                                       exc_info = e )
                delegate = delegates.PlainTextDelegate( parent = delegate_manager, **c[1] )
            delegate_manager.insertColumnDelegate( i, delegate )
            #
            # Set the header data
            #
            header_item = QtGui.QStandardItem()
            header_item.setData( QtCore.QVariant( unicode(c[1]['name']) ),
                                 Qt.DisplayRole )
            if c[1].get( 'nullable', True ) == False:
                header_item.setData( self._header_font_required,
                                     Qt.FontRole )
            else:
                header_item.setData( self._header_font,
                                     Qt.FontRole )

            settings_width = int( variant_to_pyobject( self.settings.value( field_name, 0 ) ) )
            label_size = QtGui.QFontMetrics( self._header_font_required ).size( Qt.TextSingleLine, unicode(c[1]['name']) + u' ' )
            minimal_widths = [ label_size.width() + 10 ]
            if 'minimal_column_width' in c[1]:
                minimal_widths.append( self._header_font_metrics.averageCharWidth() * c[1]['minimal_column_width'] )
            if c[1].get('editable', True) != False:
                minimal_widths.append( delegate.sizeHint( option, index ).width() )
            column_width = c[1].get( 'column_width', None )
            if column_width != None:
                minimal_widths = [ self._header_font_metrics.averageCharWidth() * column_width ]
                    
            if settings_width:
                header_item.setData( QtCore.QVariant( QtCore.QSize( settings_width, self._horizontal_header_height ) ),
                                     Qt.SizeHintRole )
            else:
                header_item.setData( QtCore.QVariant( QtCore.QSize( max( minimal_widths ), self._horizontal_header_height ) ),
                                     Qt.SizeHintRole )
             
            self.source_model.setHorizontalHeaderItem( i, header_item )
        
        self.settings.endGroup()
        self.settings.endGroup()
        # Only set the delegate manager when it is fully set up
        self.delegate_manager = delegate_manager
        self.item_delegate_changed_signal.emit()
            
    def setHeaderData( self, section, orientation, value, role ):
        assert object_thread( self )
        if orientation == Qt.Horizontal:
            if role == Qt.SizeHintRole:
                width = value.width()
                self.settings.beginGroup( 'column_width' )
                self.settings.beginGroup( '0' )
                self.settings.setValue( self._columns[section][1]['field_name'], 
                                        width )
                self.settings.endGroup()
                self.settings.endGroup()
        return super( CollectionProxy, self ).setHeaderData( section,
                                                             orientation,
                                                             value,
                                                             role )
    
    def headerData( self, section, orientation, role ):
        """In case the columns have not been set yet, don't even try to get
        information out of them
        """
        assert object_thread( self )
        if orientation == Qt.Vertical:
            if role == Qt.SizeHintRole:
                if self.header_icon != None:
                    return QtCore.QVariant( QtCore.QSize( self.iconSize.width() + 10,
                                                          self._vertical_header_height ) )
                else:
                    # if there is no icon, the line numbers will be displayed, so create some space for those
                    return QtCore.QVariant( QtCore.QSize( QtGui.QFontMetrics( self._header_font ).size( Qt.TextSingleLine, str(self._rows) ).width() + 10, self._vertical_header_height ) )
            if role == Qt.DecorationRole:
                return self.form_icon
            elif role == Qt.DisplayRole:
                if self.header_icon != None:
                    return QtCore.QVariant( '' )
        return super( CollectionProxy, self ).headerData( section, orientation, role )

    def sort( self, column, order ):
        """reimplementation of the :class:`QtGui.QAbstractItemModel` its sort function"""
        assert object_thread( self )

        def create_sort(column, order):

            def sort():
                unsorted_collection = [(i,o) for i,o in enumerate(self.get_collection())]
                field_name = self._columns[column][0]
                
                # handle the case of one of the values being None
                def compare_none( line_1, line_2 ):
                    key_1, key_2 = None, None
                    try:
                        key_1 = getattr( line_1[1], field_name )
                    except Exception, e:
                        logger.error( 'could not get attribute %s from object'%field_name, exc_info = e )
                    try:
                        key_2 = getattr( line_2[1], field_name )
                    except Exception, e:
                        logger.error( 'could not get attribute %s from object'%field_name, exc_info = e )
                    if key_1 == None and key_2 == None:
                        return 0
                    if key_1 == None:
                        return -1
                    if key_2 == None:
                        return 1
                    return cmp( key_1, key_2 )
                    
                unsorted_collection.sort( cmp = compare_none, reverse = order )
                for j,(i,_o) in enumerate(unsorted_collection):
                    self._sort_and_filter[j] = i
                return len(unsorted_collection)

            return sort

        post(create_sort(column, order), self._refresh_content)

    def data( self, index, role = Qt.DisplayRole):
        """:return: the data at index for the specified role
        This function will return ValueLoading when the data has not
        yet been fetched from the underlying model.  It will then send
        a request to the model thread to fetch this data.  Once the data
        is readily available, the dataChanged signal will be emitted

        Using Qt.UserRole as a role will return all the field attributes
        of the index.
        
        Using Qt.UserRole+1 will return the object of which an attribute
        is displayed in that specific cell
        
        """
        assert object_thread( self )
        if not index.isValid() or \
           not ( 0 <= index.row() <= self.rowCount( index ) ) or \
           not ( 0 <= index.column() <= self.columnCount() ):
            return QtCore.QVariant()
        if role in (Qt.EditRole, Qt.DisplayRole):
            if role == Qt.EditRole:
                cache = self.edit_cache
            else:
                cache = self.display_cache
            data = self._get_row_data( index.row(), cache )
            value = data[index.column()]
            if isinstance( value, DelayedProxy ):
                value = value()
                # store the created proxy, to prevent recreation of it
                # afterwards.
                data[index.column()] = value
            if isinstance( value, datetime.datetime ):
                # Putting a python datetime into a QVariant and returning
                # it to a PyObject seems to be buggy, therefore we chop the
                # microseconds
                if value:
                    value = QtCore.QDateTime(value.year, value.month,
                                             value.day, value.hour,
                                             value.minute, value.second)
            return QtCore.QVariant( value )
        elif role == Qt.ToolTipRole:
            return QtCore.QVariant(self._get_field_attribute_value(index, 'tooltip'))
        elif role == Qt.BackgroundRole:
            return QtCore.QVariant(self._get_field_attribute_value(index, 'background_color') or QtCore.QVariant())
        elif role == Qt.UserRole:
            field_attributes = ProxyDict(self._static_field_attributes[index.column()])
            dynamic_field_attributes = self._get_row_data( index.row(), self.attributes_cache )[index.column()]
            if dynamic_field_attributes != ValueLoading:
                field_attributes.update( dynamic_field_attributes )
            return QtCore.QVariant(field_attributes)
        elif role == Qt.UserRole + 1:
            try:
                return QtCore.QVariant( self.edit_cache.get_entity_at_row( index.row() ) )
            except KeyError:
                return QtCore.QVariant( ValueLoading )
        return QtCore.QVariant()

    def _get_field_attribute_value(self, index, field_attribute):
        """Get the values for the static and the dynamic field attributes at once
        :return: the value of the field attribute"""
        try:
            return self._static_field_attributes[index.column()][field_attribute]
        except KeyError:
            value = self._get_row_data( index.row(), self.attributes_cache )[index.column()]
            if value == ValueLoading:
                return None
            return value.get(field_attribute, None)

    @model_function
    def _handle_update_requests(self):
        #
        # Copy the update requests and clear the list of requests
        #
        locker = QtCore.QMutexLocker(self._mutex)
        update_requests = [u for u in self._update_requests]
        self._update_requests = []
        locker.unlock()
        #
        # Handle the requests
        #
        return_list = []
        for flushed, row, column, value in update_requests:
            attribute, field_attributes = self._columns[column]

            from sqlalchemy.exc import DatabaseError
            new_value = value()
            self.logger.debug( 'set data for row %s;col %s' % ( row, column ) )

            if new_value == ValueLoading:
                return None

            #
            # don't use _get_object, but only update objects which are in the
            # cache, otherwise it is not sure that the object updated is the
            # one that was edited
            #
            o = self.edit_cache.get_entity_at_row( row )
            if not o:
                # the object might have been deleted from the collection while the editor
                # was still open
                self.logger.debug( 'this object is no longer in the collection' )
                try:
                    self.unflushed_rows.remove( row )
                except KeyError:
                    pass
                return
            
            #
            # the object might have been deleted while an editor was open
            # 
            if self.admin.is_deleted( o ):
                return

            old_value = getattr( o, attribute )
            #
            # When the value is a related object, the related object might have changed
            #
            changed = ( new_value != old_value ) or (
              field_attributes.get('embedded', False) and \
              field_attributes.get('target', False))
            #
            # In case the attribute is a OneToMany or ManyToMany, we cannot simply compare the
            # old and new value to know if the object was changed, so we'll
            # consider it changed anyway
            #
            direction = field_attributes.get( 'direction', None )
            if direction in ( 'manytomany', 'onetomany' ):
                changed = True
            if changed:
                # update the model
                try:
                    setattr( o, attribute, new_value )
                    #
                    # setting this attribute, might trigger a default function to return a value,
                    # that was not returned before
                    #
                    self.admin.set_defaults( o, include_nullable_fields=False )
                except AttributeError, e:
                    self.logger.error( u"Can't set attribute %s to %s" % ( attribute, unicode( new_value ) ), exc_info = e )
                except TypeError:
                    # type error can be raised in case we try to set to a collection
                    pass
                if self.flush_changes and self.validator.isValid( row ):
                    # save the state before the update
                    try:
                        self.admin.flush( o )
                    except DatabaseError, e:
                        #@todo: when flushing fails, the object should not be removed from the unflushed rows ??
                        self.logger.error( 'Programming Error, could not flush object', exc_info = e )
                    locker.relock()
                    try:
                        self.unflushed_rows.remove( row )
                    except KeyError:
                        pass
                    locker.unlock()
                # update the cache
                self._add_data(self._columns, row, o)
                #@todo: update should only be sent remotely when flush was done
                self.rsh.sendEntityUpdate( self, o )
                for depending_obj in self.admin.get_depending_objects( o ):
                    self.rsh.sendEntityUpdate( self, depending_obj )
                return_list.append(( ( row, 0 ), ( row, len( self._columns ) ) ))
            elif flushed:
                locker.relock()
                self.logger.debug( 'old value equals new value, no need to flush this object' )
                try:
                    self.unflushed_rows.remove( row )
                except KeyError:
                    pass
                locker.unlock()
        return return_list

    def setData( self, index, value, role = Qt.EditRole ):
        """Value should be a function taking no arguments that returns the data to
        be set

        This function will then be called in the model_thread
        """
        assert object_thread( self )
        #
        # prevent data of being set in rows not actually in this model
        #
        if (not index.isValid()) or (index.model()!=self):
            return False
        
        if role == Qt.EditRole:

            # if the field is not editable, don't waste any time and get out of here
            # editable should be explicitely True, since the _get_field_attribute_value
            # might return intermediary values such as ValueLoading ??
            if self._get_field_attribute_value(index, 'editable') != True:
                return

            locker = QtCore.QMutexLocker( self._mutex )
            flushed = ( index.row() not in self.unflushed_rows )
            self.unflushed_rows.add( index.row() )
            self._update_requests.append( (flushed, index.row(), index.column(), value) )
            locker.unlock()
            post( self._handle_update_requests )

        return True

    @QtCore.pyqtSlot(int)
    def _emit_changes( self, row ):
        assert object_thread( self )
        if row!=None:
            column_count = self.columnCount()
            top_left = self.index( row, 0 )
            bottom_right = self.index( row, column_count - 1 )
            self.dataChanged.emit( top_left, bottom_right )

    def flags( self, index ):
        """Returns the item flags for the given index"""
        assert object_thread( self )
        flags = Qt.ItemIsEnabled | Qt.ItemIsSelectable
        if self._get_field_attribute_value(index, 'editable'):
            flags = flags | Qt.ItemIsEditable
        if self.admin.drop_action != None:
            flags = flags | Qt.ItemIsDropEnabled
        return flags

    def _add_data(self, columns, row, obj):
        """Add data from object o at a row in the cache
        :param columns: the columns of which to strip data
        :param row: the row in the cache into which to add data
        :param obj: the object from which to strip the data
        """
        if not self.admin.is_deleted( obj ):
            row_data = strip_data_from_object( obj, columns )
            dynamic_field_attributes = list(self.admin.get_dynamic_field_attributes( obj, (c[0] for c in columns)))
            static_field_attributes = self.admin.get_static_field_attributes( (c[0] for c in columns) )
            unicode_row_data = stripped_data_to_unicode( row_data, obj, static_field_attributes, dynamic_field_attributes )
        else:
            row_data = [None] * len(columns)
            dynamic_field_attributes =  [{'editable':False}] * len(columns)
            static_field_attributes = self.admin.get_static_field_attributes( (c[0] for c in columns) )
            unicode_row_data = [u''] * len(columns)
        locker = QtCore.QMutexLocker( self._mutex )
        self.edit_cache.add_data( row, obj, row_data )
        self.display_cache.add_data( row, obj, unicode_row_data )
        self.attributes_cache.add_data(row, obj, dynamic_field_attributes )
        locker.unlock()
        #
        # it might be that the CollectionProxy is deleted on the QT side of
        # the application
        #
        if not is_deleted( self ):
            self.row_changed_signal.emit( row )

    def _skip_row(self, row, obj):
        """:return: True if the object obj is already in the cache, but at a
        different row then row.  If this is the case, this object should not
        be put in the cache at row, and this row should be skipped alltogether.
        """
        try:
            return self.edit_cache.get_row_by_entity(obj)!=row
        except KeyError:
            pass
        return False

    def _offset_and_limit_rows_to_get( self ):
        """From the current set of rows to get, find the first
        continuous range of rows that should be fetched.
        :return: (offset, limit)
        """
        offset, limit, previous_length, i = 0, 0, 0, 0
        #
        # wait for a while until the rows under request don't change any
        # more
        #
        locker = QtCore.QMutexLocker(self._mutex)
        while previous_length != len(self.rows_under_request):
            previous_length = len(self.rows_under_request)
            locker.unlock()
            QThread.msleep(5)
            locker.relock()
        #
        # now filter out all rows that have been put in the cache
        # the gui thread didn't know about
        #
        rows_to_get = self.rows_under_request
        rows_already_there = set()
        for row in rows_to_get:
            if self.edit_cache.has_data_at_row(row):
                rows_already_there.add(row)
        rows_to_get.difference_update( rows_already_there )
        #
        # see if there is anything left to do
        #
        try:
            if rows_to_get:
                rows_to_get = list(rows_to_get)
                locker.unlock()
                rows_to_get.sort()
                offset = rows_to_get[0]
                #
                # find first discontinuity
                #
                for i in range(offset, rows_to_get[-1]+1):
                    if rows_to_get[i-offset] != i:
                        break
                limit = i - offset + 1
        except IndexError, e:
            logger.error('index error with rows_to_get %s'%unicode(rows_to_get), exc_info=e)
            raise e
        return (offset, limit)

    @model_function
    def _extend_cache( self ):
        """Extend the cache around the rows under request"""
        offset, limit = self._offset_and_limit_rows_to_get()
        if limit:
            columns = self._columns
            collection = self.get_collection()
            skipped_rows = 0
            for i in range(offset, min(offset + limit + 1, self._rows)):
                object_found = False
                while not object_found:
                    unsorted_row = self._sort_and_filter[i]
                    obj = collection[unsorted_row+skipped_rows]
                    if self._skip_row(i, obj):
                        skipped_rows = skipped_rows + 1
                    else:
                        self._add_data(columns, i, obj)
                        object_found = True
        return ( offset, limit )

    @model_function
    def _get_object( self, sorted_row_number ):
        """Get the object corresponding to row
        :return: the object at row row or None if the row index is invalid
        """
        try:
            # first try to get the primary key out of the cache, if it's not
            # there, query the collection_getter
            return self.edit_cache.get_entity_at_row( sorted_row_number )
        except KeyError:
            pass
        try:
            return self.get_collection()[self.map_to_source(sorted_row_number)]
        except IndexError:
            pass
        return None

    @QtCore.pyqtSlot(tuple)
    def _cache_extended( self, interval ):
        offset, limit = interval
        locker = QtCore.QMutexLocker(self._mutex)
        self.rows_under_request.difference_update( set( range( offset, offset + limit + 1) ) )
        locker.unlock()

    def _get_row_data( self, row, cache ):
        """Get the data which is to be visualized at a certain row of the
        table, if needed, post a refill request the cache to get the object
        and its neighbours in the cache, meanwhile, return an empty object
        :param row: the row of the table for which to get the data
        :param cache: the cache out of which to get row data
        :return: row_data
        """
        try:
            data = cache.get_data_at_row( row )
            #
            # check if data is None, then the cache was a copy of previous
            # cache, and the data should be refetched
            #
            if data is None:
                raise KeyError
            return data
        except KeyError:
            if row not in self.rows_under_request:
                locker = QtCore.QMutexLocker(self._mutex)
                self.rows_under_request.add( row )
                locker.unlock()
                post( self._extend_cache, self._cache_extended )
            return empty_row_data

    @model_function
    def remove( self, o ):
        collection = self.get_collection()
        if o in collection:
            collection.remove( o )
            self._rows -= 1

    @model_function
    def append( self, o ):
        collection = self.get_collection()
        if o not in collection:
            collection.append( o )

    @model_function
    def remove_objects( self, objects_to_remove, delete = True ):
        """
        :param objects_to_remove: a list of objects that need to be removed
        from the collection
        :param delete: True if the objects need to be deleted
        """
        #
        # it might be impossible to determine the depending objects once
        # the object has been removed from the collection
        #
        depending_objects = set( itertools.chain.from_iterable( self.admin.get_depending_objects( o ) for o in objects_to_remove ) )
        for obj in objects_to_remove:
            #
            # We should not update depending objects that have
            # been deleted themselves
            #
            if delete:
                try:
                    depending_objects.remove( obj )
                except KeyError:
                    pass
            #
            # if needed, delete the objects
            #
            if delete:
                self.rsh.sendEntityDelete( self, obj )
                self.admin.delete( obj )
                # remove only when delete took place without exception
                self.remove( obj )
            else:
                # even if the object is not deleted, it needs to be flushed to make
                # sure the persisted object is out of the collection as well
                self.remove( obj )
                if self.admin.is_persistent( obj ):
                    self.admin.flush( obj )
            #
            # remove the entity from the cache, only if the delete and remove
            # took place without exception
            #
            self.display_cache.delete_by_entity( obj )
            self.attributes_cache.delete_by_entity( obj )
            self.edit_cache.delete_by_entity( obj )
        for depending_obj in depending_objects:
            self.rsh.sendEntityUpdate( self, depending_obj )
        post( self.getRowCount, self._refresh_content )

    def remove_rows( self, rows, delete = True ):
        """Remove the entity associated with this row from this collection
        @param rows: a list with the numbers of the rows to remove
        @param delete: delete the entity as well
        
        The rows_removed signal will be emitted when the removal was 
        successful, otherwise the exception_signal will be emitted.
        """
        assert object_thread( self )
        self.logger.debug( 'remove rows' )

        def create_delete_function( rows ):

            def delete_function():
                """Remove all rows from the underlying collection
                :return: the number of rows left in the collection"""
                try:
                    objects_to_remove = [self._get_object( row ) for row in rows]
                    self.remove_objects( objects_to_remove, delete )
                    self.rows_removed_signal.emit()
                except Exception, exc:
                    exc_info = register_exception( logger,
                                                   'exception while removing rows',
                                                   exc )
                    self.exception_signal.emit( exc_info )

            return delete_function

        post( create_delete_function(rows) )
        return True

    def copy_row( self, row ):
        """Copy the entity associated with this row to the end of the collection
        :param row: the row number
        """
        assert object_thread( self )
        
        def create_copy_function( row ):

            def copy_function():
                o = self._get_object(row)
                new_object = self.admin.copy( o )
                self.append_object(new_object)

            return copy_function

        post( create_copy_function( row ) )
        return True

    @model_function
    def append_object( self, obj ):
        """Append an object to this collection, set the possible defaults and flush
        the object if possible/needed
        
        :param obj: the object to be added to the collection
        :return: the new number of rows in the collection
        """
        rows = self._rows
        row = max( rows - 1, 0 )
        self.beginInsertRows( QtCore.QModelIndex(), row, row )
        self.append( obj )
        # defaults might depend on object being part of a collection
        self.admin.set_defaults( obj )
        self.unflushed_rows.add( row )
        if self.flush_changes and not len( self.validator.objectValidity( obj ) ):
            self.admin.flush( obj )
            try:
                self.unflushed_rows.remove( row )
            except KeyError:
                pass
        for depending_obj in self.admin.get_depending_objects( obj ):
            self.rsh.sendEntityUpdate( self, depending_obj )
        self._rows = rows + 1
        #
        # update the cache, so the object can be retrieved
        #
        columns = self._columns
        self._add_data( columns, rows, obj )
        self.endInsertRows()
        return self._rows

    @QtCore.pyqtSlot(object)
    def append_row( self, object_getter ):
        """
        :param object_getter: a function that returns the object to be put in the
        appended row.
        """
        assert object_thread( self )

        def create_append_function( getter ):

            def append_function():
                return self.append_object( getter() )

            return append_function

        post( create_append_function( object_getter ), self._refresh_content )

    @model_function
    def getData( self ):
        """Generator for all the data queried by this proxy"""
        for _i, o in enumerate( self.get_collection() ):
            yield strip_data_from_object( o, self._columns )

    def get_admin( self ):
        """Get the admin object associated with this model"""
        return self.admin
