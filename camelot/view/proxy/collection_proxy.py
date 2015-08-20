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
# * try to work around the initial count query
#
# * the proxy should allow adding mapped fields to the objects in the collection
#   during the lifetime of the proxy
#
import collections
import datetime
import logging
import sys

logger = logging.getLogger( 'camelot.view.proxy.collection_proxy' )

import six

from camelot.admin.action.list_action import ListActionModelContext
from sqlalchemy.ext.hybrid import hybrid_property

from ...container.collection_container import CollectionContainer
from ...core.qt import (Qt, QtCore, QtGui, QtModel, QtWidgets,
                        py_to_variant, variant_to_py)
from ..crud_signals import CrudSignalHandler
from camelot.core.exception import log_programming_error
from camelot.view.fifo import Fifo
from camelot.view.model_thread import object_thread, post
from camelot.core.files.storage import StoredImage

#
# Custom Roles
#
FieldAttributesRole = Qt.UserRole
ObjectRole = Qt.UserRole + 1
PreviewRole = Qt.UserRole + 2

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

invalid_data = py_to_variant()
invalid_field_attributes_data = py_to_variant({})

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

class Update(object):

    def __init__(self, objects):
        self.objects = objects
        self.changed_ranges = []

    def model_run(self, proxy):
        for obj in self.objects:
            try:
                row = proxy.display_cache.get_row_by_entity(obj)
            except KeyError:
                continue
            #
            # Because the entity is updated, it might no longer be in our
            # collection, therefore, make sure we don't access the collection
            # to strip data of the entity
            #
            columns = proxy._columns
            self.changed_ranges.extend(proxy._add_data(columns, row, obj))
        return self

    def gui_run(self, item_model):
        root_item = item_model.source_model.invisibleRootItem()
        for row, header_item, items in self.changed_ranges:
            # emit the headerDataChanged signal, to ensure the row icon is
            # updated
            item_model.source_model.setVerticalHeaderItem(row, header_item)
            item_model.headerDataChanged.emit(Qt.Vertical, row, row)
            for column, item in items:
                root_item.setChild(row, column, item)

class Deleted(object):

    def __init__(self, objects):
        self.objects = objects
        self.rows = None

    def model_run(self, proxy):
        for obj in self.objects:
            try:
                proxy.display_cache.get_row_by_entity( obj )
            except KeyError:
                continue
            proxy.remove( obj )
            proxy.display_cache.delete_by_entity( obj )
            proxy.attributes_cache.delete_by_entity( obj )
            proxy.edit_cache.delete_by_entity( obj )
        self.rows = proxy.get_row_count()
        return self

    def gui_run(self, item_model):
        item_model._refresh_content(self.rows)

class RowCount(object):

    def __init__(self):
        self.rows = None

    def model_run(self, proxy):
        self.rows = proxy.get_row_count()
        return self

    def gui_run(self, item_model):
        if self.rows is not None:
            item_model._refresh_content(self.rows)

    def __repr__(self):
        return '{0.__class__.__name__}(rows={0.rows})'.format(self)

class RowData(Update):

    def __init__(self, rows):
        super(RowData, self).__init__(None)
        self.rows = rows
        self.difference = None
        self.changed_ranges = []

    def offset_and_limit_rows_to_get(self, proxy):
        """From the current set of rows to get, find the first
        continuous range of rows that should be fetched.
        :return: (offset, limit)
        """
        offset, limit, i = 0, 0, 0
        locker = QtCore.QMutexLocker(proxy._mutex)
        #
        # now filter out all rows that have been put in the cache
        # the gui thread didn't know about
        #
        rows_to_get = self.rows
        rows_already_there = set()
        for row in rows_to_get:
            if proxy.edit_cache.has_data_at_row(row):
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

    def model_run(self, proxy):
        offset, limit = self.offset_and_limit_rows_to_get(proxy)
        self.changed_ranges.extend(proxy._extend_cache(offset, limit))
        self.difference = set( range( offset, offset + limit + 1) )
        return self

    def gui_run(self, item_model):
        item_model.rows_under_request.difference_update(self.difference)
        super(RowData, self).gui_run(item_model)

    def __repr__(self):
        return '{0.__class__.__name__}(rows={1})'.format(self, repr(self.rows))

