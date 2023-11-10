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

import logging

from ....core.naming import initial_naming_context
from ....core.qt import QtGui, QtCore, Qt, QtWidgets
from ....core.utils import ugettext as _
from ..decorated_line_edit import DecoratedLineEdit

from .customeditor import CustomEditor, set_background_color_palette

logger = logging.getLogger('camelot.view.controls.editors.many2oneeditor')

# since this is gui code, we assume all names are lists,
# as the original tuple has been serialized/deserialized

none_name = list(initial_naming_context._bind_object(None))

class Many2OneEditor(CustomEditor):
    """Widget for editing many 2 one relations"""

    arrow_down_key_pressed = QtCore.qt_signal()

    def __init__(self,
                 parent=None,
                 action_routes = [],
                 field_name='manytoone'):
        """
        :param entity_admin : The Admin interface for the object on the one
        side of the relation
        """
        CustomEditor.__init__(self, parent)
        self.setSizePolicy( QtWidgets.QSizePolicy.Policy.Preferred,
                            QtWidgets.QSizePolicy.Policy.Fixed )
        self.setObjectName( field_name )
        self.verbose_name = ''
        self.name = none_name
        self.last_highlighted_name = None

        layout = QtWidgets.QHBoxLayout()
        layout.setSpacing(0)
        layout.setContentsMargins( 0, 0, 0, 0)
        #
        # The search timer reduced the number of search signals that are
        # emitted, by waiting for the next keystroke before emitting the
        # search signal
        #
        timer = QtCore.QTimer( self )
        timer.setInterval( 300 )
        timer.setSingleShot( True )
        timer.setObjectName( 'timer' )
        timer.timeout.connect(self.start_search)
        
        # Search input
        self.search_input = DecoratedLineEdit(self)
        self.search_input.setPlaceholderText(_('Search...'))
        # Replaced by timer start, which will call textEdited if it runs out.
        #self.search_input.textEdited.connect(self.textEdited)
        self.search_input.textEdited.connect(self._start_search_timer)
        self.search_input.set_minimum_width( 20 )
        self.search_input.arrow_down_key_pressed.connect(self.on_arrow_down_key_pressed)
        # suppose garbage was entered, we need to refresh the content
        self.search_input.editingFinished.connect(self.search_input_editing_finished)
        self.setFocusProxy(self.search_input)

        # Search Completer
        self.completer = QtWidgets.QCompleter()
        self.completer.setModel(QtGui.QStandardItemModel(self.completer))
        self.completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self.completer.setCompletionMode(
            QtWidgets.QCompleter.CompletionMode.UnfilteredPopupCompletion
        )
        self.completer.activated[QtCore.QModelIndex].connect(self.completionActivated)
        self.completer.highlighted[QtCore.QModelIndex].connect(self.completion_highlighted)
        self.search_input.setCompleter(self.completer)
        
        # Setup layout
        layout.addWidget(self.search_input)
        self.setLayout(layout)
        self.add_actions(action_routes, layout)

    @QtCore.qt_slot()
    @QtCore.qt_slot(str)
    def _start_search_timer(self, str=''):
        timer = self.findChild( QtCore.QTimer, 'timer' )
        if timer is not None:
            timer.start()

    @QtCore.qt_slot()
    @QtCore.qt_slot(str)
    def start_search(self, str=''):
        timer = self.findChild( QtCore.QTimer, 'timer' )
        if timer is not None:
            timer.stop()
        self.textEdited(self.search_input.text())

    def set_tooltip(self, tooltip):
        super().set_tooltip(tooltip)
        self.search_input.setToolTip(str(tooltip or ''))

    def set_background_color(self, background_color):
        super().set_background_color(background_color)
        set_background_color_palette(self.search_input, background_color)

    def set_editable(self, editable):
        self.search_input.setEnabled(editable)

    def on_arrow_down_key_pressed(self):
        self.arrow_down_key_pressed.emit()

    def textEdited(self, text):
        self.last_highlighted_name = None
        self.completer.setCompletionPrefix(text)
        self.completionPrefixChanged.emit(str(text))

    def display_search_completions(self, completions):
        # this might interrupt with the user typing
        model = self.completer.model()
        model.setColumnCount(1)
        model.setRowCount(len(completions))
        for row, completion in enumerate(completions):
            index = model.index(row, 0)
            for role, data in completion.items():
                model.setData(index, data, int(role))
        self.completer.complete()

    def completionActivated(self, index):
        self.name = index.data(Qt.ItemDataRole.UserRole)
        self.editingFinished.emit()

    def completion_highlighted(self, index):
        self.last_highlighted_name = index.data(Qt.ItemDataRole.UserRole)

    def search_input_editing_finished(self):
        if self.name == none_name:
            # Only try to 'guess' what the user meant when no entity is set
            # to avoid inappropriate removal of data, (eg when the user presses
            # Esc, editingfinished will be called as well, and we should not
            # overwrite the current entity set)
            if self.last_highlighted_name is not None:
                self.name = self.last_highlighted_name
                self.editingFinished.emit()
            elif self.completer.model().rowCount()==1:
                # There is only one possible option
                index = self.completer.model().index(0,0)
                self.name = index.data(Qt.ItemDataRole.UserRole)
                self.editingFinished.emit()
        self.search_input.setText(self.verbose_name or u'')

    def set_value(self, value):
        """:param value: either ValueLoading, or a function that returns None
        or the entity to be shown in the editor"""
        value = list(value if value is not None else none_name)
        self.last_highlighted_name = None
        self.name = value

    def get_value(self):
        """:return: a function that returns the selected entity or ValueLoading
        or None"""
        return self.name

    def set_verbose_name(self, verbose_name):
        """Update the gui"""
        self.verbose_name = verbose_name
        self.search_input.setText(verbose_name or u'')
