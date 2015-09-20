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
import logging

logger = logging.getLogger(__name__)

import six

from camelot.admin.action.list_action import ListActionModelContext
from sqlalchemy.ext.hybrid import hybrid_property

from ...container.collection_container import CollectionContainer
from ...core.qt import (Qt, QtCore, QtGui, QtModel, QtWidgets,
                        py_to_variant, variant_to_py)
from ...core.item_model import (ProxyDict, VerboseIdentifierRole, ObjectRole,
                                FieldAttributesRole, PreviewRole, ListModelProxy)
from ..crud_signals import CrudSignalHandler
from camelot.core.exception import log_programming_error
from camelot.view.fifo import Fifo
from camelot.view.model_thread import object_thread, post


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

from camelot.view.proxy import ValueLoading

class EmptyRowData( object ):
    def __getitem__( self, column ):
        return ValueLoading

empty_row_data = EmptyRowData()

invalid_data = py_to_variant()
invalid_field_attributes_data = py_to_variant({})

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

class UpdateMixin(object):

    def gui_run(self, item_model):
        root_item = item_model.invisibleRootItem()
        for row, header_item, items in self.changed_ranges:
            item_model.setVerticalHeaderItem(row, header_item)
            for column, item in items:
                root_item.setChild(row, column, item)

class Update(UpdateMixin):

    def __init__(self, proxy, objects):
        self.proxy = proxy
        self.objects = objects
        self.changed_ranges = []

    def model_run(self, item_model):
        for obj in self.objects:
            try:
                row = self.proxy.index(obj)
            except ValueError:
                continue
            #
            # Because the entity is updated, it might no longer be in our
            # collection, therefore, make sure we don't access the collection
            # to strip data of the entity
            #
            columns = item_model._columns
            self.changed_ranges.extend(item_model._add_data(columns, row, obj, True))
        return self

class Deleted(object):

    def __init__(self, proxy, objects):
        self.proxy = proxy
        self.objects = objects
        self.rows = None

    def model_run(self, item_model):
        for obj in self.objects:
            try:
                item_model.display_cache.get_row_by_entity(obj)
            except KeyError:
                continue
            self.proxy.remove(obj)
            item_model.display_cache.delete_by_entity( obj )
            item_model.attributes_cache.delete_by_entity( obj )
            item_model.edit_cache.delete_by_entity( obj )
        self.rows = len(self.proxy)
        return self

    def gui_run(self, item_model):
        item_model._refresh_content(self.rows)

class RowCount(object):

    def __init__(self, proxy):
        self.proxy = proxy
        self.rows = None

    def model_run(self, proxy):
        self.rows = len(self.proxy)
        return self

    def gui_run(self, item_model):
        if self.rows is not None:
            item_model._refresh_content(self.rows)

    def __repr__(self):
        return '{0.__class__.__name__}(rows={0.rows})'.format(self)

class RowData(Update):

    def __init__(self, proxy, rows):
        super(RowData, self).__init__(proxy, None)
        self.rows = set(rows)
        self.difference = None
        self.changed_ranges = []

    def offset_and_limit_rows_to_get(self):
        """From the current set of rows to get, find the first
        continuous range of rows that should be fetched.
        :return: (offset, limit)
        """
        offset, limit, i = 0, 0, 0
        rows_to_get = list(self.rows)
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

    def model_run(self, item_model):
        offset, limit = self.offset_and_limit_rows_to_get()
        self.objects = list(self.proxy[offset:offset+limit])
        super(RowData, self).model_run(item_model)
        return self

    def __repr__(self):
        return '{0.__class__.__name__}(rows={1})'.format(self, repr(self.rows))

class SetData(Update):

    def __init__(self, proxy, updates):
        super(SetData, self).__init__(proxy, None)
        # Copy the update requests and clear the list of requests
        self.updates = [u for u in updates]
        self.created_objects = None
        self.updated_objects = None

    def model_run(self, item_model):
        grouped_requests = collections.defaultdict( list )
        updated_objects, created_objects = set(), set()
        for row, obj, column, value in self.updates:
            grouped_requests[(row, obj)].append((column, value))
        admin = item_model.admin
        for (row, obj), request_group in six.iteritems(grouped_requests):
            #
            # don't use get_slice, but only update objects which are in the
            # cache, otherwise it is not sure that the object updated is the
            # one that was edited
            #
            o = item_model.edit_cache.get_entity_at_row(row)
            if not (o is obj):
                item_model.logger.warn('model view inconsistency')
                continue
            #
            # the object might have been deleted while an editor was open
            # 
            if admin.is_deleted( o ):
                continue
            changed = False
            for column, value in request_group:
                attribute, field_attributes = item_model._columns[column]

                from sqlalchemy.exc import DatabaseError
                new_value = variant_to_py(value)
                item_model.logger.debug( 'set data for row %s;col %s' % ( row, column ) )
    
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
                    item_model.logger.error( u"Can't set attribute %s to %s" % ( attribute, six.text_type( new_value ) ), exc_info = e )
                except TypeError:
                    # type error can be raised in case we try to set to a collection
                    pass
                changed = value_changed or changed
            if changed:
                if item_model.flush_changes:
                    if item_model.validator.isValid( row ):
                        # save the state before the update
                        was_persistent =admin.is_persistent(o)
                        try:
                            admin.flush( o )
                        except DatabaseError as e:
                            #@todo: when flushing fails ??
                            item_model.logger.error( 'Programming Error, could not flush object', exc_info = e )
                        if was_persistent is False:
                            created_objects.add(o)
                # update the cache
                self.changed_ranges.extend(item_model._add_data(item_model._columns, row, o, True))
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

