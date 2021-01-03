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

""" Tableview """

import logging
import six

from sqlalchemy.ext.hybrid import hybrid_property

from camelot.admin.action.list_action import ListActionGuiContext
from camelot.core.utils import ugettext as _
from camelot.view.controls.view import AbstractView
from camelot.view.model_thread import object_thread
from ...core.qt import QtCore, QtGui, QtModel, QtWidgets, Qt, variant_to_py
from ..proxy.collection_proxy import CollectionProxy
from .actionsbox import ActionsBox
from .delegates.delegatemanager import DelegateManager

logger = logging.getLogger('camelot.view.controls.tableview')


class ColumnGroupsWidget(QtWidgets.QTabBar):
    """
    A tabbar the user can use to select a group of columns within an
    item view.

    :param table: a :class:`camelot.admin.table.Table` object, describing the
        column groups.
    :param table_widget: a :class:`QtWidgets.QTableView` widget of which
        columns will be hidden and shown depending on the selected tab.
    :param parent: a :class:`QtWidgets.QWidget`
    """

    def __init__(self, table, table_widget, parent=None):
        from camelot.admin.table import ColumnGroup
        super(ColumnGroupsWidget, self).__init__(parent)
        assert object_thread(self)
        self.setShape(QtWidgets.QTabBar.RoundedSouth)
        self.groups = dict()
        self.table_widget = table_widget
        column_index = 0
        tab_index = 0
        for column in table.columns:
            if isinstance(column, ColumnGroup):
                self.addTab(six.text_type(column.verbose_name))
                previous_column_index = column_index
                column_index = column_index + len(column.get_fields())
                self.groups[tab_index] = (previous_column_index,
                                          column_index)
                tab_index += 1
            else:
                column_index += 1
        self.currentChanged.connect(self._current_index_changed)

    @QtCore.qt_slot(QtCore.QModelIndex, int, int)
    def columns_changed(self, index, first_column, last_column):
        assert object_thread(self)
        self._current_index_changed(self.currentIndex())

    @QtCore.qt_slot()
    def model_reset(self):
        assert object_thread(self)
        self._current_index_changed(self.currentIndex())

    @QtCore.qt_slot(int)
    def _current_index_changed(self, current_index):
        assert object_thread(self)
        for tab_index, (first_column,
                        last_column) in six.iteritems(self.groups):
            for column_index in range(first_column, last_column):
                self.table_widget.setColumnHidden(column_index,
                                                  tab_index != current_index)


