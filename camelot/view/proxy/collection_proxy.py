#  ============================================================================
#
#  Copyright (C) 2007-2016 Conceptive Engineering bvba.
#  www.conceptive.be / info@conceptive.be
#
#  Redistribution and use in source and binary forms, with or without
#  modification, are permitted provided that the following conditions are met:
#      * Redistributions of source code must retain the above copyright
#        notice, this list of conditions and the following disclaimer.
#      * Redistributions in binary form must reproduce the above copyright
#        notice, this list of conditions and the following disclaimer in the
#        documentation and/or other materials provided with the distribution.
#      * Neither the name of Conceptive Engineering nor the
#        names of its contributors may be used to endorse or promote products
#        derived from this software without specific prior written permission.
#  
#  THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
#  ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
#  WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
#  DISCLAIMED. IN NO EVENT SHALL <COPYRIGHT HOLDER> BE LIABLE FOR ANY
#  DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
#  (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
#  LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
#  ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
#  (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
#  SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
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
import itertools
import logging
import weakref

logger = logging.getLogger(__name__)

import six
from six import moves

from sqlalchemy.ext.hybrid import hybrid_property

from ...admin.action.list_action import ListActionModelContext
from ...core.qt import (Qt, QtCore, QtGui, QtWidgets, is_deleted,
                        py_to_variant, variant_to_py)
from ...core.item_model import (
    VerboseIdentifierRole, ObjectRole, FieldAttributesRole, PreviewRole, 
    ValidRole, ValidMessageRole, ProxyDict, AbstractModelProxy
)
from ..crud_signals import CrudSignalHandler
from ..item_model.cache import ValueCache
from camelot.core.exception import log_programming_error
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
            field_value = getattr( obj, col )
        except (Exception, RuntimeError, TypeError, NameError) as e:
            message = "could not get field '%s' of object of type %s"%(col, obj.__class__.__name__)
            log_programming_error( logger, 
                                   message,
                                   exc_info = e )
        finally:
            row_data.append( field_value )
    return row_data

invalid_data = py_to_variant()
# todo : investigate if the invalid field attributes ought to be
#        the same as the default field attributes in the object admin
invalid_field_attributes_data = py_to_variant(ProxyDict(
    editable=False,
    focus_policy=Qt.NoFocus,
))
invalid_item = QtGui.QStandardItem()
invalid_item.setFlags(Qt.NoItemFlags)
invalid_item.setData(invalid_data, Qt.EditRole)
invalid_item.setData(invalid_data, PreviewRole)
invalid_item.setData(invalid_data, ObjectRole)
invalid_item.setData(invalid_field_attributes_data, FieldAttributesRole)

initial_delay = 50
maximum_delay = 1000

class RowModelContext(ListActionModelContext):
    """A list action model context for a single row.  This context is used
    to get the state of the list action on a row
    """
    
    def __init__( self ):
        super( RowModelContext, self ).__init__()
        self.proxy = None
        self.admin = None
        self.edit_cache = ValueCache(100)
        self.attributes_cache = ValueCache(100)
        self.static_field_attributes = []
        self.current_row = None
        self.selection_count = 0
        self.collection_count = 0
        self.selected_rows = []
        self.field_attributes = dict()
        self.obj = None
        self.locale = QtCore.QLocale()
        
    def get_selection( self, yield_per = None ):
        return []
    
    def get_collection( self, yield_per = None ):
        return []
            
    def get_object( self ):
        return self.obj

