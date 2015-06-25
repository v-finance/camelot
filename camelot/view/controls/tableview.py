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

""" Tableview """

import logging
import six

from sqlalchemy.ext.hybrid import hybrid_property

from camelot.admin.action.list_action import ListActionGuiContext, ChangeAdmin
from camelot.core.utils import ugettext as _
from camelot.view.proxy.queryproxy import QueryTableProxy
from camelot.view.controls.view import AbstractView
from camelot.view.controls.user_translatable_label import UserTranslatableLabel
from camelot.view.model_thread import post
from camelot.view.model_thread import object_thread
from camelot.view import register
from ...core.qt import QtCore, QtGui, QtWidgets, Qt, variant_to_py
from .actionsbox import ActionsBox
from .delegates.delegatemanager import DelegateManager
from .inheritance import SubclassTree
from .search import SimpleSearchControl

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
        self.setSizePolicy(QtGui.QSizePolicy.Expanding,
                           QtGui.QSizePolicy.Expanding)
        self.horizontalHeader().setClickable(True)
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
        register.register(model, self)
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
        self.gui_context.view.model_changed.connect(self.model_changed)

    @hybrid_property
    def _number_of_rows_font(cls):
        return QtWidgets.QApplication.font()

    @QtCore.qt_slot(QtCore.QAbstractItemModel, AdminTableWidget)
    def model_changed(self, model, table):
        model.layoutChanged.connect(self.update_rows)
        model.modelReset.connect(self.update_rows)
        model.rowsInserted.connect(self.update_rows)
        model.rowsRemoved.connect(self.update_rows)
        selection_model = table.selectionModel()
        selection_model.selectionChanged.connect(self.selection_changed)
        self.update_rows_from_model(model)

    @QtCore.qt_slot(QtGui.QItemSelection, QtGui.QItemSelection)
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

    search_widget = SimpleSearchControl
    rows_widget = RowsWidget

    filters_changed_signal = QtCore.qt_signal()

    def __init__(self, gui_context, parent):
        QtWidgets.QWidget.__init__(self, parent)
        assert object_thread(self)
        self.gui_context = gui_context
        layout = QtWidgets.QVBoxLayout()
        widget_layout = QtWidgets.QHBoxLayout()
        search = self.search_widget(self)
        self.setFocusProxy(search)
        search.expand_search_options_signal.connect(
            self.expand_search_options)
        title = UserTranslatableLabel(
            self.gui_context.admin.get_verbose_name_plural(), self)
        title.setFont(self._title_font)
        widget_layout.addWidget(title)
        widget_layout.addWidget(search)
        number_of_rows = self.rows_widget(gui_context, parent=self)
        number_of_rows.setObjectName('number_of_rows')
        widget_layout.addWidget(number_of_rows)
        layout.addLayout(widget_layout, 0)
        self._expanded_filters_created = False
        self._expanded_search = QtWidgets.QWidget()
        self._expanded_search.hide()
        layout.addWidget(self._expanded_search, 1)
        self.setLayout(layout)
        self.setSizePolicy(QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Fixed)
        self.search = search

    @hybrid_property
    def _title_font(cls):
        font = QtWidgets.QApplication.font()
        font.setBold(True)
        return font

    def _fill_expanded_search_options(self, filters):
        """
        Given the columns in the table view, present the user with more options
        to filter rows in the table
        :param columns: a list of tuples with field names and attributes
        """
        assert object_thread(self)
        from camelot.view.flowlayout import FlowLayout
        layout = FlowLayout()
        layout.setSpacing(2)
        layout.setContentsMargins(0, 0, 0, 0)
        for filter_ in filters:
            widget = filter_.render(self.gui_context, self)
            layout.addWidget(widget)
        self._expanded_search.setLayout(layout)
        self._expanded_filters_created = True

    def _filter_changed(self):
        assert object_thread(self)
        self.filters_changed_signal.emit()

    @QtCore.qt_slot()
    def expand_search_options(self):
        assert object_thread(self)
        if self._expanded_search.isHidden():
            if not self._expanded_filters_created:
                post(self.gui_context.admin.get_expanded_search_filters,
                     self._fill_expanded_search_options)
            self._expanded_search.show()
        else:
            self._expanded_search.hide()