class TableWidget(QtWidgets.QTableView):
    """
    A widget displaying a table, to be used within a TableView.  But it does
    not rely on the model being Camelot specific, or a Collection Proxy.

    .. attribute:: margin

    margin, specified as a number of pixels, used to calculate the height of a
    row in the table, the minimum row height will allow for this number of
    pixels below and above the text.

    :param lines_per_row: the number of lines of text that should be viewable
        in a single row.
    """

    margin = 5
    keyboard_selection_signal = QtCore.qt_signal()

    def __init__(self, lines_per_row=1, parent=None):
        QtWidgets.QTableView.__init__(self, parent)
        logger.debug('create TableWidget')
        assert object_thread(self)
        self._columns_changed = dict()
        self.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.setEditTriggers(QtWidgets.QAbstractItemView.SelectedClicked |
                             QtWidgets.QAbstractItemView.DoubleClicked |
                             QtWidgets.QAbstractItemView.CurrentChanged)
        self.setSizePolicy(QtWidgets.QSizePolicy.Expanding,
                           QtWidgets.QSizePolicy.Expanding)
        try:
            self.horizontalHeader().setClickable(True)
        except AttributeError:
            self.horizontalHeader().setSectionsClickable(True)
        self._header_font_required = QtWidgets.QApplication.font()
        self._header_font_required.setBold(True)
        line_height = QtGui.QFontMetrics(QtWidgets.QApplication.font()
                                         ).lineSpacing()
        self._minimal_row_height = line_height * lines_per_row + 2*self.margin
        self.verticalHeader().setDefaultSectionSize(self._minimal_row_height)
        self.setHorizontalScrollMode(
            QtWidgets.QAbstractItemView.ScrollPerPixel)
        self.setVerticalScrollMode(QtWidgets.QAbstractItemView.ScrollPerPixel)
        self.horizontalHeader().sectionClicked.connect(
            self.horizontal_section_clicked)
        self.horizontalHeader().sectionResized.connect(
            self._save_section_width)
        self.verticalScrollBar().sliderPressed.connect(self._slider_pressed)
        self.horizontalScrollBar().sliderPressed.connect(self._slider_pressed)

    @QtCore.qt_slot()
    def selectAll(self):
        """
        Reimplement `QtWidgets.QAbstractItemView.selectAll` to add the
        option of selecting nothing.
        """
        selection_model = self.selectionModel()
        if selection_model is not None:
            if selection_model.hasSelection():
                selection_model.clear()
            else:
                super(TableWidget, self).selectAll()

    def timerEvent(self, event):
        """ On timer event, save changed column widths to the model """
        assert object_thread(self)
        for logical_index, new_width in six.iteritems(self._columns_changed):
            if self.horizontalHeader().isSectionHidden(logical_index):
                # don't save the width of a hidden section, since this will
                # result in setting the width to 0
                continue
            old_size = variant_to_py(self.model().headerData(logical_index,
                                                             Qt.Horizontal,
                                                             Qt.SizeHintRole))
            # when the size is different from the one from the model, the
            # user changed it
            if (old_size is not None) and (old_size.width() != new_width):
                new_size = QtCore.QSize(new_width, old_size.height())
                self.model().setHeaderData(logical_index,
                                           Qt.Horizontal,
                                           new_size,
                                           Qt.SizeHintRole)
        self._columns_changed = dict()
        super(TableWidget, self).timerEvent(event)

    @QtCore.qt_slot()
    def _slider_pressed(self):
        """
        Close the editor when scrolling starts, to prevent the table from
        jumping back to the open editor, or to prevent the open editor from
        being out of sight.
        """
        self.close_editor()

    @QtCore.qt_slot(int, int, int)
    def _save_section_width(self, logical_index, _old_size, new_width):
        # instead of storing the width immediately, a timer is started to store
        # the width when all event processing is done.  because at this time
        # we cannot yet determine if the section at logical_index is hidden
        # or not
        #
        # there is no need to start the timer, since this is done by the
        # QAbstractItemView itself for doing the layout, here we only store
        # which column needs to be saved.
        assert object_thread(self)
        self._columns_changed[logical_index] = new_width

    @QtCore.qt_slot(int)
    def horizontal_section_clicked(self, logical_index):
        """Update the sorting of the model and the header"""
        assert object_thread(self)
        header = self.horizontalHeader()
        order = Qt.AscendingOrder
        if not header.isSortIndicatorShown():
            header.setSortIndicatorShown(True)
        elif header.sortIndicatorSection() == logical_index:
            # apparently, the sort order on the header is already switched
            # when the section was clicked, so there is no need to reverse it
            order = header.sortIndicatorOrder()
        header.setSortIndicator(logical_index, order)
        self.model().sort(logical_index, order)

    def close_editor(self):
        """
        Close the active editor, this method is used to prevent assertion
        failures in QT when an editor is still open in the view for a cell
        that no longer exists in the model

        those assertion failures only exist in QT debug builds.
        """
        assert object_thread(self)
        current_index = self.currentIndex()
        if not current_index.isValid():
            return
        self.closePersistentEditor(current_index)

    def setModel(self, model):
        assert object_thread(self)
        #
        # An editor might be open that is no longer available for the new
        # model.  Not closing this editor, results in assertion failures
        # in qt, resulting in segfaults in the debug build.
        #
        self.close_editor()
        #
        # Editor, closed. it should be safe to change the model
        #
        QtWidgets.QTableView.setModel(self, model)
        model.setParent(self)
        # assign selection model to local variable to keep it alive during
        # method call, or PySide segfaults
        selection_model = self.selectionModel()
        selection_model.currentChanged.connect(self._current_changed)
        model.modelReset.connect(self.update_headers)
        self.update_headers()

    @QtCore.qt_slot()
    def update_headers(self):
        """
        Updating the header size seems to be no default Qt function, so, it's
        managed here
        """
        model = self.model()
        for i in range(model.columnCount()):
            size_hint = variant_to_py(model.headerData(i,
                                                       Qt.Horizontal,
                                                       Qt.SizeHintRole))
            if size_hint is not None:
                self.setColumnWidth(i, size_hint.width())
        # dont save these changes, since they are the defaults
        self._columns_changed = dict()

    @QtCore.qt_slot(QtCore.QModelIndex, QtCore.QModelIndex)
    def _current_changed(self, current, previous):
        """ This slot is called whenever the current cell is changed """
        editor = self.indexWidget(current)
        header_data = self.model().headerData
        # if there is an editor in the current cell, change the column and
        # row width to the size hint of the editor
        if editor is not None:
            column_size_hint = variant_to_py(header_data(current.column(),
                                                         Qt.Horizontal,
                                                         Qt.SizeHintRole))
            row_size_hint = variant_to_py(header_data(current.row(),
                                                      Qt.Vertical,
                                                      Qt.SizeHintRole))
            editor_size_hint = editor.sizeHint()
            self.setRowHeight(current.row(), max(row_size_hint.height(),
                                                 editor_size_hint.height()))
            self.setColumnWidth(current.column(),
                                max(column_size_hint.width(),
                                    editor_size_hint.width()))
        if current.row() != previous.row():
            if previous.row() >= 0:
                row_size_hint = variant_to_py(header_data(previous.row(),
                                                          Qt.Vertical,
                                                          Qt.SizeHintRole))
                self.setRowHeight(previous.row(), row_size_hint.height())
        if current.column() != previous.column():
            if previous.column() >= 0:
                column_size_hint = variant_to_py(header_data(previous.column(),
                                                             Qt.Horizontal,
                                                             Qt.SizeHintRole))
                self.setColumnWidth(previous.column(),
                                    column_size_hint.width())
        # whenever we change the size, sectionsResized is called, but these
        # changes should not be saved.
        self._columns_changed = dict()

    def keyPressEvent(self, e):
        assert object_thread(self)
        if self.hasFocus() and e.key() in (QtCore.Qt.Key_Enter,
                                           QtCore.Qt.Key_Return):
            self.keyboard_selection_signal.emit()
        else:
            super(TableWidget, self).keyPressEvent(e)