class UpdateMixin(object):

    def add_data(self, model_context, row, columns, obj, data):
        """Add data from object o at a row in the cache
        :param row: the row in the cache into which to add data
        :param columns: the columns for which data should be added
        :param obj: the object from which to strip the data
        :param data: fill the data cache, otherwise only fills the header cache
        :return: the changes to the item model
        """
        admin = model_context.admin
        static_field_attributes = model_context.static_field_attributes
        column_names = [model_context.static_field_attributes[column]['field_name'] for column in columns]
        action_state = None
        changed_ranges = []
        logger.debug('add data for row {0}'.format(row))
        # @todo static field attributes should be cached ??
        if (not admin.is_deleted( obj ) and (data==True) and (obj is not None)):
            row_data = {column:data for column, data in zip(columns, strip_data_from_object(obj, column_names))}
            dynamic_field_attributes ={column:fa for column, fa in zip(columns, admin.get_dynamic_field_attributes(obj, column_names))}
            if admin.list_action:
                model_context.obj = obj
                model_context.current_row = row
                action_state = admin.list_action.get_state(model_context)
        else:
            row_data = {column:None for column in columns}
            dynamic_field_attributes = {column:{'editable':False} for column in columns}
        # keep track of the columns that changed, to limit the
        # number of editors/cells that need to be updated
        changed_columns = set()
        changed_columns.update(model_context.edit_cache.add_data(row, obj, row_data))
        changed_columns.update(model_context.attributes_cache.add_data(row, obj, dynamic_field_attributes))
        if row is not None:
            items = []
            locale = model_context.locale
            for column in changed_columns:
                # copy to make sure the original dict can be reused in
                # subsequent calls
                field_attributes = dict(static_field_attributes[column])
                # the dynamic attributes might update the static attributes,
                # if get_dynamic_field_attributes is overwritten, like in 
                # the case of the EntityAdmin setting the onetomany fields
                # to not editable for objects that are not persistent
                field_attributes.update(dynamic_field_attributes[column])
                delegate = field_attributes['delegate']
                value = row_data[column]
                item = delegate.get_standard_item(locale, value, field_attributes)
                items.append((column, item))
            try:
                verbose_identifier = admin.get_verbose_identifier(obj)
            except (Exception, RuntimeError, TypeError, NameError) as e:
                message = "could not get verbose identifier of object of type %s"%(obj.__class__.__name__)
                log_programming_error(logger,
                                      message,
                                      exc_info=e)
                verbose_identifier = u''
            valid = False
            for message in model_context.validator.validate_object(obj):
                break
            else:
                valid = True
                message = None
            header_item = QtGui.QStandardItem()
            header_item.setData(py_to_variant(obj), ObjectRole)
            header_item.setData(py_to_variant(verbose_identifier), VerboseIdentifierRole)
            header_item.setData(py_to_variant(valid), ValidRole)
            header_item.setData(py_to_variant(message), ValidMessageRole)
            if action_state is not None:
                header_item.setData(py_to_variant(action_state.tooltip), Qt.ToolTipRole)
                header_item.setData(py_to_variant(six.text_type(action_state.verbose_name)), Qt.DisplayRole)
                header_item.setData(py_to_variant(action_state.icon), Qt.DecorationRole)
            changed_ranges.append((row, header_item, items))
        return changed_ranges

    def update_item_model(self, item_model):
        root_item = item_model.invisibleRootItem()
        if is_deleted(root_item):
            return
        logger.debug('begin gui update {0} rows'.format(len(self.changed_ranges)))
        row_range = (item_model.rowCount(), -1)
        column_range = (item_model.columnCount(), -1)
        for row, header_item, items in self.changed_ranges:
            row_range = (min(row, row_range[0]), max(row, row_range[1]))
            # Setting the vertical header item causes the table to scroll
            # back to its open editor.  However setting the header item every
            # time data has changed is needed to signal other parts of the
            # gui that the object itself has changed.
            item_model.setVerticalHeaderItem(row, header_item)
            for column, item in items:
                column_range = (min(column, column_range[0]), max(column, column_range[1]))
                root_item.setChild(row, column, item)
        
        logger.debug('end gui update rows {0}, columns {1}'.format(row_range, column_range))

class Update(UpdateMixin):

    def __init__(self, objects):
        self.objects = objects
        self.changed_ranges = []

    def model_run(self, model_context):
        for obj in self.objects:
            try:
                row = model_context.proxy.index(obj)
            except ValueError:
                continue
            #
            # Because the entity is updated, it might no longer be in our
            # collection, therefore, make sure we don't access the collection
            # to strip data of the entity
            #
            columns = tuple(six.iterkeys(model_context.edit_cache.get_data(row)))
            if len(columns):
                logger.debug('evaluate changes in row {0}, column {1} to {2}'.format(row, min(columns), max(columns)))
            else:
                logger.debug('evaluate changes in row {0}'.format(row))
            self.changed_ranges.extend(self.add_data(model_context, row, columns, obj, True))
        return self

    def gui_run(self, item_model):
        self.update_item_model(item_model)

    def __repr__(self):
        return '{0.__class__.__name__}({1} objects)'.format(self, len(self.objects))