class SetData(Update):

    def __init__(self, updates):
        super(SetData, self).__init__(None)
        # Copy the update requests and clear the list of requests
        self.updates = [u for u in updates]
        self.created_objects = None
        self.updated_objects = None

    def model_run(self, proxy):
        grouped_requests = collections.defaultdict( list )
        updated_objects, created_objects = set(), set()
        for row, column, value in self.updates:
            grouped_requests[row].append( (column, value) )
        admin = proxy.admin
        for row, request_group in six.iteritems(grouped_requests):
            #
            # don't use get_slice, but only update objects which are in the
            # cache, otherwise it is not sure that the object updated is the
            # one that was edited
            #
            o = proxy.edit_cache.get_entity_at_row( row )
            if o is None:
                # the object might have been deleted from the collection while the editor
                # was still open
                continue
            #
            # the object might have been deleted while an editor was open
            # 
            if admin.is_deleted( o ):
                continue
            changed = False
            for column, value in request_group:
                attribute, field_attributes = proxy._columns[column]

                from sqlalchemy.exc import DatabaseError
                new_value = value()
                proxy.logger.debug( 'set data for row %s;col %s' % ( row, column ) )
    
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
                    proxy.logger.error( u"Can't set attribute %s to %s" % ( attribute, six.text_type( new_value ) ), exc_info = e )
                except TypeError:
                    # type error can be raised in case we try to set to a collection
                    pass
                changed = value_changed or changed
            if changed:
                if proxy.flush_changes:
                    if proxy.validator.isValid( row ):
                        # save the state before the update
                        was_persistent =admin.is_persistent(o)
                        try:
                            admin.flush( o )
                        except DatabaseError as e:
                            #@todo: when flushing fails ??
                            proxy.logger.error( 'Programming Error, could not flush object', exc_info = e )
                        if was_persistent is False:
                            created_objects.add(o)
                # update the cache
                proxy.logger.debug('update cache')
                self.changed_ranges.extend(proxy._add_data(proxy._columns, row, o))
                updated_objects.add(o)
                updated_objects.update(set(admin.get_depending_objects(o)))
        self.created_objects = tuple(created_objects)
        self.updated_objects = tuple(updated_objects)
        return self

    def gui_run(self, item_model):
        super(SetData, self).gui_run(item_model)
        signal_handler = item_model._crud_signal_handler
        signal_handler.send_objects_created(item_model, self.created_objects)
        signal_handler.send_objects_updated(item_model, self.updated_objects)

class Created(RowCount):

    def __init__(self, objects):
        super(Created, self).__init__()
        self.objects = objects

    def model_run(self, proxy):
        # assume rows already contains the new object
        rows = proxy.get_row_count()
        for obj in self.objects:
            if proxy.contains(obj):
                self.rows = rows
                break
        return self

class Sort(RowCount):

    def __init__(self, column, order):
        super(Sort, self).__init__()
        self.column = column
        self.order = order

    def model_run(self, proxy):
        unsorted_collection = [(i,o) for i,o in enumerate(proxy.get_value())]
        field_name = proxy._columns[self.column][0]
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

        unsorted_collection.sort( cmp = compare_none, reverse = self.order )
        for j,(i,_o) in enumerate(unsorted_collection):
            proxy._sort_and_filter[j] = i
        self.rows = len(unsorted_collection)
        return self

