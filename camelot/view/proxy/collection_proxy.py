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

logger = logging.getLogger(__name__)


from sqlalchemy.ext.hybrid import hybrid_property

from ...admin.action.base import State
from ...admin.action.list_action import ListActionModelContext
from ...admin.action.form_action import FormActionModelContext
from ...admin.admin_route import AdminRoute
from ...core.qt import (Qt, QtCore, QtGui, QtWidgets, is_deleted,
                        py_to_variant, variant_to_py)
from ...core.item_model import (
    ObjectRole, FieldAttributesRole, PreviewRole, 
    AbstractModelProxy, CompletionPrefixRole, ActionRoutesRole,
    ActionStatesRole, ProxyRegistry, ProxyDict, CompletionsRole
)
from ..crud_action import ChangeSelection, Created, Completion, Deleted, Filter, RowCount, RowData, SetData, SetColumns, Sort, Update
from ..crud_signals import CrudSignalHandler
from ..item_model.cache import ValueCache
from ..utils import get_settings
from camelot.view.model_thread import object_thread
from camelot.view.art import from_admin_icon
from camelot.view.action_runner import ActionRunner


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
invalid_item.setData(invalid_data, CompletionsRole)
invalid_item.setData('[]', ActionRoutesRole)
invalid_item.setData('[]', ActionStatesRole)

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

                 
class CollectionProxy(QtGui.QStandardItemModel):
    """The :class:`CollectionProxy` contains a limited copy of the data in the
    actual collection, usable for fast visualisation in a 
    :class:`QtWidgets.QTableView`  

    The behavior of the :class:`QtWidgets.QTableView`, such as what happens when the
    user clicks on a row is defined in the :class:`ObjectAdmin` class.

    :attr max_row_count: the maximum number of rows that can be loaded in the
        model.  each row, even when not yet displayed will consume a certain
        amount of memory, this maximum puts an upper limit on that.
    """

    action_state_changed_signal = QtCore.qt_signal(tuple, State)

    max_row_count = 10000000 # display maxium 10M rows

    def __init__(self, admin_route, max_number_of_rows=10):
        """
        :param admin_route: the route to the view to display
        """
        super(CollectionProxy, self).__init__()
        assert object_thread(self)
        assert isinstance(max_number_of_rows, int)
        assert isinstance(admin_route, tuple)
        assert len(admin_route)
        from camelot.view.model_thread import get_model_thread
        admin_name = admin_route[-1]
        self.logger = logger.getChild('{0}.{1}'.format(id(self), admin_name))
        self.logger.debug('initialize proxy for %s' % (admin_name))
        self.admin_route = admin_route
        self.settings = get_settings(admin_name)
        self._horizontal_header_height = QtGui.QFontMetrics( self._header_font_required ).height() + 10
        self._header_font_metrics = QtGui.QFontMetrics( self._header_font )
        vertical_header_font_height = QtGui.QFontMetrics( self._header_font ).height()
        self._vertical_header_height = vertical_header_font_height + 10
        self.vertical_header_size =  QtCore.QSize(
            16 + 10, self._vertical_header_height
        )
        self._max_number_of_rows = max_number_of_rows
        self._mode_name = None
        self._model_context = None
        self._model_thread = get_model_thread()
        self._action_routes = []
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

    def roleNames(self):
        role_names = super().roleNames()
        role_names[ActionRoutesRole] = b'action_routes'
        role_names[ActionStatesRole] = b'action_states'
        role_names[Qt.BackgroundRole] = b'background'
        role_names[Qt.TextAlignmentRole] = b'text_alignment'
        return role_names
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
        if is_deleted(self):
            return
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
                runner = ActionRunner( request.model_run, self)
                runner.exec_()


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
        request_id = next(self.__crud_request_counter)
        self.logger.debug('append request {0} {1}'.format(request_id, request))
        self.__crud_requests.append((self._model_context, request_id, request))
        self._start_timer()

    #
    # end of timer functions
    #


    @QtCore.qt_slot(int)
    def _refresh_content(self, rows ):
        assert object_thread( self )
        assert isinstance(rows, int)
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
    # Methods to behave like a GuiContext.
    def create_model_context(self):
        return self._model_context
    
    def get_progress_dialog(self):
        pass
    
    @property
    def mode_name(self):
        return self._mode_name
    # End of methods to behave like a GuiContext. 
    
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
        root_item.setEnabled(row_count is not None)
        self.setRowCount(min(row_count or 0, self.max_row_count))
        self.logger.debug('_reset end')

    def set_value(self, value):
        """
        :param value: The route containing the proxy id of te collection of objects to display.
                      This route will contain only 1 integer which is a valid id for the
                      :class:`camelot.core.item_model.ProxyRegistry` (e.g. ['123']).
                      This is also the return type of ProxyRegistry.register().
        """
        self.logger.debug('set_value called')
        model_context = RowModelContext()
        model_context.admin = AdminRoute.admin_for(self.admin_route)
        model_context.proxy = ProxyRegistry.pop(value)
        assert isinstance(model_context.proxy, AbstractModelProxy)
        # todo : remove the concept of a validator
        model_context.validator = model_context.admin.get_validator()
        self._model_context = model_context
        #self._filters = dict()
        self._reset()
        # filters might be applied before the value is set
        for list_filter, value in self._filters.items():
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
        if (sender != self) and (self._model_context is not None):
            self.logger.debug(
                'received {0} objects updated'.format(len(objects))
            )
            self._append_request(Update(objects))

    @QtCore.qt_slot(object, tuple)
    def objects_deleted(self, sender, objects):
        """Handles the entity signal, indicating that the model is out of
        date"""
        assert object_thread( self )
        if (sender != self) and (self._model_context is not None):
            self.logger.debug(
                'received {0} objects deleted'.format(len(objects))
                )
            self._append_request(Deleted(objects, super(CollectionProxy, self).rowCount()))

    @QtCore.qt_slot(object, tuple)
    def objects_created(self, sender, objects):
        """Handles the entity signal, indicating that the model is out of
        date"""
        assert object_thread( self )
        if (sender != self) and (self._model_context is not None):
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

    # decorate method as a slot, to make it accessible in QML
    @QtCore.qt_slot(int, int, QtCore.QVariant, int)
    def setHeaderData(self, section, orientation, value, role):
        self.logger.debug('setHeaderData called')
        assert object_thread( self )
        if orientation == Qt.Horizontal and role == Qt.SizeHintRole:
            item = self.verticalHeaderItem(section)
            if item is not None:
                item.setData(value.width(), role)
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
                    return py_to_variant(from_admin_icon(icon).getQPixmap())
            else:
                return item.data(role)

        return super(CollectionProxy, self).headerData(section, orientation, role)

    # decorate method as a slot, to make it accessible in QML
    @QtCore.qt_slot(int, int)
    @QtCore.qt_slot(int, int)
    def sort(self, column, order=Qt.AscendingOrder):
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
            return invalid_item.data(role)

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
                return False
            row = index.row()
            obj = variant_to_py(self.headerData(row, Qt.Vertical, ObjectRole))
            if obj is None:
                logger.debug('set data called on row without object')
                return False
            self.logger.debug('set data ({0},{1})'.format(row, column))
            self._update_requests.append((row, obj, column, value))
            # dont trigger the timer, since the item  model might be deleted
            # by the time the timout happens
            self.timeout_slot()
        elif role == CompletionPrefixRole:
            self._append_request(Completion(index.row(), index.column(), value))
        return True

    def get_admin( self ):
        """Get the admin object associated with this model"""
        self.logger.debug('get_admin called')
        return AdminRoute.admin_for(self.admin_route)

    def add_action_route(self, action_route):
        """Add the action route for an action that needs it's state to be updated
        when the selection changed. See change_selection below

        :param action_route: The action route.
        """
        self._action_routes.append(action_route)

    @QtCore.qt_slot(QtCore.QItemSelectionModel, QtCore.QModelIndex)
    def change_selection(self, selection_model, current_index):
        """Determine the new state of actions and emit a action_state_changed_signal
        for each action that was added using add_action_route.
        """
        self.logger.debug('change_selection called')

        if selection_model is not None:
            # Create model context based on selection
            # model_conext.field_attributes required???
            model_context = ListActionModelContext()
            model_context.proxy = self.get_value()
            model_context.admin = self.get_admin()
            if current_index.isValid():
                model_context.current_row = current_index.row()
                model_context.current_column = current_index.column()
            model_context.collection_count = self.rowCount()
            if model_context.current_column is not None:
                model_context.current_field_name = variant_to_py(
                    self.headerData(
                        model_context.current_column, Qt.Horizontal, Qt.UserRole
                    )
                )
            if selection_model is not None:
                selection = selection_model.selection()
                for i in range( len( selection ) ):
                    selection_range = selection[i]
                    rows_range = ( selection_range.top(), selection_range.bottom() )
                    model_context.selected_rows.append( rows_range )
                    model_context.selection_count += ( rows_range[1] - rows_range[0] ) + 1
        else:
            model_context = FormActionModelContext()
            model_context.proxy = self.get_value()
            model_context.admin = self.get_admin()
            if current_index >= 0:
                model_context.current_row = current_index
                model_context.selection_count = 1

        request = ChangeSelection(self._action_routes, model_context)
        self._append_request(request)
