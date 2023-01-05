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
import json
import logging

logger = logging.getLogger(__name__)


from sqlalchemy.ext.hybrid import hybrid_property

from ...admin.action.base import GuiContext
from ...core.naming import initial_naming_context
from ...core.qt import Qt, QtCore, QtGui, QtWidgets, is_deleted
from ...core.item_model import (
    ObjectRole, PreviewRole,
    CompletionPrefixRole, ActionRoutesRole,
    ActionStatesRole, CompletionsRole,
    ActionModeRole, FocusPolicyRole,
    VisibleRole, NullableRole
)
from ..crud_action import (
    changeselection_name, created_name, completion_name, deleted_name,
    rowcount_name, rowdata_name, setdata_name, setcolumns_name, sort_name,
    update_name, runfieldaction_name
)
from camelot.view.qml_view import get_crud_signal_handler
from ..utils import get_settings
from ..qml_view import LiveRef
from .. import gui_naming_context
from camelot.view.model_thread import object_thread
from camelot.view.art import from_admin_icon
from camelot.view.action_runner import action_runner


invalid_data = None
invalid_item = QtGui.QStandardItem()
invalid_item.setFlags(Qt.ItemFlag.NoItemFlags)
invalid_item.setData(invalid_data, Qt.ItemDataRole.EditRole)
invalid_item.setData(invalid_data, PreviewRole)
invalid_item.setData(invalid_data, ObjectRole)
invalid_item.setData(invalid_data, CompletionsRole)
invalid_item.setData('[]', ActionRoutesRole)
invalid_item.setData('[]', ActionStatesRole)
invalid_item.setData(invalid_data, ActionModeRole)
invalid_item.setData(Qt.FocusPolicy.NoFocus, FocusPolicyRole)
invalid_item.setData(True, VisibleRole)
invalid_item.setData(True, NullableRole)

initial_delay = 50
maximum_delay = 1000


# CollectionProxy subclasses GuiContext to be able to behave
# as a gui_context when running field actions.  To be removed later on.

