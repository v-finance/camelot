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

from ...core.qt import QtCore, QtGui, QtWidgets, Qt


logger = logging.getLogger('camelot.view.controls.tableview')


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
        self._columns_changed = dict()
        self.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectionBehavior.SelectRows)
        self.setEditTriggers(QtWidgets.QAbstractItemView.EditTrigger.SelectedClicked |
                             QtWidgets.QAbstractItemView.EditTrigger.DoubleClicked |
                             QtWidgets.QAbstractItemView.EditTrigger.CurrentChanged)
        self.setSizePolicy(QtWidgets.QSizePolicy.Policy.Expanding,
                           QtWidgets.QSizePolicy.Policy.Expanding)
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
            QtWidgets.QAbstractItemView.ScrollMode.ScrollPerPixel)
        self.setVerticalScrollMode(QtWidgets.QAbstractItemView.ScrollMode.ScrollPerPixel)
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
        for logical_index, new_width in self._columns_changed.items():
            if self.horizontalHeader().isSectionHidden(logical_index):
                # don't save the width of a hidden section, since this will
                # result in setting the width to 0
                continue
            old_size = self.model().headerData(logical_index,
                                               Qt.Orientation.Horizontal,
                                               Qt.ItemDataRole.SizeHintRole)
            # when the size is different from the one from the model, the
            # user changed it
            if (old_size is not None) and (old_size.width() != new_width):
                new_size = QtCore.QSize(new_width, old_size.height())
                self.model().setHeaderData(logical_index,
                                           Qt.Orientation.Horizontal,
                                           new_size,
                                           Qt.ItemDataRole.SizeHintRole)
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
        self._columns_changed[logical_index] = new_width

    @QtCore.qt_slot(int)
    def horizontal_section_clicked(self, logical_index):
        """Update the sorting of the model and the header"""
        header = self.horizontalHeader()
        order = Qt.SortOrder.AscendingOrder
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
        current_index = self.currentIndex()
        if not current_index.isValid():
            return
        self.closePersistentEditor(current_index)

    def setModel(self, model):
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
        # not required/allowed for CrudItemModel
        #model.setParent(self)
        # assign selection model to local variable to keep it alive during
        # method call, or PySide segfaults
        selection_model = self.selectionModel()
        selection_model.currentChanged.connect(self._current_changed)
        model.modelReset.connect(self.update_headers)
        if hasattr(model, 'updateHeaders'):
            model.updateHeaders.connect(self.update_headers)
        self.update_headers()

    @QtCore.qt_slot()
    def update_headers(self):
        """
        Updating the header size seems to be no default Qt function, so, it's
        managed here
        """
        model = self.model()
        for i in range(model.columnCount()):
            size_hint = model.headerData(i,
                                         Qt.Orientation.Horizontal,
                                         Qt.ItemDataRole.SizeHintRole)
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
            column_size_hint = header_data(current.column(),
                                           Qt.Orientation.Horizontal,
                                           Qt.ItemDataRole.SizeHintRole)
            row_size_hint = header_data(current.row(),
                                        Qt.Orientation.Vertical,
                                        Qt.ItemDataRole.SizeHintRole)
            editor_size_hint = editor.sizeHint()
            self.setRowHeight(current.row(), max(row_size_hint.height(),
                                                 editor_size_hint.height()))
            self.setColumnWidth(current.column(),
                                max(column_size_hint.width(),
                                    editor_size_hint.width()))
        if current.row() != previous.row():
            if previous.row() >= 0:
                row_size_hint = header_data(previous.row(),
                                            Qt.Orientation.Vertical,
                                            Qt.ItemDataRole.SizeHintRole)
                self.setRowHeight(previous.row(), row_size_hint.height())
        if current.column() != previous.column():
            if previous.column() >= 0:
                column_size_hint = header_data(previous.column(),
                                               Qt.Orientation.Horizontal,
                                               Qt.ItemDataRole.SizeHintRole)
                self.setColumnWidth(previous.column(),
                                    column_size_hint.width())
        # whenever we change the size, sectionsResized is called, but these
        # changes should not be saved.
        self._columns_changed = dict()

        self.model().changeSelection([current.row(), current.row()], current.row(), current.column())

    def keyPressEvent(self, e):
        if self.hasFocus() and e.key() in (QtCore.Qt.Key.Key_Enter,
                                           QtCore.Qt.Key.Key_Return):
            self.keyboard_selection_signal.emit()
        else:
            super(TableWidget, self).keyPressEvent(e)