class RowCount(object):

    def __init__(self):
        self.rows = None

    def model_run(self, model_context):
        self.rows = len(model_context.proxy)
        # clear the whole cache, there might be more efficient means to 
        # do this
        model_context.edit_cache = ValueCache(model_context.edit_cache.max_entries)
        model_context.attributes_cache = ValueCache(model_context.attributes_cache.max_entries)
        return self

    def gui_run(self, item_model):
        if self.rows is not None:
            item_model._refresh_content(self.rows)

    def __repr__(self):
        return '{0.__class__.__name__}(rows={0.rows})'.format(self)


class Deleted(RowCount, UpdateMixin):

    def __init__(self, objects, rows_in_view):
        """
        
        """
        super(Deleted, self).__init__()
        self.objects = objects
        self.changed_ranges = []
        self.rows_in_view = rows_in_view

    def model_run(self, model_context):
        row = None
        objects_to_remove = set()
        #
        # the object might or might not be in the proxy when the
        # deletion is handled
        #
        for obj in self.objects:
            try:
                row = model_context.proxy.index(obj)
            except ValueError:
                continue
            objects_to_remove.add(obj)
            #
            # If the object was valid, the header item should be updated
            # make sure all views know the validity of the row has changed
            #
            header_item = QtGui.QStandardItem()
            header_item.setData(py_to_variant(None), ObjectRole)
            header_item.setData(py_to_variant(u''), VerboseIdentifierRole)
            header_item.setData(py_to_variant(True), ValidRole)
            self.changed_ranges.append((row, header_item, tuple()))
        #
        # if the object that is going to be deleted is in the proxy, the
        # proxy might be unaware of the deleting, so remove the object from
        # the proxy
        for obj in objects_to_remove:
            model_context.proxy.remove(obj)
        #
        # when it's no longer in the proxy, the len of the proxy will be
        # different from the one of the view
        #
        if (row is not None) or (len(model_context.proxy) != self.rows_in_view):
            # but updating the view is only needed if the rows changed
            super(Deleted, self).model_run(model_context)
        return self

    def gui_run(self, item_model):
        self.update_item_model(item_model)
        RowCount.gui_run(self, item_model)


class Filter(RowCount):

    def __init__(self, action, old_value, new_value):
        super(Filter, self).__init__()
        self.action = action
        self.old_value = old_value
        self.new_value = new_value

    def model_run(self, model_context):
        # comparison of old and new value can only happen in the model thread
        if self.old_value != self.new_value:
            model_context.proxy.filter(self.action, self.new_value)
        super(Filter, self).model_run(model_context)
        return self

    def __repr__(self):
        return '{0.__class__.__name__}(action={1})'.format(
            self,
            type(self.action).__name__
        )

class RowData(Update):

    def __init__(self, rows, cols):
        super(RowData, self).__init__(None)
        self.rows = rows.copy()
        self.cols = cols.copy()
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

    def model_run(self, model_context):
        offset, limit = self.offset_and_limit_rows_to_get()
        for obj in list(model_context.proxy[offset:offset+limit]):
            row = model_context.proxy.index(obj)
            self.changed_ranges.extend(self.add_data(model_context, row, self.cols, obj, True))
        return self

    def gui_run(self, item_model):
        super(RowData, self).gui_run(item_model)
            
    def __repr__(self):
        return '{0.__class__.__name__}(rows={1}, cols={2})'.format(
            self, repr(self.rows), repr(self.cols))

