#  ============================================================================
#
#  Copyright (C) 2007-2013 Conceptive Engineering bvba. All rights reserved.
#  www.conceptive.be / info@conceptive.be
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
#  visit www.python-camelot.com or contact info@conceptive.be
#
#  This file is provided AS IS with NO WARRANTY OF ANY KIND, INCLUDING THE
#  WARRANTY OF DESIGN, MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE.
#
#  For use of this library in commercial applications, please contact
#  info@conceptive.be
#
#  ============================================================================

"""Proxy representing a collection of entities that live in the model thread.

The proxy represents them in the gui thread and provides access to the data
with zero delay.  If the data is not yet present in the proxy, dummy data is
returned and an update signal is emitted when the correct data is available.
"""

#
# Things to take into account for next version
#
# * subsequent calls that require a refresh of the query, should happen when a
#   lock is hold, to prevent multiple queries or count queries
#
# * try to work around the initial count query
#
# * the proxy should allow adding mapped fields to the objects in the collection
#   during the lifetime of the proxy, so a single proxy can be reused for multiple
#   views.
#
import collections
import datetime
import logging

logger = logging.getLogger( 'camelot.view.proxy.collection_proxy' )

import six

from camelot.admin.action.list_action import ListActionModelContext
from sqlalchemy.ext.hybrid import hybrid_property

from ...container.collection_container import CollectionContainer
from ...core.qt import (Qt, QtCore, QtGui, QtModel, QtWidgets, is_deleted,
                        py_to_variant, variant_to_py)
from camelot.core.exception import log_programming_error
from camelot.view.fifo import Fifo
from camelot.view.remote_signals import get_signal_handler
from camelot.view.model_thread import object_thread, post

from camelot.core.files.storage import StoredImage


class ProxyDict(dict):
    """Subclass of dictionary to fool the Qt Variant object and prevent
    it from converting dictionary keys to whatever Qt object, but keep
    everything python"""
    pass

def strip_data_from_object( obj, columns ):
    """For every column in columns, get the corresponding value from the
    object.  Getting a value from an object is time consuming, so using
    this function should be minimized.
    :param obj: the object of which to get data
    :param columns: a list of columns for which to get data
    """
    row_data = []

    for _i, col in enumerate( columns ):
        field_value = None
        try:
            field_value = getattr( obj, col[0] )
        except (Exception, RuntimeError, TypeError, NameError) as e:
            message = "could not get field '%s' of object of type %s"%(col[0], obj.__class__.__name__)
            log_programming_error( logger, 
                                   message,
                                   exc_info = e )
        finally:
            row_data.append( field_value )
    return row_data

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
                unicode_data = u'.'.join( [six.text_type( e ) for e in field_data] )
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
                unicode_data = six.text_type( field_data )
        except (Exception, RuntimeError, TypeError, NameError) as e:
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

class RowModelContext(ListActionModelContext):
    """A list action model context for a single row.  This context is used
    to get the state of the list action on a row
    """
    
    def __init__( self ):
        super( RowModelContext, self ).__init__()
        self.model = None
        self.admin = None
        self.current_row = None
        self.selection_count = 0
        self.collection_count = 0
        self.selected_rows = []
        self.field_attributes = dict()
        self.obj = None
        
    def get_selection( self, yield_per = None ):
        return []
    
    def get_collection( self, yield_per = None ):
        return []
            
    def get_object( self ):
        return self.obj