class SetColumns(object):

    def __init__(self, columns):
        self.columns = [c[0] for c in columns]
        self.static_field_attributes = None

    def __repr__(self):
        return '{0.__class__.__name__}(columns=[{1}...])'.format(
            self,
            ', '.join(self.columns[:2])
        )

    def model_run(self, proxy):
        self.static_field_attributes = list(
            proxy.admin.get_static_field_attributes(self.columns)
        )
        return self

    def gui_run(self, item_model):
        item_model._static_field_attributes = self.static_field_attributes
        item_model.beginResetModel()
        item_model.settings.beginGroup( 'column_width' )
        item_model.settings.beginGroup( '0' )
        #
        # this loop can take a while to complete
        #
        font_metrics = QtGui.QFontMetrics(item_model._header_font_required)
        char_width = font_metrics.averageCharWidth()
        source_model = item_model.sourceModel()
        #
        # increase the number of columns at once, since this is slow, and
        # setHorizontalHeaderItem will increase the number of columns one by one
        #
        source_model.setColumnCount(len(self.columns))
        for i, (field_name, fa) in enumerate(zip(self.columns,
                                                 self.static_field_attributes)):
            verbose_name = six.text_type(fa['name'])
            header_item = QtGui.QStandardItem()
            set_header_data = header_item.setData
            #
            # Set the header data
            #
            set_header_data(py_to_variant( verbose_name ), Qt.DisplayRole)
            if fa.get( 'nullable', True ) == False:
                set_header_data(item_model._header_font_required, Qt.FontRole)
            else:
                set_header_data(item_model._header_font, Qt.FontRole)

            settings_width = int( variant_to_py( item_model.settings.value( field_name, 0 ) ) )
            if settings_width > 0:
                width = settings_width
            else:
                width = fa['column_width'] * char_width
            header_item.setData( py_to_variant( QtCore.QSize( width, item_model._horizontal_header_height ) ),
                                 Qt.SizeHintRole )
            source_model.setHorizontalHeaderItem( i, header_item )
        item_model.settings.endGroup()
        item_model.settings.endGroup()
        item_model.endResetModel()