class SetData(Update):

    def __init__(self, updates):
        super(SetData, self).__init__(None)
        # Copy the update requests and clear the list of requests
        self.updates = [u for u in updates]
        self.created_objects = None
        self.updated_objects = None

    def __repr__(self):
        return '{0.__class__.__name__}([{1}])'.format(
            self,
            ', '.join(['(row={0}, column={1})'.format(row, column) for row, _o, column, _v in self.updates])
        )

    def model_run(self, model_context):
        grouped_requests = collections.defaultdict( list )
        updated_objects, created_objects = set(), set()
        for row, obj, column, value in self.updates:
            grouped_requests[(row, obj)].append((column, value))
        admin = model_context.admin
        for (row, obj), request_group in six.iteritems(grouped_requests):
            object_slice = list(model_context.proxy[row:row+1])
            if not len(object_slice):
                logger.error('Cannot set data : no object in row {0}'.format(row))
                continue
            o = object_slice[0]
            if not (o is obj):
                logger.warn('Cannot set data : object in row {0} is inconsistent with view'.format(row))
                continue
            #
            # the object might have been deleted while an editor was open
            # 
            if admin.is_deleted(obj):
                continue
            changed = False
            for column, value in request_group:
                static_field_attributes = model_context.static_field_attributes[column]
                field_name = static_field_attributes['field_name']

                from sqlalchemy.exc import DatabaseError
                new_value = variant_to_py(value)
                logger.debug( 'set data for row %s;col %s' % ( row, column ) )

                old_value = getattr(obj, field_name )
                value_changed = ( new_value != old_value )
                #
                # In case the attribute is a OneToMany or ManyToMany, we cannot simply compare the
                # old and new value to know if the object was changed, so we'll
                # consider it changed anyway
                #
                direction = static_field_attributes.get( 'direction', None )
                if direction in ( 'manytomany', 'onetomany' ):
                    value_changed = True
                if value_changed is not True:
                    continue
                #
                # now check if this column is editable, since editable might be
                # dynamic and change after every change of the object
                #
                fields = [field_name]
                for fa in admin.get_dynamic_field_attributes(obj, fields):
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
                    admin.set_field_value(obj, field_name, new_value)
                    #
                    # setting this attribute, might trigger a default function 
                    # to return a value, that was not returned before
                    #
                    admin.set_defaults(obj)
                except AttributeError as e:
                    logger.error( u"Can't set attribute %s to %s" % ( field_name, six.text_type( new_value ) ), exc_info = e )
                except TypeError:
                    # type error can be raised in case we try to set to a collection
                    pass
                changed = value_changed or changed
            if changed:
                for message in model_context.validator.validate_object(obj):
                    break
                else:
                    # save the state before the update
                    was_persistent = admin.is_persistent(obj)
                    try:
                        admin.flush(obj)
                    except DatabaseError as e:
                        #@todo: when flushing fails ??
                        logger.error( 'Programming Error, could not flush object', exc_info = e )
                    if was_persistent is False:
                        created_objects.add(obj)
                # update the cache
                columns = tuple(moves.xrange(len(model_context.static_field_attributes)))
                self.changed_ranges.extend(self.add_data(model_context, row, columns, obj, True))
                updated_objects.add(obj)
                updated_objects.update(set(admin.get_depending_objects(obj)))
        self.created_objects = tuple(created_objects)
        self.updated_objects = tuple(updated_objects)
        return self

    def gui_run(self, item_model):
        super(SetData, self).gui_run(item_model)
        signal_handler = item_model._crud_signal_handler
        signal_handler.send_objects_created(item_model, self.created_objects)
        signal_handler.send_objects_updated(item_model, self.updated_objects)

class Created(UpdateMixin):
    """
    Does not subclass RowCount, because row count will reset the whole edit
    cache.

    When a created object is detected simply update the row of this object,
    assuming other objects have not been changed position.
    """

    def __init__(self, objects):
        self.objects = objects
        self.changed_ranges = []

    def __repr__(self):
        return '{0.__class__.__name__}({1} objects)'.format(
            self, len(self.objects)
        )

    def model_run(self, model_context):
        # the proxy cannot return it's length including the new object before
        # the new object has been indexed
        for obj in self.objects:
            try:
                row = model_context.proxy.index(obj)
            except ValueError:
                continue
            columns = tuple(range(len(model_context.static_field_attributes)))
            self.changed_ranges.extend(self.add_data(model_context, row, columns, obj, True))
        return self

    def gui_run(self, item_model):
        # appending new items to the model will increase the rowcount, so
        # there is no need to set the rowcount explicitly
        self.update_item_model(item_model)

class Sort(RowCount):

    def __init__(self, column, order):
        super(Sort, self).__init__()
        self.column = column
        self.order = order

    def model_run(self, model_context):
        field_name = model_context.static_field_attributes[self.column]['field_name']
        model_context.proxy.sort(field_name, self.order!=Qt.AscendingOrder)
        super(Sort, self).model_run(model_context)
        return self

    def __repr__(self):
        return '{0.__class__.__name__}(column={0.column}, order={0.order})'.format(self)