# QIdentityProxyModel should be used instead of QSortFilterProxyModel, but
# QIdentityProxyModel is missing from PySide
class CollectionProxy(QtModel.QSortFilterProxyModel):
    """The :class:`CollectionProxy` contains a limited copy of the data in the
    actual collection, usable for fast visualisation in a 
    :class:`QtWidgets.QTableView`  

    The behavior of the :class:`QtWidgets.QTableView`, such as what happens when the
    user clicks on a row is defined in the :class:`ObjectAdmin` class.

    """

    row_changed_signal = QtCore.qt_signal(int, int, int)
    exception_signal = QtCore.qt_signal(object)
    rows_removed_signal = QtCore.qt_signal()
    
    # it looks as QtCore.QModelIndex cannot be serialized for cross
    # thread signals
    _rows_about_to_be_inserted_signal = QtCore.qt_signal( int, int )
    _rows_inserted_signal = QtCore.qt_signal( int, int )

    def __init__( self,
                  admin,
                  max_number_of_rows = 10, 
                  flush_changes = True,
                  cache_collection_proxy = None,
                  ):
        """
:param admin: the admin interface for the items in the collection

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
        self.setSourceModel(self.source_model)
        
        self.logger = logging.getLogger(logger.name + '.%s'%id(self))
        self.logger.debug('initialize query table for %s' % (admin.get_verbose_name()))
        # the mutex is recursive to avoid blocking during unittest, when
        # model and view are used in the same thread
        self._mutex = QtCore.QMutex(QtCore.QMutex.Recursive)
        self.admin = admin
        self.list_action = admin.list_action
        self.row_model_context = RowModelContext()
        self.row_model_context.admin = admin
        self.settings = self.admin.get_settings()
        self._horizontal_header_height = QtGui.QFontMetrics( self._header_font_required ).height() + 10
        self._header_font_metrics = QtGui.QFontMetrics( self._header_font )
        vertical_header_font_height = QtGui.QFontMetrics( self._header_font ).height()
        self._vertical_header_height = vertical_header_font_height * self.admin.lines_per_row + 10
        self.vertical_header_size =  QtCore.QSize( 16 + 10,
                                                   self._vertical_header_height )
        self.validator = admin.get_validator(self)
        self._collection = []
        self.flush_changes = flush_changes
        self.mt = get_model_thread()
        # Set database connection and load data
        self._rows = None
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
            self.action_state_cache = cache_collection_proxy.action_state_cache.shallow_copy( max_cache )
        else:        
            self.display_cache = Fifo( max_cache )
            self.edit_cache = Fifo( max_cache )
            self.attributes_cache = Fifo( max_cache )
            self.action_state_cache = Fifo( max_cache )
        # The rows in the table for which a cache refill is under request
        self.rows_under_request = set()
        self._update_requests = list()
        self._rowcount_requests = list()
        # The rows that have unflushed changes
        self.unflushed_rows = set()
        self._sort_and_filter = SortingRowMapper()
        self.row_changed_signal.connect( self._emit_changes )
        self._rows_about_to_be_inserted_signal.connect( self._rows_about_to_be_inserted, Qt.QueuedConnection )
        self._rows_inserted_signal.connect( self._rows_inserted, Qt.QueuedConnection )
        self.rsh = get_signal_handler()
        self.rsh.connect_signals( self )
#    # the initial collection might contain unflushed rows
        post( self._update_unflushed_rows )
#    # in that way the number of rows is requested as well
        if cache_collection_proxy:
            self.setRowCount( cache_collection_proxy.rowCount() )
        self.logger.debug( 'initialization finished' )

    
    @hybrid_property
    def _header_font( cls ):
        return QtWidgets.QApplication.font()
    
    @hybrid_property
    def _header_font_required( cls ):
        font = QtWidgets.QApplication.font()
        font.setBold( True )
        return font

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
        if self._rows is None:
            self.refresh()
            return 0
        return self._rows
    
    def hasChildren( self, parent ):
        assert object_thread( self )
        return False
    
    def buddy(self, index):
        return index

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

    def getRowCount( self ):
        # make sure we don't count an object twice if it is twice
        # in the list, since this will drive the cache nuts
        locker = QtCore.QMutexLocker(self._mutex)
        self._rowcount_requests.pop()
        if len(self._rowcount_requests) == 0:
            # this is the last request on its way, do the counting now
            rows = len( set( self.get_collection() ) )
        else:
            # other row count reqests are on their way, do nothing now
            rows = None
        locker.unlock()
        return rows

    def refresh( self ):
        assert object_thread( self )
        locker = QtCore.QMutexLocker(self._mutex)
        self._rowcount_requests.append(True)
        post( self.getRowCount, self._refresh_content )
        locker.unlock()

    @QtCore.qt_slot(int)
    def _refresh_content(self, rows ):
        assert object_thread( self )
        locker = QtCore.QMutexLocker(self._mutex)
        self.display_cache = Fifo( 10 * self.max_number_of_rows )
        self.edit_cache = Fifo( 10 * self.max_number_of_rows )
        self.attributes_cache = Fifo( 10 * self.max_number_of_rows )
        self.action_state_cache = Fifo( 10 * self.max_number_of_rows )
        self.rows_under_request = set()
        self.unflushed_rows = set()
        # once the cache has been cleared, no updates ought to be accepted
        self._update_requests = list()
        locker.unlock()
        self.setRowCount( rows )

    def set_value(self, collection):
        """
        :param collection: the list of objects to display
        """
        if collection is None:
            collection = []
        elif isinstance(collection, CollectionContainer):
            collection = collection._collection
        self._collection = collection
        self.refresh()
    
    def get_value(self):
        return self._collection

    def get_collection( self ):
        return self._collection

    def handleRowUpdate( self, row ):
        """Handles the update of a row when this row might be out of date"""
        assert object_thread( self )
        self.display_cache.delete_by_row( row )
        self.edit_cache.delete_by_row( row )
        self.attributes_cache.delete_by_row( row )
        self.action_state_cache.delete_by_row( row )
        self.dataChanged.emit( self.index( row, 0 ),
                               self.index( row, self.columnCount() - 1 ) )

    @QtCore.qt_slot( object, object )
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

                return entity_update

            post( create_entity_update(row, entity) )
        else:
            self.logger.debug( 'duplicate update' )

    @QtCore.qt_slot( object, object )
    def handle_entity_delete( self, sender, obj ):
        """Handles the entity signal, indicating that the model is out of
        date"""
        assert object_thread( self )
        self.logger.debug( 'received entity delete signal' )
        if sender != self:
            try:
                self.display_cache.get_row_by_entity( obj )
            except KeyError:
                self.logger.debug( 'entity not in cache' )
                return

            def entity_remove( obj ):
                self.remove( obj )
                self.display_cache.delete_by_entity( obj )
                self.attributes_cache.delete_by_entity( obj )
                self.edit_cache.delete_by_entity( obj )
                self.action_state_cache.delete_by_entity( obj )
                return self._rows

            post( entity_remove, self._refresh_content, args=(obj,) )

    @QtCore.qt_slot( object, object )
    def handle_entity_create( self, sender, entity ):
        """Handles the entity signal, indicating that the model is out of
        date"""
        assert object_thread( self )
        self.logger.debug( 'received entity create signal' )
        # @todo : decide what to do when a new entity has been created,
        #         probably do nothing
        return

    @QtCore.qt_slot(object)
    def setRowCount( self, rows ):
        """Callback method to set the number of rows
        @param rows the new number of rows
        """
        assert object_thread( self )
        if rows == None:
            # other row counts are on their way, ignore this one
            return
        self._rows = rows
        self.layoutChanged.emit()

    def get_static_field_attributes(self):
        return list(self.admin.get_static_field_attributes([c[0] for c in self._columns]))
    
    @QtCore.qt_slot(object)
    def set_static_field_attributes(self, static_fa):
        self._static_field_attributes = static_fa
        self.beginResetModel()
        self.settings.beginGroup( 'column_width' )
        self.settings.beginGroup( '0' )
        #
        # this loop can take a while to complete
        #
        font_metrics = QtGui.QFontMetrics(self._header_font_required)
        char_width = font_metrics.averageCharWidth()
        source_model = self.sourceModel()
        for i, (field_name, fa) in enumerate( self._columns ):
            verbose_name = six.text_type(fa['name'])
            header_item = QtGui.QStandardItem()
            set_header_data = header_item.setData
            #
            # Set the header data
            #
            set_header_data(py_to_variant( verbose_name ), Qt.DisplayRole)
            if fa.get( 'nullable', True ) == False:
                set_header_data(self._header_font_required, Qt.FontRole)
            else:
                set_header_data(self._header_font, Qt.FontRole)

            settings_width = int( variant_to_py( self.settings.value( field_name, 0 ) ) )
            if settings_width > 0:
                width = settings_width
            else:
                width = fa['column_width'] * char_width
            header_item.setData( py_to_variant( QtCore.QSize( width, self._horizontal_header_height ) ),
                                 Qt.SizeHintRole )
            source_model.setHorizontalHeaderItem( i, header_item )
        
        self.settings.endGroup()
        self.settings.endGroup()
        self.endResetModel()

    def set_columns(self, columns):
        """Callback method to set the columns

        :param columns: a list with fields to be displayed of the form [('field_name', field_attributes), ...] as
        returned by the `get_columns` method of the `EntityAdmin` class
        """
        assert object_thread( self )
        self.logger.debug( 'set_columns' )
        self._columns = columns
        post(self.get_static_field_attributes, self.set_static_field_attributes)

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
                #
                # sizehint role is requested, for every row, so we have to
                # return a fixed value
                #
                return py_to_variant(self.vertical_header_size)
            #
            # get icon from action state
            #
            action_state = self._get_row_data( section, self.action_state_cache )[0]
            if action_state not in (None, ValueLoading):
                icon = action_state.icon
                if icon is not None:
                    if role == Qt.DecorationRole:
                        return icon.getQPixmap()
                verbose_name = action_state.verbose_name
                if verbose_name is not None:
                    if role == Qt.DisplayRole:
                        return py_to_variant(six.text_type(verbose_name))
                tooltip = action_state.tooltip
                if tooltip is not None:
                    if role == Qt.ToolTipRole:
                        return py_to_variant(six.text_type(tooltip))
        return self.sourceModel().headerData(section, orientation, role)

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
                    except Exception as e:
                        logger.error( 'could not get attribute %s from object'%field_name, exc_info = e )
                    try:
                        key_2 = getattr( line_2[1], field_name )
                    except Exception as e:
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
           not ( 0 <= index.row() < self.rowCount( index ) ) or \
           not ( 0 <= index.column() < self.columnCount() ):
            if role == Qt.UserRole:
                return py_to_variant({})
            else:
                return py_to_variant()
        if role in (Qt.EditRole, Qt.DisplayRole):
            if role == Qt.EditRole:
                cache = self.edit_cache
            else:
                cache = self.display_cache
            data = self._get_row_data( index.row(), cache )
            value = data[index.column()]
            if isinstance(value, datetime.datetime):
                # Putting a python datetime into a Qt Variant and returning
                # it to a PyObject seems to be buggy, therefore we chop the
                # microseconds
                if value:
                    value = QtCore.QDateTime(value.year, value.month,
                                             value.day, value.hour,
                                             value.minute, value.second)
            elif isinstance(value, (list, dict)):
                value = CollectionContainer(value)
            return py_to_variant( value )
        elif role == Qt.ToolTipRole:
            return py_to_variant(self._get_field_attribute_value(index, 'tooltip'))
        elif role == Qt.BackgroundRole:
            return py_to_variant(self._get_field_attribute_value(index, 'background_color') or py_to_variant())
        elif role == Qt.UserRole:
            field_attributes = ProxyDict(self._static_field_attributes[index.column()])
            dynamic_field_attributes = self._get_row_data( index.row(), self.attributes_cache )[index.column()]
            if dynamic_field_attributes != ValueLoading:
                field_attributes.update( dynamic_field_attributes )
            return py_to_variant(field_attributes)
        elif role == Qt.UserRole + 1:
            try:
                return py_to_variant( self.edit_cache.get_entity_at_row( index.row() ) )
            except KeyError:
                return py_to_variant( ValueLoading )
        return py_to_variant()

    def _get_field_attribute_value(self, index, field_attribute):
        """Get the values for the static and the dynamic field attributes at once
        :return: the value of the field attribute"""
        try:
            return self._static_field_attributes[index.column()][field_attribute]
        except KeyError:
            value = self._get_row_data( index.row(), self.attributes_cache )[index.column()]
            if value is ValueLoading:
                return None
            return value.get(field_attribute, None)

    def _handle_update_requests(self):
        #
        # wait for a while until the update requests array doesn't change any
        # more
        #
        previous_length = 0
        locker = QtCore.QMutexLocker(self._mutex)
        while previous_length != len(self._update_requests):
            previous_length = len(self._update_requests)
            locker.unlock()
            QtCore.QThread.msleep(5)
            locker.relock()
        #
        # Copy the update requests and clear the list of requests
        #
        update_requests = [u for u in self._update_requests]
        self._update_requests = []
        locker.unlock()
        #
        # Handle the requests
        #
        return_list = []
        grouped_requests = collections.defaultdict( list )
        for flushed, row, column, value in update_requests:
            grouped_requests[row].append( (flushed, column, value) )
        admin = self.admin
        for row, request_group in six.iteritems(grouped_requests):
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
                continue
            #
            # the object might have been deleted while an editor was open
            # 
            if admin.is_deleted( o ):
                continue
            changed = False
            for flushed, column, value in request_group:
                attribute, field_attributes = self._columns[column]

                from sqlalchemy.exc import DatabaseError
                new_value = value()
                self.logger.debug( 'set data for row %s;col %s' % ( row, column ) )
    
                if new_value == ValueLoading:
                    continue

                old_value = getattr( o, attribute )
                value_changed = ( new_value != old_value )
                #
                # In case the attribute is a OneToMany or ManyToMany, we cannot simply compare the
                # old and new value to know if the object was changed, so we'll
                # consider it changed anyway
                #
                direction = field_attributes.get( 'direction', None )
                if direction in ( 'manytomany', 'onetomany' ):
                    value_changed = True
                if value_changed is not True:
                    continue
                #
                # now check if this column is editable, since editable might be
                # dynamic and change after every change of the object
                #
                fields = [attribute]
                for fa in admin.get_dynamic_field_attributes(o, fields):
                    # if editable is not in the field_attributes dict, it wasn't
                    # dynamic but static, so earlier checks should have 
                    # intercepted this change
                    if fa.get('editable', True) == True:
                        # interrupt inner loop, so outer loop can be continued
                        break
                else:
                    continue
                # update the model
                try:
                    admin.set_field_value(o, attribute, new_value)
                    #
                    # setting this attribute, might trigger a default function 
                    # to return a value, that was not returned before
                    #
                    admin.set_defaults( o, include_nullable_fields=False )
                except AttributeError as e:
                    self.logger.error( u"Can't set attribute %s to %s" % ( attribute, six.text_type( new_value ) ), exc_info = e )
                except TypeError:
                    # type error can be raised in case we try to set to a collection
                    pass
                changed = value_changed or changed
            if changed:
                if self.flush_changes:
                    if self.validator.isValid( row ):
                        # save the state before the update
                        was_persistent =admin.is_persistent(o)
                        try:
                            admin.flush( o )
                        except DatabaseError as e:
                            #@todo: when flushing fails, the object should not be removed from the unflushed rows ??
                            self.logger.error( 'Programming Error, could not flush object', exc_info = e )
                        locker.relock()
                        try:
                            self.unflushed_rows.remove( row )
                        except KeyError:
                            pass
                        locker.unlock()
                        if was_persistent is False:
                            self.rsh.sendEntityCreate(self, o)
                # update the cache
                self._add_data(self._columns, row, o)
                #@todo: update should only be sent remotely when flush was done
                self.rsh.sendEntityUpdate( self, o )
                for depending_obj in admin.get_depending_objects( o ):
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

    # @todo : it seems Qt regulary crashes when dataChanged is emitted
    #         don't do the emit inside a slot, but rework the CollectionProxy
    #         to behave as an action that yields all it's updates
    @QtCore.qt_slot(int, int, int)
    def _emit_changes( self, row, from_column, thru_column ):
        assert object_thread( self )
        # emit the headerDataChanged signal, to ensure the row icon is
        # updated
        self.headerDataChanged.emit(Qt.Vertical, row, row)
        if thru_column >= from_column:
            top_left = self.index(row, from_column)
            bottom_right = self.index(row, thru_column)
            self.dataChanged.emit(top_left, bottom_right)

    def flags( self, index ):
        """Returns the item flags for the given index"""
        assert object_thread( self )
        if not index.isValid() or \
           not ( 0 <= index.row() <= self.rowCount( index ) ) or \
           not ( 0 <= index.column() <= self.columnCount() ):
            return Qt.NoItemFlags
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
        action_state = None
        if not self.admin.is_deleted( obj ):
            row_data = strip_data_from_object( obj, columns )
            dynamic_field_attributes = list(self.admin.get_dynamic_field_attributes( obj, (c[0] for c in columns)))
            static_field_attributes = self.admin.get_static_field_attributes( (c[0] for c in columns) )
            unicode_row_data = stripped_data_to_unicode( row_data, obj, static_field_attributes, dynamic_field_attributes )
            if self.list_action:
                self.row_model_context.obj = obj
                self.row_model_context.current_row = row
                action_state = self.list_action.get_state(self.row_model_context)
        else:
            row_data = [None] * len(columns)
            dynamic_field_attributes =  [{'editable':False}] * len(columns)
            static_field_attributes = self.admin.get_static_field_attributes( (c[0] for c in columns) )
            unicode_row_data = [u''] * len(columns)
        # keep track of the columns that changed, to limit the
        # number of editors/cells that need to be updated
        changed_columns = set()
        locker = QtCore.QMutexLocker( self._mutex )
        changed_columns.update( self.edit_cache.add_data( row, obj, row_data ) )
        changed_columns.update( self.display_cache.add_data( row, obj, unicode_row_data ) )
        changed_columns.update( self.attributes_cache.add_data(row, obj, dynamic_field_attributes ) )
        self.action_state_cache.add_data(row, obj, [action_state] )
        locker.unlock()
        #
        # it might be that the CollectionProxy is deleted on the Qt side of
        # the application
        #
        if not is_deleted( self ) and row != None:
            if len( changed_columns ) == len( columns ):
                # this is new data or everything has changed, dont waste any
                # time to fine grained updates
                self.row_changed_signal.emit( row, 0, len( columns ) - 1 )
            elif len( changed_columns ):
                changed_columns = sorted( changed_columns )
                next_changed_columns = changed_columns[1:] + [None]
                from_column = changed_columns[0]
                for changed_column, next_column in zip( changed_columns,
                                                        next_changed_columns ):
                    if next_column != changed_column + 1:
                        self.row_changed_signal.emit( row, 
                                                      from_column, 
                                                      changed_column )
                        from_column = next_column
            else:
                # only the header changed
                self.row_changed_signal.emit( row, 1, 0 )

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
            QtCore.QThread.msleep(5)
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
        rows_to_get = list(rows_to_get)
        locker.unlock()        
        #
        # see if there is anything left to do
        #
        try:
            if len(rows_to_get):
                rows_to_get.sort()
                offset = rows_to_get[0]
                #
                # find first discontinuity
                #
                for i in range(offset, rows_to_get[-1]+1):
                    if rows_to_get[i-offset] != i:
                        break
                limit = i - offset + 1
        except IndexError as e:
            logger.error('index error with rows_to_get %s'%six.text_type(rows_to_get), exc_info=e)
            raise e
        return (offset, limit)

    def _extend_cache( self ):
        """Extend the cache around the rows under request"""
        offset, limit = self._offset_and_limit_rows_to_get()
        if limit:
            columns = self._columns
            collection = self.get_collection()
            skipped_rows = 0
            try:
                for i in range(offset, min( offset + limit + 1,
                                            len( collection ) ) ):
                    object_found = False
                    while not object_found:
                        unsorted_row = self._sort_and_filter[i]
                        obj = collection[unsorted_row+skipped_rows]
                        if self._skip_row(i, obj):
                            skipped_rows = skipped_rows + 1
                        else:
                            self._add_data(columns, i, obj)
                            object_found = True
            except IndexError:
                # stop when the end of the collection is reached, no matter
                # what the request was
                pass
        return ( offset, limit )

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

    @QtCore.qt_slot(tuple)
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
        assert row >= 0
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
            locker = QtCore.QMutexLocker(self._mutex)
            if row not in self.rows_under_request:    
                self.rows_under_request.add( row )
                #
                # unlock before posting to model thread, since in the
                # single threaded mode, the model thread function needs to
                # acquire the lock
                #
                locker.unlock()
                post( self._extend_cache, self._cache_extended )
            return empty_row_data

    def remove( self, o ):
        collection = self.get_collection()
        if o in collection:
            collection.remove( o )
            self._rows -= 1

    def append( self, o ):
        collection = self.get_collection()
        if o not in collection:
            collection.append( o )

    @QtCore.qt_slot( int, int )
    def _rows_about_to_be_inserted( self, first, last ):
        self.beginInsertRows( QtCore.QModelIndex(), first, last )
        
    @QtCore.qt_slot( int, int )
    def _rows_inserted( self, _first, _last ):
        self.endInsertRows()
        
    def append_object(self, obj):
        """Append an object to this collection
        
        :param obj: the object to be added to the collection
        :return: the new number of rows in the collection
        
        """
        rows = self._rows
        row = max( rows - 1, 0 )
        self._rows_about_to_be_inserted_signal.emit( row, row )
        self.append( obj )
        # defaults might depend on object being part of a collection
        if not self.admin.is_persistent(obj):
            self.unflushed_rows.add( row )
        for depending_obj in self.admin.get_depending_objects( obj ):
            self.rsh.sendEntityUpdate( self, depending_obj )
        self._rows = rows + 1
        #
        # update the cache, so the object can be retrieved
        #
        columns = self._columns
        self._add_data( columns, rows, obj )
        self._rows_inserted_signal.emit( row, row )
        return self._rows

    def get_admin( self ):
        """Get the admin object associated with this model"""
        return self.admin