class AdminTableWidget(QtWidgets.QWidget):
    """
    A table widget that inspects the admin class and changes the behavior
    of the table as specified in the admin class
    """

    def __init__(self, admin, parent=None):
        super(AdminTableWidget, self).__init__(parent)
        assert object_thread(self)
        self._admin = admin
        table_widget = TableWidget(parent=self,
                                   lines_per_row=admin.lines_per_row)
        table_widget.setObjectName('table_widget')
        column_groups = ColumnGroupsWidget(admin.get_table(), table_widget)
        column_groups.setObjectName('column_groups')
        layout = QtWidgets.QVBoxLayout()
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(table_widget)
        layout.addWidget(column_groups)
        self.setLayout(layout)
        if admin.drop_action is not None:
            table_widget.setDragDropMode(QtWidgets.QAbstractItemView.DragDrop)
            table_widget.setDropIndicatorShown(True)

    def __getattr__(self, name):
        table_widget = self.findChild(QtWidgets.QWidget, 'table_widget')
        if table_widget is not None:
            return getattr(table_widget, name)

    def setModel(self, model):
        assert object_thread(self)
        table_widget = self.findChild(QtWidgets.QWidget, 'table_widget')
        column_groups = self.findChild(QtWidgets.QWidget, 'column_groups')
        if table_widget is not None:
            model.columnsInserted.connect(column_groups.columns_changed)
            model.columnsRemoved.connect(column_groups.columns_changed)
            model.layoutChanged.connect(column_groups.model_reset)
            model.modelReset.connect(column_groups.model_reset)
            table_widget.setModel(model)
            column_groups.model_reset()