class SetColumns(object):

    def __init__(self, columns):
        """
        :param columns: a list with field names
        """
        self.columns = list(columns)
        self.static_field_attributes = None

    def __repr__(self):
        return '{0.__class__.__name__}(columns=[{1}...])'.format(
            self,
            ', '.join([col for col, _i in zip(self.columns, (1,2,))])
        )

    def model_run(self, model_context):
        model_context.static_field_attributes = list(
            model_context.admin.get_static_field_attributes(self.columns)
        )
        # creating the header items should be done here instead of in the gui
        # run
        self.static_field_attributes = model_context.static_field_attributes
        return self

    def gui_run(self, item_model):
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
        item_model.setColumnCount(len(self.static_field_attributes))
        for i, fa in enumerate(self.static_field_attributes):
            verbose_name = six.text_type(fa['name'])
            field_name = fa['field_name']
            header_item = QtGui.QStandardItem()
            set_header_data = header_item.setData
            #
            # Set the header data
            #
            set_header_data(py_to_variant(field_name), Qt.UserRole)
            set_header_data(py_to_variant(verbose_name), Qt.DisplayRole)
            set_header_data(py_to_variant({'editable': fa.get('editable', True)}), FieldAttributesRole)
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

class SetHeaderData(object):

    def __init__(self, column, width):
        self.column = column
        self.width = width
        self.field_name = None

    def __repr__(self):
        return '{0.__class__.__name__}({0.column}, {0.width})'.format(self)

    def model_run(self, model_context):
        self.field_name = model_context.static_field_attributes[self.column]['field_name']
        return self

    def gui_run(self, item_model):
        item_model.settings.beginGroup('column_width')
        item_model.settings.beginGroup('0')
        item_model.settings.setValue(self.field_name, self.width)
        item_model.settings.endGroup()
        item_model.settings.endGroup()
        