class CollectionProxy(QtGui.QStandardItemModel, GuiContext):
    """The :class:`CollectionProxy` contains a limited copy of the data in the
    actual collection, usable for fast visualisation in a 
    :class:`QtWidgets.QTableView`  

    The behavior of the :class:`QtWidgets.QTableView`, such as what happens when the
    user clicks on a row is defined in the :class:`ObjectAdmin` class.

    :attr max_row_count: the maximum number of rows that can be loaded in the
        model.  each row, even when not yet displayed will consume a certain
        amount of memory, this maximum puts an upper limit on that.
    """

    action_state_changed_cpp_signal = QtCore.qt_signal('QStringList', QtCore.QByteArray) # used in C++

    max_row_count = 10000000 # display maxium 10M rows

    def __init__(self, admin_route):
        """
        :param admin_route: the route to the view to display
        """
        super(CollectionProxy, self).__init__()
        assert object_thread(self)
        assert isinstance(admin_route, tuple)
        assert len(admin_route)
        # TODO: replace with passed entity_name as part of future changes.
        admin_name = admin_route[-2]
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
        self._gui_context = gui_naming_context.bind(
            ('transient', str(id(self))), self
        )
        self._model_context = None
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

        self.__time = QtCore.QDateTime.currentDateTime()

        self._columns = []

        self.__crud_request_counter = itertools.count()
        self.__crud_requests = collections.deque()

        self._reset()
        crud_signal_handler = get_crud_signal_handler()
        crud_signal_handler.connectSignals( self )
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
                self._append_request(rowcount_name, None)
                root_item.setEnabled(True)
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
        role_names[Qt.ItemDataRole.BackgroundRole] = b'background'
        role_names[Qt.ItemDataRole.TextAlignmentRole] = b'text_alignment'
        role_names[ActionModeRole] = b'action_mode'
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
                self._append_request(setdata_name, [u for u in self._update_requests])
                self._update_requests = list()
            if self._rows_under_request:
                self._append_request(
                    rowdata_name,
                    {
                        # take a copy, since the collection might be cleared
                        # before it is processed
                        "rows": list(self._rows_under_request),
                        "columns": list(self._cols_under_request),
                    }
                )
                self._rows_under_request.clear()
                self._cols_under_request.clear()
            # stop the timer after adding the requests, otherwise the timer
            # will be trigered again
            timer.stop()
            # only slow down if the timout actually caused requests and
            # requests are arriving at the speed of the interval
            current = QtCore.QDateTime.currentDateTime()
            elapsed = self.__time.msecsTo(current)
            self.__time = current
            if len(self.__crud_requests) and (elapsed < (timer.interval() + initial_delay)):
                # convert interval to int in case a long is returned
                timer.setInterval(min(maximum_delay, int(timer.interval()) * 2))
            while len(self.__crud_requests):
                model_context, request_id, request, mode = self.__crud_requests.popleft() # <- too soon
                self.logger.debug('post request {0} {1} : {2}'.format(request_id, request, mode))
                action_runner.run_action(
                    request, self._gui_context,
                    model_context.property('name'), mode
                )

    def _start_timer(self):
        """
        Start the timer if it is not yet active.
        """
        timer = self.findChild(QtCore.QTimer, 'timer')
        if (timer is not None) and (not timer.isActive()):
            elapsed = self.__time.msecsTo(QtCore.QDateTime.currentDateTime())
            if elapsed > (timer.interval() + (2*initial_delay)):
                # reset the interval after enough time has passed
                timer.setInterval(initial_delay)
            timer.start()

    def _last_request(self):
        """
        :return: the last crud request issued, or `None` if the queue is empty
        """
        if len(self.__crud_requests):
            return self.__crud_requests[-1][-1]

    def _append_request(self, request, mode):
        """
        Always use this method to add CRUD requests to the queue, since it
        will make sure :
        - no request is added to the queue while handling the
          feedback from a request.
        - the timer for handling the requests is started
        - the request is associated with the current model context
        """
        request_id = next(self.__crud_request_counter)
        self.logger.debug('append request {0} {1} : {2}'.format(request_id, request, mode))
        self.__crud_requests.append((self._model_context, request_id, request, mode))
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

    def get_progress_dialog(self):
        pass

    def get_window(self):
        parent = QtCore.QObject.parent(self)
        if parent is not None:
            return parent.window()

    def copy(self, base_class=None):
        return super().copy(
            base_class=base_class or GuiContext
        )

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
        root_item.setFlags(Qt.ItemFlag.NoItemFlags)
        root_item.setEnabled(row_count is not None)
        self.setRowCount(min(row_count or 0, self.max_row_count))
        self.logger.debug('_reset end')

    def set_value(self, value):
        """
        :param value: The name of the model context to execute the crud
            actions against.
        """
        self.logger.debug('set_value called')
        self._model_context = None
        self._reset()
        if value is not None:
            self._model_context = LiveRef(list(value))
            # the columns might be set before the value, but they might be running
            # in the model thread for a different model context as well, so
            # resubmit the set columns task for this model context
            columns = [c['name'] if isinstance(c, dict) else c for c in self._columns]
            self._append_request(setcolumns_name, columns)
        self.layoutChanged.emit()
    
    def get_value(self):
        if self._model_context is not None:
            return tuple(self._model_context.property('name'))

    @QtCore.qt_slot(list)
    def objectsUpdated(self, objects):
        """Handles the entity signal, indicating that the model is out of
        date
        """
        assert object_thread(self)
        if self._model_context is not None:
            self.logger.debug(
                'received objects updated: {}'.format(objects)
            )
            self._append_request(update_name, {'objects': LiveRef(objects)})
            self.timeout_slot()

    @QtCore.qt_slot(list)
    def objectsDeleted(self, objects):
        """Handles the entity signal, indicating that the model is out of
        date"""
        assert object_thread( self )
        if self._model_context is not None:
            self.logger.debug(
                #'received {0} objects deleted'.format(len(objects))
                'received objects deleted: {}'.format(objects)
                )
            self._append_request(deleted_name, {
                'objects': LiveRef(objects),
                'rows': super(CollectionProxy, self).rowCount()
            })
            #self.timeout_slot()

    @QtCore.qt_slot(list)
    def objectsCreated(self, objects):
        """Handles the entity signal, indicating that the model is out of
        date"""
        assert object_thread( self )
        if self._model_context is not None:
            self.logger.debug(
                'received objects created: {}'.format(objects)
                #'received {0} objects created'.format(len(objects))
            )
            self._append_request(created_name, {'objects': LiveRef(objects)})
            self.timeout_slot()

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
            self._append_request(setcolumns_name, self._columns)

    # decorate method as a slot, to make it accessible in QML
    @QtCore.qt_slot(int, Qt.Orientation, QtCore.QVariant, int)
    def setHeaderData(self, section, orientation, value, role):
        self.logger.debug('setHeaderData called')
        assert object_thread( self )
        if orientation == Qt.Orientation.Horizontal and role == Qt.ItemDataRole.SizeHintRole:
            item = self.horizontalHeaderItem(section)
            if item is not None:
                item.setData(value.width(), role)
                field_name = item.data(Qt.ItemDataRole.UserRole)
                width = value.width()
                self.settings.beginGroup('column_width')
                self.settings.beginGroup('0')
                self.settings.setValue(field_name, width)
                self.settings.endGroup()
                self.settings.endGroup()
        return super(CollectionProxy, self).setHeaderData(section, orientation, value, role)
    
    def headerData( self, section, orientation, role ):
        """In case the columns have not been set yet, don't even try to get
        information out of them
        """
        assert object_thread( self )
        if (orientation == Qt.Orientation.Vertical) and (section >= 0):
            if role == Qt.ItemDataRole.SizeHintRole:
                #
                # sizehint role is requested, for every row, so we have to
                # return a fixed value
                #
                return self.vertical_header_size
            item = self.verticalHeaderItem(section)
            if item is None:
                if section not in self._rows_under_request:
                    self._rows_under_request.add(section)
                    self._start_timer()
                return invalid_data
            if role == Qt.ItemDataRole.DecorationRole:
                icon = item.data(role)
                if icon is not None:
                    return from_admin_icon(icon).getQPixmap()
            else:
                return item.data(role)

        return super(CollectionProxy, self).headerData(section, orientation, role)

    # decorate method as a slot, to make it accessible in QML
    @QtCore.qt_slot(int, int)
    def sort(self, column, order=Qt.SortOrder.AscendingOrder):
        """reimplementation of the :class:`QtGui.QAbstractItemModel` its sort function"""
        self.logger.debug('sort called')
        assert object_thread( self )
        self._append_request(sort_name, (column, order))

    def data(self, index, role = Qt.ItemDataRole.DisplayRole):
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
        if role == Qt.ItemDataRole.DisplayRole:
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
            return self.headerData(row, Qt.Orientation.Vertical, role)

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
            return Qt.ItemFlag.NoItemFlags
        return child_item.flags()

    def setData( self, index, value, role = Qt.ItemDataRole.EditRole ):
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
        if role == Qt.ItemDataRole.EditRole:
            column = index.column()
            # if the field is not editable, don't waste any time and get out of here
            if not (index.flags() | Qt.ItemFlag.ItemIsEditable):
                self.logger.debug('set data called on not editable field')
                return False
            row = index.row()
            obj_id = self.headerData(row, Qt.Orientation.Vertical, ObjectRole)
            if obj_id is None:
                logger.debug('set data called on row without object')
                return False
            self.logger.debug('set data ({0},{1})'.format(row, column))
            if not isinstance(value, (list, tuple)):
                # the value is not a name, bind it
                value = initial_naming_context._bind_object(value)
            self._update_requests.append((row, obj_id, column, value))
            # dont trigger the timer, since the item  model might be deleted
            # by the time the timout happens
            self.timeout_slot()
        elif role == CompletionPrefixRole:
            self._append_request(
                completion_name, {'row': index.row(), 'column': index.column(), 'prefix': value}
            )
        elif role == ActionModeRole:
            value = json.loads(value)
            row = index.row()
            obj_id = self.headerData(row, Qt.Orientation.Vertical, ObjectRole)
            self._append_request(
                runfieldaction_name, {
                    'row': row,
                    'column': index.column(),
                    'object': obj_id,
                    'action_route': value[0],
                    'action_mode': value[1],
                }
            )
        return True

    def get_admin( self ):
        """Get the admin object associated with this model"""
        self.logger.debug('get_admin called')
        return initial_naming_context.resolve(self.admin_route)

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

        # as long as no value is set, there is no selection
        if self.get_value() is None:
            return

        current_row, current_column, row_ranges = -1, None, []

        if selection_model is not None:
            if current_index.isValid():
                current_row = current_index.row()
                current_column = current_index.column()
            if selection_model is not None:
                selection = selection_model.selection()
                for i in range( len( selection ) ):
                    selection_range = selection[i]
                    rows_range = (selection_range.top(), selection_range.bottom())
                    row_ranges.extend(rows_range)
        else:
            if current_index >= 0:
                current_row = current_index
                row_ranges.extend((current_row, current_row))

        self.change_selection_v2(row_ranges, current_row, current_column)

    @QtCore.qt_slot(list, int, int)
    def change_selection_v2(self, row_ranges, current_row, current_column):
        self.logger.debug('change_selection_v2 called')

        if current_row < 0:
            current_row = None
            current_row_id = None
        else:
            current_row_id = self.headerData(current_row, Qt.Orientation.Vertical, ObjectRole)


        current_field_name = None
        if current_column is not None:
            current_field_name = self.headerData(
                current_column, Qt.Orientation.Horizontal, Qt.ItemDataRole.UserRole
            )
        assert len(row_ranges) % 2 == 0
        selected_rows = []
        selected_rows_ids = []
        for i in range(len(row_ranges) // 2):
            begin_row = row_ranges[2 * i]
            end_row = row_ranges[2 * i + 1]
            selected_rows.append(( begin_row, end_row))
            selected_rows_ids.append((
                self.headerData(begin_row, Qt.Orientation.Vertical, ObjectRole),
                self.headerData(end_row, Qt.Orientation.Vertical, ObjectRole)
            ))

        request = changeselection_name
        self._append_request(request, {
            'action_routes': self._action_routes,
            'current_row': current_row,
            'current_row_id': current_row_id,
            'current_column': current_column,
            'selected_rows': selected_rows,
            'selected_rows_ids': selected_rows_ids,
            'current_field_name': current_field_name,
        })