# QIdentityProxyModel should be used instead of QSortFilterProxyModel, but
# QIdentityProxyModel is missing from PySide
class CollectionProxy(QtModel.QSortFilterProxyModel):
    """The :class:`CollectionProxy` contains a limited copy of the data in the
    actual collection, usable for fast visualisation in a 
    :class:`QtWidgets.QTableView`  

    The behavior of the :class:`QtWidgets.QTableView`, such as what happens when the
    user clicks on a row is defined in the :class:`ObjectAdmin` class.

    """

    def __init__( self,
                  admin,
                  max_number_of_rows = 10, 
                  flush_changes = True,
                  ):
        """
:param admin: the admin interface for the items in the collection

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
        self.logger.debug('initialize proxy for %s' % (admin.get_verbose_name()))
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
        self._value = None
        self.flush_changes = flush_changes
        self.mt = get_model_thread()
        #
        # The timer reduced the number of times the model thread is
        # triggered, by waiting for the next gui event before triggering
        # the model
        #
        timer = QtCore.QTimer(self)
        timer.setInterval(5)
        timer.setSingleShot(True)
        timer.setObjectName('timer')
        timer.timeout.connect(self.timeout_slot)

        self._columns = []
        self._static_field_attributes = []
        self._max_number_of_rows = max_number_of_rows

        # The rows in the table for which a cache refill is under request
        self.rows_under_request = set()
        # once the cache has been cleared, no updates ought to be accepted
        self._update_requests = list()
        self.__crud_requests = collections.deque()

        self._reset()
        self._sort_and_filter = SortingRowMapper()
        self._crud_signal_handler = CrudSignalHandler()
        self._crud_signal_handler.connect_signals( self )
#    # in that way the number of rows is requested as well
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
        rows = super(CollectionProxy, self).rowCount()
        self.logger.debug('row count requested, returned {0}'.format(rows))
        # no need to count rows when there is no value or there are no columns
        if (rows == 0) and (self._value is not None) and (self._static_field_attributes):
            root_item = self.source_model.invisibleRootItem()
            if not root_item.isEnabled():
                if not isinstance(self._last_request(), RowCount):
                    self._append_request(RowCount())
            return 0
        return rows

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

    #
    # begin functions that handle the timer
    # to group requests to the model thread
    #

    @QtCore.qt_slot()
    def timeout_slot(self):
        self.logger.debug('timout slot')
        timer = self.findChild(QtCore.QTimer, 'timer')
        if timer is not None:
            timer.stop()
            if self._update_requests:
                self._append_request(SetData(self._update_requests))
                self._update_requests = list()
            if self.rows_under_request:
                self._append_request(RowData(self.rows_under_request))
            while len(self.__crud_requests):
                request = self.__crud_requests.popleft()
                self.logger.debug('post request {0}'.format(request))
                post(request.model_run, self._crud_update, args=(self,))

    def _start_timer(self):
        """
        Start the timer if it is not yet active.
        """
        timer = self.findChild(QtCore.QTimer, 'timer')
        if (timer is not None) and (not timer.isActive()):
            timer.start()

    def _last_request(self):
        """
        :return: the last crud request issued, or `None` if the queue is empty
        """
        if len(self.__crud_requests):
            return self.__crud_requests[-1]

    def _append_request(self, request):
        """
        Always use this method to add CRUD requests to the queue, since it
        will make sure no request is added to the queue while handling the
        feedback from a request.
        """
        self.logger.debug('append request {0}'.format(request))
        self.__crud_requests.append(request)
        self._start_timer()

    #
    # end of timer functions
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

    def get_row_count( self ):
        locker = QtCore.QMutexLocker(self._mutex)
        # make sure we don't count an object twice if it is twice
        # in the list, since this will drive the cache nuts
        rows = len( set( self.get_value() ) )
        locker.unlock()
        return rows

    @QtCore.qt_slot(int)
    def _refresh_content(self, rows ):
        assert object_thread( self )
        assert isinstance(rows, six.integer_types)
        self._reset(row_count=rows)
        self.layoutChanged.emit()

    @QtCore.qt_slot(object)
    def _crud_update(self, crud_request):
        self.logger.debug('begin update {0}'.format(crud_request))
        try:
            crud_request.gui_run(self)
            self.logger.debug('end update {0}'.format(crud_request))
        except Exception as e:
            self.logger.error('exception during update {0}'.format(crud_request),
                              exc_info=e
                              )
        

    def refresh(self):
        self._reset()
        self.layoutChanged.emit()

    def _reset(self, cache_collection_proxy=None, row_count=None):
        """
        reset all shared state and cache
        """
        # make sure all pending requests are handled before removing things
        # wont work since _reset is called within the handling of crud requests
        # self.timeout_slot()
        # end
        max_cache = 10 * self.max_number_of_rows
        locker = QtCore.QMutexLocker(self._mutex)
        if cache_collection_proxy is not None:
            self.logger.debug('_reset state from cache')
            cached_entries = len( cache_collection_proxy.display_cache )
            max_cache = max( cached_entries, max_cache )
            self.display_cache = cache_collection_proxy.display_cache.shallow_copy( max_cache )
            self.edit_cache = cache_collection_proxy.edit_cache.shallow_copy( max_cache )
            self.attributes_cache = cache_collection_proxy.attributes_cache.shallow_copy( max_cache )
            self.source_model.setRowCount(cache_collection_proxy.rowCount())
        else:
            self.logger.debug('_reset state')
            self.display_cache = Fifo( max_cache )
            self.edit_cache = Fifo( max_cache )
            self.attributes_cache = Fifo( max_cache )
            root_item = self.source_model.invisibleRootItem()
            root_item.setEnabled(row_count != None)
            self.source_model.setRowCount(row_count or 0)
        # The rows in the table for which a cache refill is under request
        self.rows_under_request = set()
        # once the cache has been cleared, no updates ought to be accepted
        self._update_requests = list()
        locker.unlock()

    def set_value(self, value, cache_collection_proxy=None):
        """
        :param value: the collection of objects to display or None
        :param cache_collection_proxy: the CollectionProxy on which this CollectionProxy
        will reuse the cache. Passing a cache has the advantage that objects that were
        present in the original cache will remain at the same row in the new cache
        This is used when a form is created from a tableview.  Because between the last
        query of the tableview, and the first of the form, the object might have changed
        position in the query.
        """
        if isinstance(value, CollectionContainer):
            value = value._collection
        self._value = value
        self._reset(cache_collection_proxy)
        self.layoutChanged.emit()
    
    def get_value(self):
        return self._value

    @QtCore.qt_slot(object, tuple)
    def objects_updated(self, sender, objects):
        """Handles the entity signal, indicating that the model is out of
        date
        """
        assert object_thread(self)
        if sender != self:
            self.logger.debug(
                'received {0} objects updated'.format(len(objects))
            )
            self._append_request(Update(objects))
            self._start_timer()

    @QtCore.qt_slot(object, tuple)
    def objects_deleted(self, sender, objects):
        """Handles the entity signal, indicating that the model is out of
        date"""
        assert object_thread( self )
        if sender != self:
            self.logger.debug(
                'received {0} objects deleted'.format(len(objects))
            )
            self._append_request(Deleted(objects))
            self._start_timer()

    @QtCore.qt_slot(object, tuple)
    def objects_created(self, sender, objects):
        """Handles the entity signal, indicating that the model is out of
        date"""
        assert object_thread( self )
        if sender != self:
            self.logger.debug(
                'received {0} objects created'.format(len(objects))
            )
            self._append_request(Created(objects))
            self._start_timer()

    def set_columns(self, columns):
        """Callback method to set the columns

        :param columns: a list with fields to be displayed of the form [('field_name', field_attributes), ...] as
        returned by the `get_columns` method of the `EntityAdmin` class
        """
        self.logger.debug( 'set_columns' )
        assert object_thread( self )
        self._columns = columns
        self._append_request(SetColumns(columns))
        self._start_timer()

    def setHeaderData(self, section, orientation, value, role):
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
        source_model = self.sourceModel()
        source_model.setHeaderData(section, orientation, value, role)
    
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
            source_model = self.sourceModel()
            item = source_model.verticalHeaderItem(section)
            if item is None:
                if section not in self.rows_under_request:
                    self.rows_under_request.add(section)
                    self._start_timer()
                return py_to_variant(None)
            if role == Qt.DecorationRole:
                icon = variant_to_py(item.data(role))
                if icon is not None:
                    return py_to_variant(icon.getQPixmap())
            else:
                return item.data(role)

        return self.sourceModel().headerData(section, orientation, role)

    def sort( self, column, order ):
        """reimplementation of the :class:`QtGui.QAbstractItemModel` its sort function"""
        assert object_thread( self )
        self._append_request(Sort(column, order))
        self._start_timer()

    def data( self, index, role = Qt.DisplayRole):
        """:return: the data at index for the specified role
        This function will return ValueLoading when the data has not
        yet been fetched from the underlying model.  It will then send
        a request to the model thread to fetch this data.  Once the data
        is readily available, the dataChanged signal will be emitted
        """
        assert object_thread( self )
        if (not index.isValid()) or (index.model()!=self):
            if role == FieldAttributesRole:
                return invalid_field_attributes_data
            else:
                return invalid_data

        root_item = self.source_model.invisibleRootItem()
        child_item = root_item.child(index.row(), index.column())

        if child_item is None:
            row = index.row()
            if row not in self.rows_under_request:
                self.rows_under_request.add(row)
                self._start_timer()
            if role == FieldAttributesRole:
                return py_to_variant(
                    ProxyDict(self._static_field_attributes[index.column()])
                )
            return py_to_variant(ValueLoading)

        # the standard implementation uses EditRole as DisplayRole
        if role == Qt.DisplayRole:
            role = PreviewRole
        elif role == ObjectRole:
            return self.headerData(index.row(), Qt.Vertical, role)

        return child_item.data(role)

        #if role in (Qt.EditRole, Qt.DisplayRole):
            #if role == Qt.EditRole:
                #cache = self.edit_cache
            #else:
                #cache = self.display_cache
            #data = self._get_row_data( index.row(), cache )
            #value = data[index.column()]
            #if isinstance(value, datetime.datetime):
                ## Putting a python datetime into a Qt Variant and returning
                ## it to a PyObject seems to be buggy, therefore we chop the
                ## microseconds
                #if value:
                    #value = QtCore.QDateTime(value.year, value.month,
                                             #value.day, value.hour,
                                             #value.minute, value.second)
            #elif isinstance(value, (list, dict)):
                #value = CollectionContainer(value)
            #return py_to_variant( value )
        #elif role == Qt.ToolTipRole:
            #return py_to_variant(self._get_field_attribute_value(index, 'tooltip'))
        #elif role == Qt.BackgroundRole:
            #return py_to_variant(self._get_field_attribute_value(index, 'background_color') or py_to_variant())
        #elif role == FieldAttributesRole:
            #field_attributes = ProxyDict(self._static_field_attributes[index.column()])
            #dynamic_field_attributes = self._get_row_data( index.row(), self.attributes_cache )[index.column()]
            #if dynamic_field_attributes != ValueLoading:
                #field_attributes.update( dynamic_field_attributes )
            #return py_to_variant(field_attributes)
        #elif role == ObjectRole:
            #try:
                #return py_to_variant( self.edit_cache.get_entity_at_row( index.row() ) )
            #except KeyError:
                #return py_to_variant( ValueLoading )
        #return py_to_variant()

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
            self.logger.debug('set data ({0},{1})'.format(index.row(), index.column()))
            locker = QtCore.QMutexLocker( self._mutex )
            self._update_requests.append( (index.row(), index.column(), value) )
            locker.unlock()
            self._start_timer()
        return True

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
        :param r"ow: the row in the cache into which to add data
        :param obj: the object from which to strip the data
        :return: the changes to the item model
        """
        action_state = None
        changed_ranges = []
        logger.debug('_add data for row {0}'.format(row))
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
        locker.unlock()
        if row is not None:
            items = []
            for column in changed_columns:
                field_attributes = dynamic_field_attributes[column]
                field_attributes.update(self._static_field_attributes[column])
                item = QtModel.QStandardItem()
                item.setData(py_to_variant(row_data[column]), Qt.EditRole)
                item.setData(py_to_variant(ProxyDict(field_attributes)), FieldAttributesRole)
                item.setData(py_to_variant(unicode_row_data[column]), PreviewRole)
                items.append((column, item))
            header_item = QtModel.QStandardItem()
            header_item.setData(py_to_variant(obj), ObjectRole)
            if action_state is not None:
                header_item.setData(py_to_variant(action_state.tooltip), Qt.ToolTipRole)
                header_item.setData(py_to_variant(row+1), Qt.DisplayRole)
                header_item.setData(py_to_variant(action_state.icon), Qt.DecorationRole)
            changed_ranges.append((row, header_item, items))
        return changed_ranges

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

    def _extend_cache(self, offset, limit):
        """Extend the cache around the rows under request"""
        changed_ranges = []
        if limit:
            columns = self._columns
            collection = self.get_value()
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
                            changed_ranges.extend(self._add_data(columns, i, obj))
                            object_found = True
            except IndexError:
                # stop when the end of the collection is reached, no matter
                # what the request was
                pass
        return changed_ranges

    def get_slice(self, i, j, yield_per=None):
        """
        Get an iterator over a number of objects mapped between two rows in the
        proxy.

        The requested row numbers should be positive and smaller than the number
        of rows, or an :attr:`IndexError` will be raised.  The row numbers are
        the row numbers after sorting and filtering, so their relative order
        corresponds to the row numbers showed in the item view.

        :param i: the row number of the first object in the slice
        :param j: the row number of the first object not in the slice
        :param yield_per: an integer number giving a hint on how many objects
            should fetched from the database at the same time
        :return: an iterator over the objects in the slice

        The number of objects returned by the iterator is not guaranteed to be
        `j-i` since the underlying collection might have been modified without
        the proxy being aware of it.

        This method guarantees temporary consistency with the view, meaning that
        while the iterator returns an object, that object will be in the same
        row in the view.  However when the iterator returns the next object,
        there is no guarantee any more over the row of the previous object.
        """

        # for now, dont get the actual number of rows, as this might be too
        # slow
        row_count = sys.maxint
        if not (0<=i<=row_count):
            raise IndexError('first row not in range', i, 0, row_count)
        if not (0<=j<=row_count):
            raise IndexError('last row not in range', j, 0, row_count)
        for row in xrange(i, j):
            try:
                obj = self.edit_cache.get_entity_at_row(row)
            except KeyError:
                self._extend_cache(row, row+self.edit_cache.max_entries)
                try:
                    obj = self.edit_cache.get_entity_at_row(row)
                except KeyError:
                    # there is no data available to extend the cache any
                    # more
                    break
            yield obj

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
            logger.debug( 'data in row {0} not yet loaded row'.format(row))
            if row not in self.rows_under_request:
                self.rows_under_request.add(row)
                self._start_timer()
            return empty_row_data

    def remove( self, o ):
        collection = self.get_value()
        if o in collection:
            collection.remove( o )

    def append( self, o ):
        collection = self.get_value()
        if o not in collection:
            collection.append( o )

    def contains(self, obj):
        collection = self.get_value()
        return (obj in collection)

    def get_admin( self ):
        """Get the admin object associated with this model"""
        return self.admin