class TableView(AbstractView):
    """
    :param gui_context: a :class:`camelot.admin.action.application_action.ApplicationActionGuiContext` object.
    :param admin: an :class:`camelot.admin.entity_admin.EntityAdmin` object
    :param search_text: a predefined search text to put in the search widget
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

    model_changed = QtCore.qt_signal(QtCore.QAbstractItemModel,
                                     AdminTableWidget)

    def __init__(self,
                 gui_context,
                 admin,
                 search_text=None,
                 proxy=QueryTableProxy,
                 parent=None):
        super(TableView, self).__init__(parent)
        assert object_thread(self)
        self.admin = admin
        self.search_text = search_text
        self.application_gui_context = gui_context
        self.gui_context = gui_context
        self.proxy = proxy
        widget_layout = QtWidgets.QVBoxLayout()
        widget_layout.setSpacing(0)
        widget_layout.setContentsMargins(0, 0, 0, 0)
        splitter = QtGui.QSplitter(self)
        splitter.setObjectName('splitter')
        widget_layout.addWidget(splitter)
        table_widget = QtWidgets.QWidget(self)
        # make sure the table itself takes expands to fill the available
        # width of the view
        size_policy = QtGui.QSizePolicy(QtGui.QSizePolicy.Expanding,
                                        QtGui.QSizePolicy.Expanding)
        size_policy.setHorizontalStretch(1)
        table_widget.setSizePolicy(size_policy)
        filters_widget = QtWidgets.QWidget(self)
        self.table_layout = QtWidgets.QVBoxLayout()
        self.table_layout.setSpacing(0)
        self.table_layout.setContentsMargins(0, 0, 0, 0)
        self.table = None
        self.header = None
        self.filters_layout = QtWidgets.QVBoxLayout()
        self.filters_layout.setSpacing(0)
        self.filters_layout.setContentsMargins(0, 0, 0, 0)
        self.actions = None
        table_widget.setLayout(self.table_layout)
        filters_widget.setLayout(self.filters_layout)
        splitter = self.findChild(QtWidgets.QWidget, 'splitter')
        class_tree = SubclassTree(self.admin)
        class_tree.setObjectName('class_tree')
        class_tree.subclass_clicked_signal.connect(self.change_admin)
        splitter.addWidget(class_tree)
        splitter.addWidget(table_widget)
        splitter.addWidget(filters_widget)
        self.setLayout(widget_layout)
        self.widget_layout = widget_layout
        self.search_filter = lambda q: q
        shortcut = QtGui.QShortcut(QtGui.QKeySequence(QtGui.QKeySequence.Find),
                                   self)
        shortcut.activated.connect(self.activate_search)

        self.gui_context.admin = self.admin
        self.gui_context.view = self
        self.header = self.header_widget(self.gui_context, self)
        self.widget_layout.insertWidget(0, self.header)
        self.header.search.search_signal.connect(self.startSearch)
        self.header.search.cancel_signal.connect(self.cancelSearch)
        self.header.search.on_arrow_down_signal.connect(self.focusTable)
        self.setFocusProxy(self.header)
        if self.search_text:
            self.header.search.search(self.search_text)

    @QtCore.qt_slot()
    def activate_search(self):
        assert object_thread(self)
        self.header.search.setFocus(QtCore.Qt.ShortcutFocusReason)

    @QtCore.qt_slot(object)
    def set_subclass_tree(self, subclasses):
        assert object_thread(self)
        class_tree = self.findChild(QtWidgets.QWidget, 'class_tree')
        if len(subclasses) > 0:
            class_tree.show()
            class_tree.set_subclasses(subclasses)
        else:
            class_tree.hide()

    @QtCore.qt_slot(object)
    def change_admin(self, new_admin):
        action = ChangeAdmin(new_admin)
        action.gui_run(self.gui_context)

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
            self.rebuild_query()

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
        new_model = self.proxy(admin)
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
        self.model_changed.emit(new_model, self.table)

    @QtCore.qt_slot()
    def on_keyboard_selection_signal(self):
        assert object_thread(self)
        self.sectionClicked(self.table.currentIndex().row())

    def closeEvent(self, event):
        """reimplements close event"""
        assert object_thread(self)
        logger.debug('tableview closed')
        event.accept()

    @QtCore.qt_slot(object)
    def _set_query(self, query):
        assert object_thread(self)
        if isinstance(self.table.model(), QueryTableProxy):
            # apply the filters on the query, to activate the default filter
            filters_widget = self.findChild(ActionsBox, 'filters')
            if filters_widget is not None:
                for filter_widget in filters_widget.get_action_widgets():
                    filter_widget.run_action()
            self.table.model().set_value(query)
        self.table.clearSelection()

    @QtCore.qt_slot()
    def refresh(self):
        """Refresh the whole view"""
        assert object_thread(self)
        model = self.get_model()
        if model is not None:
            model.refresh()

    @QtCore.qt_slot()
    def rebuild_query(self):
        """resets the table model query"""

        # table can be None during view initialization
        if self.table is None:
            return

        if not isinstance(self.table.model(), QueryTableProxy):
            return

        def rebuild_query():
            query = self.admin.get_query()
            if self.search_filter:
                query = self.search_filter(query)
            return query

        post(rebuild_query, self._set_query)

    @QtCore.qt_slot(str)
    def startSearch(self, text):
        """rebuilds query based on filtering text"""
        assert object_thread(self)
        from camelot.view.search import create_entity_search_query_decorator
        logger.debug('search %s' % text)
        self.search_filter = create_entity_search_query_decorator(
            self.admin, six.text_type(text))
        self.rebuild_query()

    @QtCore.qt_slot()
    def cancelSearch(self):
        """resets search filtering to default"""
        assert object_thread(self)
        logger.debug('cancel search')
        self.search_filter = lambda q: q
        self.rebuild_query()

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
            filters_widget = ActionsBox(gui_context=self.gui_context,
                                        parent=self)
            filters_widget.setObjectName('filters')
            self.filters_layout.addWidget(filters_widget)
            filters_widget.set_actions(filters)
        self.filters_layout.addStretch(1)

    def set_list_actions(self, actions):
        """sets filters for the tableview"""
        assert object_thread(self)
        actions_widget = self.findChild(ActionsBox, 'actions')
        if actions:
            actions_widget = ActionsBox(parent=self,
                                        gui_context=self.gui_context)
            actions_widget.setObjectName('actions')
            actions_widget.set_actions(actions)
            self.filters_layout.addWidget(actions_widget)

    @QtCore.qt_slot()
    def focusTable(self):
        assert object_thread(self)
        if self.table and self.table.model().rowCount() > 0:
            self.table.setFocus()
            self.table.selectRow(0)