class RowsWidget(QtWidgets.QLabel):
    """
    Widget that is part of the header widget, displaying the number of rows in
    the table view
    """

    def __init__(self, gui_context, parent=None):
        QtWidgets.QLabel.__init__(self, parent)
        assert object_thread(self)
        self.gui_context = gui_context
        self.setFont(self._number_of_rows_font)
        self.selected_count = 0
        self.set_item_view(gui_context.item_view)

    @hybrid_property
    def _number_of_rows_font(cls):
        return QtWidgets.QApplication.font()

    def set_item_view(self,item_view):
        model = item_view.model()
        model.layoutChanged.connect(self.update_rows)
        model.modelReset.connect(self.update_rows)
        model.rowsInserted.connect(self.update_rows)
        model.rowsRemoved.connect(self.update_rows)
        selection_model = item_view.selectionModel()
        selection_model.selectionChanged.connect(self.selection_changed)
        self.update_rows_from_model(model)

    # Using QtModel because QItemSelection resides in QtGui in Qt4 and in
    # QtCore in Qt5
    @QtCore.qt_slot(QtModel.QItemSelection, QtModel.QItemSelection)
    def selection_changed(self, selected, deselected):
        def count(selection):
            selection_count = 0
            for i in range(len(selection)):
                selection_range = selection[i]
                rows_range = (selection_range.top(), selection_range.bottom())
                selection_count += (rows_range[1] - rows_range[0]) + 1
            return selection_count
        self.selected_count += count(selected) - count(deselected)
        self.update_rows_from_model(self.gui_context.view.get_model())

    def update_rows_from_model(self, model):
        rows = model.rowCount()
        if self.selected_count == 0:
            self.setText(_('(%i rows)') % rows)
        else:
            self.setText(_('(%i rows, %i selected)') % (rows,
                                                        self.selected_count))

    @QtCore.qt_slot()
    def update_rows(self, *args):
        assert object_thread(self)
        model = self.sender()
        self.update_rows_from_model(model)


class HeaderWidget(QtWidgets.QWidget):
    """
    HeaderWidget for a tableview, containing the title, the search widget, and
    the number of rows in the table
    """

    rows_widget = RowsWidget

    def __init__(self, gui_context, parent):
        QtWidgets.QWidget.__init__(self, parent)
        assert object_thread(self)
        self.gui_context = gui_context
        layout = QtWidgets.QVBoxLayout()
        widget_layout = QtWidgets.QHBoxLayout()
        actions_toolbar = QtWidgets.QToolBar()
        actions_toolbar.setObjectName('actions_toolbar')
        actions_toolbar.setIconSize(QtCore.QSize(16, 16))
        widget_layout.addWidget(actions_toolbar)
        number_of_rows = self.rows_widget(gui_context, parent=self)
        number_of_rows.setObjectName('number_of_rows')
        widget_layout.addWidget(number_of_rows)
        layout.addLayout(widget_layout, 0)
        self.setLayout(layout)
        self.setSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Fixed)


