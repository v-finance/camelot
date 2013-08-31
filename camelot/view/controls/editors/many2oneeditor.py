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

from functools import update_wrapper, partial

from PyQt4 import QtGui
from PyQt4 import QtCore
from PyQt4.QtCore import Qt

from ....admin.action import field_action
from camelot.view.model_thread import post, object_thread, model_function
from camelot.view.search import create_entity_search_query_decorator
from camelot.view.remote_signals import get_signal_handler
from camelot.view.controls.decorated_line_edit import DecoratedLineEdit

from camelot.core.utils import ugettext as _
from camelot.core.utils import variant_to_pyobject

from customeditor import CustomEditor, set_background_color_palette

import logging
logger = logging.getLogger('camelot.view.controls.editors.many2oneeditor')

class Many2OneEditor( CustomEditor ):
    """Widget for editing many 2 one relations"""

    arrow_down_key_pressed = QtCore.pyqtSignal()

    class CompletionsModel(QtCore.QAbstractListModel):

        def __init__(self, parent=None):
            QtCore.QAbstractListModel.__init__(self, parent)
            self._completions = []

        def setCompletions(self, completions):
            self._completions = completions
            self.layoutChanged.emit()

        def data(self, index, role):
            if role == Qt.DisplayRole:
                return QtCore.QVariant(self._completions[index.row()][0])
            elif role == Qt.EditRole:
                return QtCore.QVariant(self._completions[index.row()][1])
            return QtCore.QVariant()

        def rowCount(self, index=None):
            return len(self._completions)

        def columnCount(self, index=None):
            return 1

    def __init__(self,
                 admin=None,
                 parent=None,
                 editable=True,
                 field_name='manytoone',
                 actions = [field_action.ClearObject(),
                            field_action.SelectObject(),
                            field_action.NewObject(),
                            field_action.OpenObject()],
                 **kwargs):
        """:param entity_admin : The Admin interface for the object on the one
        side of the relation
        """
        CustomEditor.__init__(self, parent)
        self.setSizePolicy( QtGui.QSizePolicy.Preferred,
                            QtGui.QSizePolicy.Fixed )
        self.setObjectName( field_name )
        self.admin = admin
        self.new_value = None
        self._entity_representation = ''
        self.obj = None
        self._last_highlighted_entity_getter = None

        self.layout = QtGui.QHBoxLayout()
        self.layout.setSpacing(0)
        self.layout.setContentsMargins( 0, 0, 0, 0)

        # Search input
        self.search_input = DecoratedLineEdit(self)
        self.search_input.setPlaceholderText(_('Search...'))
        self.search_input.textEdited.connect(self.textEdited)
        self.search_input.set_minimum_width( 20 )
        self.search_input.arrow_down_key_pressed.connect(self.on_arrow_down_key_pressed)
        # suppose garbage was entered, we need to refresh the content
        self.search_input.editingFinished.connect(self.search_input_editing_finished)
        self.setFocusProxy(self.search_input)

        # Search Completer
        self.completer = QtGui.QCompleter()
        self.completions_model = self.CompletionsModel(self.completer)
        self.completer.setModel(self.completions_model)
        self.completer.setCaseSensitivity(Qt.CaseInsensitive)
        self.completer.setCompletionMode(
            QtGui.QCompleter.UnfilteredPopupCompletion
        )
        self.completer.activated[QtCore.QModelIndex].connect(self.completionActivated)
        self.completer.highlighted[QtCore.QModelIndex].connect(self.completion_highlighted)
        self.search_input.setCompleter(self.completer)

        # Setup layout
        self.layout.addWidget(self.search_input)
        self.setLayout(self.layout)
        self.add_actions(actions, self.layout)
        get_signal_handler().connect_signals(self)

    def set_field_attributes(self, **fa):
        self.field_attributes = fa
        set_background_color_palette(self.search_input, fa.get('background_color'))
        self.search_input.setToolTip(fa.get('tooltip', '') or '')
        self.search_input.setEnabled(fa.get('editable', False))
        self.update_actions()

    def on_arrow_down_key_pressed(self):
        self.arrow_down_key_pressed.emit()

    def textEdited(self, text):
        self._last_highlighted_entity_getter = None
        text = unicode( self.search_input.text() )

        def create_search_completion(text):
            return lambda: self.search_completions(text)

        post(
            create_search_completion(unicode(text)),
            self.display_search_completions
        )
        self.completer.complete()

    @model_function
    def search_completions(self, text):
        """Search for object that match text, to fill the list of completions

        :return: a list of tuples of (object_representation, object)
        """
        search_decorator = create_entity_search_query_decorator(
            self.admin, text
        )
        if search_decorator:
            sresult = [
                (unicode(e), e)
                for e in search_decorator(self.admin.get_query()).limit(20)
            ]
            return text, sresult
        return text, []

    def display_search_completions(self, prefix_and_completions):
        assert object_thread( self )
        prefix, completions = prefix_and_completions
        self.completions_model.setCompletions(completions)
        self.completer.setCompletionPrefix(prefix)
        self.completer.complete()

    def completionActivated(self, index):
        obj = index.data(Qt.EditRole)
        self.set_object(variant_to_pyobject(obj))

    def completion_highlighted(self, index ):
        obj = index.data(Qt.EditRole)
        self._last_highlighted_entity_getter = variant_to_pyobject(obj)

    @QtCore.pyqtSlot( object, object )
    def handle_entity_update( self, sender, entity ):
        if entity is self.get_value():
            self.set_object(entity, False)

    @QtCore.pyqtSlot( object, object )
    def handle_entity_delete( self, sender, entity ):
        if entity is self.get_value():
            self.set_object(None, False)

    @QtCore.pyqtSlot( object, object )
    def handle_entity_create( self, sender, entity ):
        if entity is self.new_value:
            self.new_value = None
            self.set_object(entity)

    def search_input_editing_finished(self):
        if self.obj is None:
            # Only try to 'guess' what the user meant when no entity is set
            # to avoid inappropriate removal of data, (eg when the user presses
            # Esc, editingfinished will be called as well, and we should not
            # overwrite the current entity set)
            if self._last_highlighted_entity_getter:
                self.set_object(self._last_highlighted_entity_getter)
            elif self.completions_model.rowCount()==1:
                # There is only one possible option
                index = self.completions_model.index(0,0)
                entity_getter = variant_to_pyobject(index.data(Qt.EditRole))
                self.set_object(entity_getter)
        self.search_input.setText(self._entity_representation or u'')

    def set_value(self, value):
        """:param value: either ValueLoading, or a function that returns None
        or the entity to be shown in the editor"""
        self._last_highlighted_entity_getter = None
        self.new_value = None
        value = CustomEditor.set_value(self, value)
        self.set_object(value, propagate = False)
        self.update_actions()

    def get_value(self):
        """:return: a function that returns the selected entity or ValueLoading
        or None"""
        value = CustomEditor.get_value(self)
        if value is not None:
            return value
        return self.obj

    @QtCore.pyqtSlot(tuple)
    def set_instance_representation(self, representation_and_propagate):
        """Update the gui"""
        (desc, propagate) = representation_and_propagate
        self._entity_representation = desc
        self.search_input.setText(desc or u'')

        if propagate:
            self.editingFinished.emit()

    def set_object(self, obj, propagate=True):
        self.obj = obj

        def get_instance_representation( obj, propagate ):
            """Get a representation of the instance"""
            if obj is not None:
                return (unicode(obj), propagate)
            return (None, propagate)

        post( update_wrapper( partial( get_instance_representation,
                                       obj,
                                       propagate ),
                              get_instance_representation ),
              self.set_instance_representation)

    selected_object = property(fset=set_object)