class CollectionProxy(QtGui.QStandardItemModel):
    """The :class:`CollectionProxy` contains a limited copy of the data in the
    actual collection, usable for fast visualisation in a 
    :class:`QtWidgets.QTableView`  

    The behavior of the :class:`QtWidgets.QTableView`, such as what happens when the
    user clicks on a row is defined in the :class:`ObjectAdmin` class.

    :attr instances: the set of `CollectionProxy` instances.  To be used
        during unit testing to fire the timer events of all models without
        waiting
    """

    instances = weakref.WeakSet()

    def __init__(self, admin, max_number_of_rows=10):
        """
        :param admin: the admin interface for the items in the collection
        """
        super(CollectionProxy, self).__init__()
        assert object_thread( self )
        from camelot.view.model_thread import get_model_thread

        self.logger = logger.getChild('{0}.{1}'.format(id(self), admin.entity.__name__))
        self.logger.debug('initialize proxy for %s' % (admin.get_verbose_name()))
        self.admin = admin
        self._list_action = admin.list_action
        self.settings = self.admin.get_settings()
        self._horizontal_header_height = QtGui.QFontMetrics( self._header_font_required ).height() + 10
        self._header_font_metrics = QtGui.QFontMetrics( self._header_font )
        vertical_header_font_height = QtGui.QFontMetrics( self._header_font ).height()
        self._vertical_header_height = vertical_header_font_height * self.admin.lines_per_row + 10
        self.vertical_header_size =  QtCore.QSize( 16 + 10,
                                                   self._vertical_header_height )
        self._max_number_of_rows = max_number_of_rows
        self._model_context = None
        self._model_thread = get_model_thread()
        #
        # The timer reduced the number of times the model thread is
        # triggered, by waiting for the next gui event before triggering
        # the model
        #
        timer = QtCore.QTimer(self)
        timer.setInterval(initial_delay)
        timer.setSingleShot(True)
        timer.setObjectName('timer')
        timer.timeout.connect(self.timeout_slot)

        self.__time = QtCore.QTime()
        self.__time.start()

        self._filters = dict()
        self._columns = []

        self.__crud_request_counter = itertools.count()
        self.__crud_requests = collections.deque()

        self._reset()
        self._crud_signal_handler = CrudSignalHandler()
        self._crud_signal_handler.connect_signals( self )
        self.instances.add(self)
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
        # no need to count rows when there is no value or there are no columns
        if (rows == 0) and (self._model_context is not None) and self.columnCount():
            root_item = self.invisibleRootItem()
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
    # begin functions that handle the timer
    # to group requests to the model thread
    #

    @QtCore.qt_slot()
    def timeout_slot(self):
        self.logger.debug('timout slot')
        timer = self.findChild(QtCore.QTimer, 'timer')
        if timer is not None:
            if self._update_requests:
                self._append_request(SetData(self._update_requests))
                self._update_requests = list()
            if self._rows_under_request:
                self._append_request(
                    RowData(self._rows_under_request, self._cols_under_request)
                )
                self._rows_under_request.clear()
                self._cols_under_request.clear()
            # stop the timer after adding the requests, otherwise the timer
            # will be trigered again
            timer.stop()
            # only slow down if the timout actually caused requests and
            # requests are arriving at the speed of the interval
            if len(self.__crud_requests) and (self.__time.restart() < (timer.interval() + initial_delay)):
                # convert interval to int in case a long is returned
                timer.setInterval(min(maximum_delay, int(timer.interval()) * 2))
            while len(self.__crud_requests):
                model_context, request_id, request = self.__crud_requests.popleft()
                self.logger.debug('post request {0} {1}'.format(request_id, request))
                post(request.model_run, self._crud_update, args=(model_context,), exception=self._crud_exception)

    def _start_timer(self):
        """
        Start the timer if it is not yet active.
        """
        timer = self.findChild(QtCore.QTimer, 'timer')
        if (timer is not None) and (not timer.isActive()):
            if self.__time.elapsed() > (timer.interval() + (2*initial_delay)):
                # reset the interval after enough time has passed
                timer.setInterval(initial_delay)
            timer.start()

    def _last_request(self):
        """
        :return: the last crud request issued, or `None` if the queue is empty
        """
        if len(self.__crud_requests):
            return self.__crud_requests[-1][-1]

    def _append_request(self, request):
        """
        Always use this method to add CRUD requests to the queue, since it
        will make sure :
        - no request is added to the queue while handling the
          feedback from a request.
        - the timer for handling the requests is started
        - the request is associated with the current model context
        """
        request_id = six.next(self.__crud_request_counter)
        self.logger.debug('append request {0} {1}'.format(request_id, request))
        self.__crud_requests.append((self._model_context, request_id, request))
        self._start_timer()

    #
    # end of timer functions
    #


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
        self.logger.debug('refresh called')
        self._reset()
        self.layoutChanged.emit()

    def _reset(self, row_count=None):
        """
        reset all shared state and cache
        """
        self.logger.debug('_reset(row_count={0})'.format(row_count))
        #
        # clear the request state before changing the model, changing the
        # model will trigger signals, filling the state again
        #
        # A dictionary where the key is the row for which data is requested,
        # and the value indicating if the request has been send
        self._rows_under_request = set()
        self._cols_under_request = set()
        # once the cache has been cleared, no updates ought to be accepted
        self._update_requests = list()
        # make sure all pending requests are handled before removing things
        # wont work since _reset is called within the handling of crud requests
        # self.timeout_slot()
        #
        # is this the best way to reset the standard items ? maybe it's much
        # easier to replace the source model all at once
        self.setRowCount(0)
        root_item = self.invisibleRootItem()
        root_item.setFlags(Qt.NoItemFlags)
        root_item.setEnabled(row_count != None)
        self.setRowCount(row_count or 0)
        self.logger.debug('_reset end')

    def set_value(self, value):
        """
        :param value: the collection of objects to display or None
        """
        self.logger.debug('set_value called')
        assert isinstance(value, AbstractModelProxy)
        model_context = RowModelContext()
        model_context.admin = self.admin
        model_context.proxy = value
        # todo : remove the concept of a validator
        model_context.validator = self.admin.get_validator()
        self._model_context = model_context
        #self._filters = dict()
        self._reset()
        # filters might be applied before the value is set
        for list_filter, value in six.iteritems(self._filters):
            self._append_request(Filter(list_filter, None, value))
        # the columns might be set before the value, but they might be running
        # in the model thread for a different model context as well, so
        # resubmit the set columns task for this model context
        self._append_request(SetColumns(self._columns))
        self.layoutChanged.emit()
    
    def get_value(self):
        if self._model_context is not None:
            return self._model_context.proxy

    def set_filter(self, list_filter, value):
        """
        Set the filter mode for a specific filter

        :param list_filter: a :class:`camelot.admin.action.list_filter.Filter`
           object, used as the key to filter on
        :param value: the value on which to filter,
        """
        self.logger.debug('set_filter called')
        old_value = self._filters.get(list_filter)
        self._filters[list_filter] = value
        if (self._model_context is not None):
            self._append_request(Filter(list_filter, old_value, value))

    @QtCore.qt_slot(object, tuple)
    def objects_updated(self, sender, objects):
        """Handles the entity signal, indicating that the model is out of
            )
        date
        """
        assert object_thread(self)
        if sender != self:
            self.logger.debug(
                'received {0} objects updated'.format(len(objects))
            )
            self._append_request(Update(objects))

    @QtCore.qt_slot(object, tuple)
    def objects_deleted(self, sender, objects):
        """Handles the entity signal, indicating that the model is out of
        date"""
        assert object_thread( self )
        if sender != self:
            self.logger.debug(
                'received {0} objects deleted'.format(len(objects))
                )
            self._append_request(Deleted(objects, super(CollectionProxy, self).rowCount()))

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


    def add_columns(self, field_names):
        """
        Add columns to the columns available through the model

        :param field_names: an iterable of field names
        :return: a generator of column indexes on which the data for these
            field names will be available.

        When the same field name appears multiple times in field_names, it will
        generate different indices.  This is needed for the view, since the
        views use the same indices as the model, and the view needs to be able
        to make the disctinction between different cells pointing to the same
        field.
        """
        self.logger.debug('add_columns called')
        assert object_thread(self)
        for i, field_name in enumerate(field_names):
            self._columns.append(field_name)
            yield i
        if len(self._columns) and (self._model_context is not None):
            self._append_request(SetColumns(self._columns))

    def setHeaderData(self, section, orientation, value, role):
        self.logger.debug('setHeaderData called')
        assert object_thread( self )
        if orientation == Qt.Horizontal:
            if role == Qt.SizeHintRole:
                width = value.width()
                self._append_request(SetHeaderData(section, width))
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
                if section not in self._rows_under_request:
                    self._rows_under_request.add(section)
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
        self.logger.debug('sort called')
        assert object_thread( self )
        self._append_request(Sort(column, order))

    def data(self, index, role = Qt.DisplayRole):
        """:return: the data at index for the specified role
        This function will return ValueLoading when the data has not
        yet been fetched from the underlying model.  It will then send
        a request to the model thread to fetch this data.  Once the data
        is readily available, the dataChanged signal will be emitted
        """
        #
        # this method is performance critical, do as few things as possible
        # here
        #
        if (not index.isValid()) or (index.model()!=self):
            if role == FieldAttributesRole:
                return invalid_field_attributes_data
            else:
                return invalid_data

        root_item = self.invisibleRootItem()
        row = index.row()
        col = index.column()
        child_item = root_item.child(row, col)
        # the standard implementation uses EditRole as DisplayRole
        if role == Qt.DisplayRole:
            role = PreviewRole

        if child_item is None:
            if (row not in self._rows_under_request) or (col not in self._cols_under_request):
                if (row >= 0) and (col >= 0):
                    self._rows_under_request.add(row)
                    self._cols_under_request.add(col)
                    self._start_timer()
                # set the child item, to prevent a row that has been requested
                # to be requested twice
                # dont do this any more since this causes a data changed signal
                # which causes more data to be requested again, and so on.
                #invalid_clone = invalid_item.clone()
                #root_item.setChild(row, col, invalid_clone)
            return invalid_item.data(role)

        if role == ObjectRole:
            return self.headerData(row, Qt.Vertical, role)

        return child_item.data(role)

    def flags(self, index):
        """The default implementation of `flags` implicitly creates a child item
        when there is None, and returns the default flags which are editable.
        This makes cells which have no associated item yet editable, which can
        result in data loss once they do have an associated item, but the editor
        is already created.
        """
        root_item = self.invisibleRootItem()
        child_item = root_item.child(index.row(), index.column())
        if child_item is None:
            return Qt.NoItemFlags
        return child_item.flags()

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
            self.logger.debug('set data index is invalid')
            return False
        if role == Qt.EditRole:
            column = index.column()
            # if the field is not editable, don't waste any time and get out of here
            field_attributes = variant_to_py(self.headerData(column, Qt.Horizontal, FieldAttributesRole))
            if field_attributes.get('editable', True) != True:
                self.logger.debug('set data called on not editable field : {}'.format(field_attributes))
                return
            row = index.row()
            obj = variant_to_py(self.headerData(row, Qt.Vertical, ObjectRole))
            if obj is None:
                logger.debug('set data called on row without object')
                return
            self.logger.debug('set data ({0},{1})'.format(row, column))
            self._update_requests.append((row, obj, column, value))
            # dont trigger the timer, since the item  model might be deleted
            # by the time the timout happens
            self.timeout_slot()
        return True

    def get_admin( self ):
        """Get the admin object associated with this model"""
        self.logger.debug('get_admin called')
        return self.admin