class TableView(AbstractView):
    """
    :param gui_context: a :class:`camelot.admin.action.application_action.ApplicationActionGuiContext` object.
    :param admin: an :class:`camelot.admin.entity_admin.EntityAdmin` object
    :param proxy: a class implementing :class:`QtCore.QAbstractTableModel` that
      will be used as a model for the table view.
    :param parent: a :class:`QtWidgets.QWidget` object

    A generic tableview widget that puts together some other widgets. The
    behaviour of this class and the resulting interface can be tuned by
    specifying specific class attributes which define the underlying widgets
    used ::

    class MovieRentalTableView(TableView):
      title_format = 'Grand overview of recent movie rentals'

    The attributes that can be specified are :

    .. attribute:: header_widget

    The widget class to be used as a header in the table view::

    header_widget = HeaderWidget

    .. attribute:: table_widget

    The widget class used to display a table within the table view ::

    table_widget = TableWidget

    .. attribute:: title_format

    A string used to format the title of the view ::

    title_format = '%(verbose_name_plural)s'

    - emits the row_selected signal when a row has been selected
    """

    header_widget = HeaderWidget
    AdminTableWidget = AdminTableWidget

    def __init__(self,
                 gui_context,
                 admin,
                 parent=None):
        super(TableView, self).__init__(parent)
        assert object_thread(self)
        self.admin = admin
        self.application_gui_context = gui_context
        self.gui_context = gui_context
        widget_layout = QtWidgets.QVBoxLayout()
        widget_layout.setSpacing(0)
        widget_layout.setContentsMargins(0, 0, 0, 0)
        splitter = QtWidgets.QSplitter(self)
        splitter.setObjectName('splitter')
        widget_layout.addWidget(splitter)
        table_widget = QtWidgets.QWidget(self)
        # make sure the table itself takes expands to fill the available
        # width of the view
        size_policy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding,
                                            QtWidgets.QSizePolicy.Expanding)
        size_policy.setHorizontalStretch(1)
        table_widget.setSizePolicy(size_policy)
        filters_widget = QtWidgets.QWidget(self)
        self.table_layout = QtWidgets.QVBoxLayout()
        self.table_layout.setSpacing(0)
        self.table_layout.setContentsMargins(0, 0, 0, 0)
        self.table = None
        self.filters_layout = QtWidgets.QVBoxLayout()
        self.filters_layout.setSpacing(0)
        self.filters_layout.setContentsMargins(0, 0, 0, 0)
        self.actions = None
        table_widget.setLayout(self.table_layout)
        filters_widget.setLayout(self.filters_layout)
        splitter = self.findChild(QtWidgets.QWidget, 'splitter')
        splitter.addWidget(table_widget)
        splitter.addWidget(filters_widget)
        self.setLayout(widget_layout)
        self.widget_layout = widget_layout
        self.gui_context.admin = self.admin
        self.gui_context.view = self

    def close_view(self, accept):
        self.close_clicked_signal.emit()

    @QtCore.qt_slot(int)
    def sectionClicked(self, section):
        """emits a row_selected signal"""
        assert object_thread(self)
        #
        # close the table editor before opening a form or such
        #
        # Qt seems to crash in certain cases when the editor is open and the
        # underlying model is changed
        #
        if self.table:
            self.table.close_editor()
        self.admin.list_action.gui_run(self.gui_context)

    def get_admin(self):
        return self.admin

    def get_model(self):
        return self.table.model()

    def set_value(self, value):
        model = self.get_model()
        if model is not None:
            model.set_value(value)

    @QtCore.qt_slot(object)
    def set_admin(self, admin):
        """
        Switch to a different subclass, where admin is the admin object of the
        subclass
        """
        assert object_thread(self)
        logger.debug('set_admin called')
        self.admin = admin
        if self.table:
            self.table_layout.removeWidget(self.table)
            self.table.deleteLater()
            if self.table.model() is not None:
                self.table.model().deleteLater()
        splitter = self.findChild(QtWidgets.QWidget, 'splitter')
        self.table = self.AdminTableWidget(self.admin, splitter)
        self.table.setObjectName('AdminTableWidget')
        new_model = CollectionProxy(admin)
        self.table.setModel(new_model)
        self.table.verticalHeader().sectionClicked.connect(self.sectionClicked)
        self.table.keyboard_selection_signal.connect(
            self.on_keyboard_selection_signal)
        self.table_layout.insertWidget(1, self.table)
        self.gui_context = self.application_gui_context.copy(
            ListActionGuiContext)
        self.gui_context.view = self
        self.gui_context.admin = self.admin
        self.gui_context.item_view = self.table
        header = self.findChild(QtWidgets.QWidget, 'header_widget')
        if header is not None:
            header.deleteLater()
        header = self.header_widget(self.gui_context, self)
        header.setObjectName('header_widget')
        self.widget_layout.insertWidget(0, header)
        self.setFocusProxy(header)

    @QtCore.qt_slot()
    def on_keyboard_selection_signal(self):
        assert object_thread(self)
        self.sectionClicked(self.table.currentIndex().row())

    def closeEvent(self, event):
        """reimplements close event"""
        assert object_thread(self)
        logger.debug('tableview closed')
        event.accept()

    @QtCore.qt_slot()
    def refresh(self):
        """Refresh the whole view"""
        assert object_thread(self)
        model = self.get_model()
        if model is not None:
            model.refresh()

    def set_columns(self, columns):
        delegate = DelegateManager(columns, parent=self)
        table = self.table
        table.setItemDelegate(delegate)

    def set_filters(self, filters):
        logger.debug('setting filters for tableview')
        filters_widget = self.findChild(ActionsBox, 'filters')
        while True:
            item = self.filters_layout.takeAt(0)
            if item is None:
                break
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()
        if filters:
            filters_widget = ActionsBox(parent=self)
            filters_widget.setObjectName('filters')
            self.filters_layout.addWidget(filters_widget)
            for action in filters:
                action_widget = self.render_action(action, filters_widget)
                filters_widget.layout().addWidget(action_widget)
        self.filters_layout.addStretch(1)

    def set_list_actions(self, actions):
        """sets filters for the tableview"""
        assert object_thread(self)
        actions_widget = self.findChild(ActionsBox, 'actions')
        if actions:
            actions_widget = ActionsBox(parent=self)
            actions_widget.setObjectName('actions')
            for action in actions:
                actions_widget.layout().addWidget(
                    self.render_action(action, actions_widget)
                )
            self.filters_layout.addWidget(actions_widget)

    @QtCore.qt_slot( object, object )
    def set_toolbar_actions( self, toolbar_area, toolbar_actions ):
        """Set the toolbar for a specific area
        :param toolbar_area: the area on which to put the toolbar, from
            :class:`Qt.LeftToolBarArea` through :class:`Qt.BottomToolBarArea`
        :param toolbar_actions: a list of :class:`camelot.admin.action..base.Action` objects,
            as returned by the :meth:`camelot.admin.application_admin.ApplicationAdmin.get_toolbar_actions`
            method.
        """
        if toolbar_actions != None:
            toolbar = self.findChild(QtWidgets.QToolBar, 'actions_toolbar')
            assert toolbar
            for action in toolbar_actions:
                rendered = self.render_action(action, toolbar)
                # both QWidgets and QActions can be put in a toolbar
                if isinstance(rendered, QtWidgets.QWidget):
                    toolbar.addWidget(rendered)
                elif isinstance(rendered, QtWidgets.QAction):
                    toolbar.addAction( rendered )

    @QtCore.qt_slot(bool)
    def action_triggered(self, _checked = False):
        """Execute an action that was triggered somewhere in the main window,
        such as the toolbar or the main menu"""
        action_action = self.sender()
        action_action.action.gui_run(self.gui_context)

    @QtCore.qt_slot()
    def focusTable(self):
        assert object_thread(self)
        if self.table and self.table.model().rowCount() > 0:
            self.table.setFocus()
            self.table.selectRow(0)