class Created(RowCount, UpdateMixin):

    def __init__(self, proxy, objects):
        super(Created, self).__init__(proxy)
        self.objects = objects
        self.changed_ranges = []

    def model_run(self, item_model):
        # assume rows already contains the new object
        rows = len(self.proxy)
        for obj in self.objects:
            try:
                row = self.proxy.index(obj)
            except ValueError:
                continue
            # rows should only be not None when a created object was in the cache
            self.rows = rows
            self.changed_ranges.extend(item_model._add_data(item_model._columns, row, obj, True))
        return self

    def gui_run(self, item_model):
        RowCount.gui_run(self, item_model)
        UpdateMixin.gui_run(self, item_model)

class Sort(RowCount):

    def __init__(self, proxy, column, order):
        super(Sort, self).__init__(proxy)
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
        #
        # increase the number of columns at once, since this is slow, and
        # setHorizontalHeaderItem will increase the number of columns one by one
        #
        item_model.setColumnCount(len(self.columns))
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
            item_model.setHorizontalHeaderItem( i, header_item )
        item_model.settings.endGroup()
        item_model.settings.endGroup()
        item_model.endResetModel()


class CollectionProxy(QtModel.QStandardItemModel):
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
        self.locale = QtCore.QLocale()
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
            root_item = self.invisibleRootItem()
            if not root_item.isEnabled():
                if not isinstance(self._last_request(), RowCount):
                    self._append_request(RowCount(self._value))
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
                self._append_request(SetData(self._value, self._update_requests))
                self._update_requests = list()
            if self.rows_under_request:
                self._append_request(RowData(self._value, self.rows_under_request))
            while len(self.__crud_requests):
                request = self.__crud_requests.popleft()
                self.logger.debug('post request {0}'.format(request))
                post(request.model_run, self._crud_update, args=(self,), exception=self._crud_exception)

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

    def get_validator(self):
        return self.validator

    @QtCore.qt_slot(int)
    def _refresh_content(self, rows ):
        assert object_thread( self )
        assert isinstance(rows, six.integer_types)
        self._reset(row_count=rows)
        self.layoutChanged.emit()

    @QtCore.qt_slot(object)
    def _crud_exception(self, exception_info):
        self.logger.error('CRUD exception')
        
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

    def _reset(self, row_count=None):
        """
        reset all shared state and cache
        """
        # make sure all pending requests are handled before removing things
        # wont work since _reset is called within the handling of crud requests
        # self.timeout_slot()
        # end
        max_cache = 10 * self._max_number_of_rows
        locker = QtCore.QMutexLocker(self._mutex)
        # is this the best way to reset the standard items ? maybe it's much
        # easier to replace the source model all at once
        self.setRowCount(0)
        self.logger.debug('_reset state')
        self.edit_cache = Fifo( max_cache )
        self.attributes_cache = Fifo( max_cache )
        root_item = self.invisibleRootItem()
        root_item.setEnabled(row_count != None)
        self.setRowCount(row_count or 0)
        # The rows in the table for which a cache refill is under request
        self.rows_under_request = set()
        # once the cache has been cleared, no updates ought to be accepted
        self._update_requests = list()
        locker.unlock()

    def set_value(self, value):
        """
        :param value: the collection of objects to display or None
        """
        if isinstance(value, CollectionContainer):
            value = value._collection
        self._value = ListModelProxy(value)
        self._reset()
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
            self._append_request(Update(self._value, objects))
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
            self._append_request(Deleted(self._value, objects))
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
            self._append_request(Created(self._value, objects))
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
        return super(CollectionProxy, self).setHeaderData(section, orientation, value, role)
    
    def headerData( self, section, orientation, role ):
        """In case the columns have not been set yet, don't even try to get
        information out of them
        """
        assert object_thread( self )
        if (orientation == Qt.Vertical) and (section >= 0):
            if role == Qt.SizeHintRole:
                #
                # sizehint role is requested, for every row, so we have to
                # return a fixed value
                #
                return py_to_variant(self.vertical_header_size)
            item = self.verticalHeaderItem(section)
            if item is None:
                if section not in self.rows_under_request:
                    self.rows_under_request.add(section)
                    self._start_timer()
                return invalid_data
            if role == Qt.DecorationRole:
                icon = variant_to_py(item.data(role))
                if icon is not None:
                    return py_to_variant(icon.getQPixmap())
            else:
                return item.data(role)

        return super(CollectionProxy, self).headerData(section, orientation, role)

    def sort( self, column, order ):
        """reimplementation of the :class:`QtGui.QAbstractItemModel` its sort function"""
        assert object_thread( self )
        self._append_request(Sort(self._value, column, order))
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

        root_item = self.invisibleRootItem()
        child_item = root_item.child(index.row(), index.column())

        # the standard implementation uses EditRole as DisplayRole
        if role == Qt.DisplayRole:
            role = PreviewRole

        if child_item is None:
            row = index.row()
            if (row not in self.rows_under_request) and (row >= 0):
                self.rows_under_request.add(row)
                self._start_timer()
            if role == FieldAttributesRole:
                return py_to_variant(
                    ProxyDict(self._static_field_attributes[index.column()])
                )
            elif role in (PreviewRole, ObjectRole):
                return invalid_data
            return py_to_variant(ValueLoading)


        if role == ObjectRole:
            return self.headerData(index.row(), Qt.Vertical, role)

        return child_item.data(role)

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
            field_attributes = variant_to_py(self.data(index, FieldAttributesRole))
            if field_attributes.get('editable') != True:
                return
            row = index.row()
            column = index.column()
            obj = variant_to_py(self.headerData(row, Qt.Vertical, ObjectRole))
            if obj is None:
                return
            self.logger.debug('set data ({0},{1})'.format(row, column))
            self._update_requests.append((row, obj, column, value))
            self._start_timer()
        return True

    def _add_data(self, columns, row, obj, data):
        """Add data from object o at a row in the cache
        :param columns: the columns of which to strip data
        :param r"ow: the row in the cache into which to add data
        :param obj: the object from which to strip the data
        :param data: fill the data cache, otherwise only fills the header cache
        :return: the changes to the item model
        """
        action_state = None
        changed_ranges = []
        logger.debug('_add data for row {0}'.format(row))
        # @todo static field attributes should be cached ??
        if (not self.admin.is_deleted( obj ) and data==True):
            row_data = strip_data_from_object( obj, columns )
            dynamic_field_attributes = list(self.admin.get_dynamic_field_attributes( obj, (c[0] for c in columns)))
            static_field_attributes = list(self.admin.get_static_field_attributes( (c[0] for c in columns) ))
            if self.list_action:
                self.row_model_context.obj = obj
                self.row_model_context.current_row = row
                action_state = self.list_action.get_state(self.row_model_context)
        else:
            row_data = [None] * len(columns)
            dynamic_field_attributes =  [{'editable':False}] * len(columns)
            static_field_attributes = list(self.admin.get_static_field_attributes( (c[0] for c in columns) ))
        # keep track of the columns that changed, to limit the
        # number of editors/cells that need to be updated
        changed_columns = set()
        locker = QtCore.QMutexLocker( self._mutex )
        changed_columns.update( self.edit_cache.add_data( row, obj, row_data ) )
        changed_columns.update( self.attributes_cache.add_data(row, obj, dynamic_field_attributes ) )
        locker.unlock()
        if row is not None:
            items = []
            locale = self.locale
            for column in changed_columns:
                # copy to make sure the original dict can be compared in subsequent
                # calls
                field_attributes = dict(dynamic_field_attributes[column])
                field_attributes.update(static_field_attributes[column])
                delegate = field_attributes['delegate']
                value = row_data[column]
                item = delegate.get_standard_item(locale, value, field_attributes)
                items.append((column, item))
            verbose_identifier = self.admin.get_verbose_identifier(obj)
            header_item = QtModel.QStandardItem()
            header_item.setData(py_to_variant(obj), ObjectRole)
            header_item.setData(py_to_variant(verbose_identifier), VerboseIdentifierRole)
            if action_state is not None:
                header_item.setData(py_to_variant(action_state.tooltip), Qt.ToolTipRole)
                header_item.setData(py_to_variant(row+1), Qt.DisplayRole)
                header_item.setData(py_to_variant(action_state.icon), Qt.DecorationRole)
            changed_ranges.append((row, header_item, items))
        return changed_ranges

    def get_admin( self ):
        """Get the admin object associated with this model"""
        return self.admin
