#  ============================================================================
#
#  Copyright (C) 2007-2011 Conceptive Engineering bvba. All rights reserved.
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

from camelot.core.utils import is_deleted
from camelot.core.files.storage import StoredFile
from camelot.view.art import Icon
from camelot.view.fifo import Fifo
from camelot.view.controls import delegates
from camelot.view.controls.exception import register_exception
from camelot.view.remote_signals import get_signal_handler
from camelot.view.model_thread import gui_function, \
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

    @gui_function
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
            logger.error('ProgrammingError : could not get field %s of object of type %s'%(col[0], obj.__class__.__name__),
                         exc_info=e)
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

class CollectionProxy( QtCore.QAbstractTableModel ):
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

    @gui_function
    def __init__( self, 
                  admin, 
                  collection_getter, 
                  columns_getter,
                  max_number_of_rows = 10, 
                  edits = None, 
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
        from camelot.view.model_thread import get_model_thread
        self.logger = logging.getLogger(logger.name + '.%s'%id(self))
        self.logger.debug('initialize query table for %s' % (admin.get_verbose_name()))
        self._mutex = QtCore.QMutex()
        self.admin = admin
        self._horizontal_header_height = QtGui.QFontMetrics( self._header_font_required ).height() + 10
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
        self.column_count = 0
        self.flush_changes = flush_changes
        self.delegate_manager = None
        self.mt = get_model_thread()
        # Set database connection and load data
        self._rows = 0
        self._columns = []
        self._static_field_attributes = []
        self._max_number_of_rows = max_number_of_rows
        if cache_collection_proxy:
            self.display_cache = cache_collection_proxy.display_cache.shallow_copy( 10 * self.max_number_of_rows )
            self.edit_cache = cache_collection_proxy.edit_cache.shallow_copy( 10 * self.max_number_of_rows )
            self.attributes_cache = cache_collection_proxy.attributes_cache.shallow_copy( 10 * self.max_number_of_rows )
        else:        
            self.display_cache = Fifo( 10 * self.max_number_of_rows )
            self.edit_cache = Fifo( 10 * self.max_number_of_rows )
            self.attributes_cache = Fifo( 10 * self.max_number_of_rows )
        # The rows in the table for which a cache refill is under request
        self.rows_under_request = set()
        self._update_requests = list()
        # The rows that have unflushed changes
        self.unflushed_rows = set()
        self._sort_and_filter = SortingRowMapper()
        # Set edits
        self.edits = edits or []
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

    @gui_function
    def revertRow( self, row ):
        def create_refresh_entity( row ):

            @model_function
            def refresh_entity():
                o = self._get_object( row )
                self.admin.refresh( o )
                return row, o

            return refresh_entity

        post( create_refresh_entity( row ), self._revert_row )

    @QtCore.pyqtSlot(tuple)
    @gui_function
    def _revert_row(self, row_and_entity ):
        row, entity = row_and_entity
        self.handleRowUpdate( row )
        self.rsh.sendEntityUpdate( self, entity )

    @gui_function
    def refresh( self ):
        post( self.getRowCount, self._refresh_content )

    @QtCore.pyqtSlot(int)
    @gui_function
    def _refresh_content(self, rows ):
        self.display_cache = Fifo( 10 * self.max_number_of_rows )
        self.edit_cache = Fifo( 10 * self.max_number_of_rows )
        self.attributes_cache = Fifo( 10 * self.max_number_of_rows )
        locker = QtCore.QMutexLocker(self._mutex)
        self.rows_under_request = set()
        self.unflushed_rows = set()
        locker.unlock()
        self.setRowCount( rows )

    def set_collection_getter( self, collection_getter ):
        self.logger.debug('set collection getter')
        self._collection_getter = collection_getter
        self.refresh()

    @model_function
    def get_collection( self ):
        return self._collection_getter()

    @gui_function
    def handleRowUpdate( self, row ):
        """Handles the update of a row when this row might be out of date"""
        self.display_cache.delete_by_row( row )
        self.edit_cache.delete_by_row( row )
        self.attributes_cache.delete_by_row( row )
        self.dataChanged.emit( self.index( row, 0 ),
                               self.index( row, self.column_count ) )

    @QtCore.pyqtSlot( object, object )
    def handle_entity_update( self, sender, entity ):
        """Handles the entity signal, indicating that the model is out of
        date"""
        self.logger.debug( '%s %s received entity update signal' % \
                     ( self.__class__.__name__, self.admin.get_verbose_name() ) )
        if sender != self:
            try:
                row = self.display_cache.get_row_by_entity(entity)
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
                    columns = self.getColumns()
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
        self.logger.debug( 'received entity delete signal' )
        #
        # simply removing the entity from the collection might have
        # undesirable effects.  eg when a form is pointing to this entity, 
        # so instead update the entity
        #
        self.handle_entity_update( sender, entity )

    @QtCore.pyqtSlot( object, object )
    def handle_entity_create( self, sender, entity ):
        """Handles the entity signal, indicating that the model is out of
        date"""
        self.logger.debug( 'received entity create signal' )
        # @todo : decide what to do when a new entity has been created,
        #         probably do nothing
        return

    @QtCore.pyqtSlot(int)
    def setRowCount( self, rows ):
        """Callback method to set the number of rows
        @param rows the new number of rows
        """
        self._rows = rows
        self.layoutChanged.emit()

    def getItemDelegate( self ):
        """:return: a DelegateManager for this model, or None if no DelegateManager yet available
        a DelegateManager will be available once the item_delegate_changed signal has been emitted"""
        self.logger.debug( 'getItemDelegate' )
        return self.delegate_manager

    def getColumns( self ):
        """:return: the columns as set by the setColumns method"""
        return self._columns

    @QtCore.pyqtSlot(object)
    @gui_function
    def setColumns( self, columns ):
        """Callback method to set the columns

        :param columns: a list with fields to be displayed of the form [('field_name', field_attributes), ...] as
        returned by the getColumns method of the ElixirAdmin class
        """
        self.logger.debug( 'setColumns' )
        self.column_count = len( columns )
        self._columns = columns

        delegate_manager = delegates.DelegateManager()
        delegate_manager.set_columns_desc( columns )

        # set a delegate for the vertical header
        delegate_manager.insertColumnDelegate( -1, delegates.PlainTextDelegate(parent = delegate_manager) )

        #
        # this loop can take a while to complete, so processEvents is called regulary
        #
        for i, c in enumerate( columns ):
#            if i%10==0:
#                QtCore.QCoreApplication.processEvents(QtCore.QEventLoop.ExcludeSocketNotifiers, 100)
            field_name = c[0]
            self.logger.debug( 'creating delegate for %s' % field_name )
            if 'delegate' in c[1]:
                try:
                    delegate = c[1]['delegate']( parent = delegate_manager, **c[1] )
                except Exception, e:
                    logger.error('ProgrammingError : could not create delegate for field %s'%field_name, exc_info=e)
                    delegate = delegates.PlainTextDelegate( parent = delegate_manager, **c[1] )
                delegate_manager.insertColumnDelegate( i, delegate )
                continue
            elif c[1]['python_type'] == str:
                if c[1]['length']:
                    delegate = delegates.PlainTextDelegate( parent = delegate_manager, maxlength = c[1]['length'] )
                    delegate_manager.insertColumnDelegate( i, delegate )
                else:
                    delegate = delegates.TextEditDelegate( parent = delegate_manager, **c[1] )
                    delegate_manager.insertColumnDelegate( i, delegate )
            else:
                delegate = delegates.PlainTextDelegate(parent = delegate_manager)
                delegate_manager.insertColumnDelegate( i, delegate )

        # Only set the delegate manager when it is fully set up
        self.delegate_manager = delegate_manager
        self.item_delegate_changed_signal.emit()
        self.layoutChanged.emit()

    def rowCount( self, index = None ):
        return self._rows

    def columnCount( self, index = None ):
        return self.column_count

    @gui_function
    def headerData( self, section, orientation, role ):
        """In case the columns have not been set yet, don't even try to get
        information out of them
        """
        if orientation == Qt.Horizontal:
            if section >= self.column_count:
                return QtCore.QAbstractTableModel.headerData( self, section, orientation, role )
            c = self.getColumns()[section]

            if role == Qt.DisplayRole:
                return QtCore.QVariant( unicode(c[1]['name']) )

            elif role == Qt.FontRole:
                if ( 'nullable' in c[1] ) and \
                   ( c[1]['nullable'] == False ):
                    return QtCore.QVariant( self._header_font_required )
                else:
                    return QtCore.QVariant( self._header_font )

            elif role == Qt.SizeHintRole:
                option = QtGui.QStyleOptionViewItem()
                if self.delegate_manager:
                    editor_size = self.delegate_manager.sizeHint( option, self.index( 0, section ) )
                else:
                    editor_size = QtCore.QSize(0, 0)
                if 'minimal_column_width' in c[1]:
                    minimal_column_width = QtGui.QFontMetrics( self._header_font ).size( Qt.TextSingleLine, 'A' ).width()*c[1]['minimal_column_width']
                else:
                    minimal_column_width = 100
                editable = True
                if 'editable' in c[1]:
                    editable = c[1]['editable']
                label_size = QtGui.QFontMetrics( self._header_font_required ).size( Qt.TextSingleLine, unicode(c[1]['name']) + ' ' )
                size = max( minimal_column_width, label_size.width() + 10 )
                if editable:
                    size = max( size, editor_size.width() )
                return QtCore.QVariant( QtCore.QSize( size, self._horizontal_header_height ) )
        else:
            if role == Qt.SizeHintRole:
                if self.header_icon:
                    return QtCore.QVariant( QtCore.QSize( self.iconSize.width() + 10,
                                                          self._vertical_header_height ) )
                else:
                    # if there is no icon, the line numbers will be displayed, so create some space for those
                    return QtCore.QVariant( QtCore.QSize( QtGui.QFontMetrics( self._header_font ).size( Qt.TextSingleLine, str(self._rows) ).width() + 10, self._vertical_header_height ) )
            if role == Qt.DecorationRole:
                return self.form_icon
#      elif role == Qt.DisplayRole:
#        return QtCore.QVariant()
        return QtCore.QAbstractTableModel.headerData( self, section, orientation, role )

    @gui_function
    def sort( self, column, order ):
        """reimplementation of the QAbstractItemModel its sort function"""

        def create_sort(column, order):

            def sort():
                unsorted_collection = [(i,o) for i,o in enumerate(self.get_collection())]
                key = lambda item:getattr(item[1], self._columns[column][0])
                unsorted_collection.sort(key=key, reverse=order)
                for j,(i,_o) in enumerate(unsorted_collection):
                    self._sort_and_filter[j] = i
                return len(unsorted_collection)

            return sort

        post(create_sort(column, order), self._refresh_content)

    @gui_function
    def data( self, index, role ):
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
        if not index.isValid() or \
           not ( 0 <= index.row() <= self.rowCount( index ) ) or \
           not ( 0 <= index.column() <= self.columnCount( index ) ):
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
            return QtCore.QVariant(self._get_field_attribute_value(index, 'background_color') or QtGui.QColor('White'))
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
            attribute, field_attributes = self.getColumns()[column]

            from sqlalchemy.exc import DatabaseError
            from sqlalchemy import orm
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
            if direction in ( orm.interfaces.MANYTOMANY, orm.interfaces.ONETOMANY ):
                changed = True
            if changed:
                # update the model
                model_updated = False
                try:
                    setattr( o, attribute, new_value )
                    #
                    # setting this attribute, might trigger a default function to return a value,
                    # that was not returned before
                    #
                    self.admin.set_defaults( o, include_nullable_fields=False )
                    model_updated = True
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
                    #
                    # we can only track history if the model was updated, and it was
                    # flushed before, otherwise it has no primary key yet
                    #
                    if model_updated and hasattr(o, 'id') and o.id:
                        #
                        # in case of files or relations, we cannot pickle them
                        #
                        if isinstance( old_value, StoredFile ):
                            old_value = old_value.name
                        if not direction:
                            from camelot.model.memento import BeforeUpdate
                            # only register the update when the camelot model is active
                            if hasattr(BeforeUpdate, 'query'):
                                from camelot.model.authentication import getCurrentAuthentication
                                history = BeforeUpdate( model = unicode( self.admin.entity.__name__ ),
                                                       primary_key = o.id,
                                                       previous_attributes = {attribute:old_value},
                                                       authentication = getCurrentAuthentication() )

                                try:
                                    history.flush()
                                except DatabaseError, e:
                                    self.logger.error( 'Programming Error, could not flush history', exc_info = e )
                # update the cache
                self._add_data(self.getColumns(), row, o)
                #@todo: update should only be sent remotely when flush was done
                self.rsh.sendEntityUpdate( self, o )
                for depending_obj in self.admin.get_depending_objects( o ):
                    self.rsh.sendEntityUpdate( self, depending_obj )
                return_list.append(( ( row, 0 ), ( row, len( self.getColumns() ) ) ))
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
        #
        # prevent data of being set in rows not actually in this model
        #
        if not index.isValid():
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
    @gui_function
    def _emit_changes( self, row ):
        if row!=None:
            self.dataChanged.emit( self.index( row, 0 ),
                                   self.index( row, self.column_count ) )

    def flags( self, index ):
        """Returns the item flags for the given index"""
        flags = Qt.ItemIsEnabled | Qt.ItemIsSelectable
        if self._get_field_attribute_value(index, 'editable'):
            flags = flags | Qt.ItemIsEditable
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
            columns = self.getColumns()
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

    @gui_function
    def remove_rows( self, rows, delete = True ):
        """Remove the entity associated with this row from this collection
        @param rows: a list with the numbers of the rows to remove
        @param delete: delete the entity as well
        
        The rows_removed signal will be emitted when the removal was 
        successful, otherwise the exception_signal will be emitted.
        """
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

    @gui_function
    def copy_row( self, row ):
        """Copy the entity associated with this row to the end of the collection
        :param row: the row number
        """

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
        rows = self.rowCount()
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
# TODO : it's not because an object is added to this list, that it was created
# it might as well exist already, eg. manytomany relation
#      from camelot.model.memento import Create
#      from camelot.model.authentication import getCurrentAuthentication
#      history = Create(model=unicode(self.admin.entity.__name__),
#                       primary_key=o.id,
#                       authentication = getCurrentAuthentication())
#      elixir.session.flush([history])
#      self.rsh.sendEntityCreate(self, o)
        self._rows = rows + 1
        self.endInsertRows()
        return self._rows

    @QtCore.pyqtSlot(object)
    @gui_function
    def append_row( self, object_getter ):
        """
        :param object_getter: a function that returns the object to be put in the
        appended row.
        """

        def create_append_function( getter ):

            def append_function():
                return self.append_object( getter() )

            return append_function

        post( create_append_function( object_getter ), self._refresh_content )

    @model_function
    def getData( self ):
        """Generator for all the data queried by this proxy"""
        for _i, o in enumerate( self.get_collection() ):
            yield strip_data_from_object( o, self.getColumns() )

    def get_admin( self ):
        """Get the admin object associated with this model"""
        return self.admin

