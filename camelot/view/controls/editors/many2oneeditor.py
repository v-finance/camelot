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

from functools import update_wrapper, partial

import six

from ....core.qt import QtCore, Qt, QtWidgets, py_to_variant, variant_to_py

from ....admin.action import field_action
from ....admin.action.list_filter import SearchFilter
from ...crud_signals import CrudSignalHandler
from camelot.view.model_thread import post, object_thread
from camelot.view.controls.decorated_line_edit import DecoratedLineEdit
from camelot.core.utils import ugettext as _

from .customeditor import CustomEditor, set_background_color_palette

import logging
logger = logging.getLogger('camelot.view.controls.editors.many2oneeditor')

class Many2OneEditor( CustomEditor ):
    """Widget for editing many 2 one relations"""

    arrow_down_key_pressed = QtCore.qt_signal()

    class CompletionsModel(QtCore.QAbstractListModel):

        def __init__(self, parent):
            QtCore.QAbstractListModel.__init__(self, parent)
            self._completions = []

        def setCompletions(self, completions):
            self._completions = completions
            self.layoutChanged.emit()

        def data(self, index, role):
            return py_to_variant(self._completions[index.row()].get(role))

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
        """
        :param entity_admin : The Admin interface for the object on the one
        side of the relation
        """
        CustomEditor.__init__(self, parent)
        self.setSizePolicy( QtWidgets.QSizePolicy.Preferred,
                            QtWidgets.QSizePolicy.Fixed )
        self.setObjectName( field_name )
        self.admin = admin
        self.new_value = None
        self._entity_representation = ''
        self.obj = None
        self._last_highlighted_entity_getter = None

        layout = QtWidgets.QHBoxLayout()
        layout.setSpacing(0)
        layout.setContentsMargins( 0, 0, 0, 0)

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
        self.completer = QtWidgets.QCompleter()
        completions_model = self.CompletionsModel(self.completer)
        self.completer.setModel(completions_model)
        self.completer.setCaseSensitivity(Qt.CaseInsensitive)
        self.completer.setCompletionMode(
            QtWidgets.QCompleter.UnfilteredPopupCompletion
        )
        self.completer.activated[QtCore.QModelIndex].connect(self.completionActivated)
        self.completer.highlighted[QtCore.QModelIndex].connect(self.completion_highlighted)
        self.search_input.setCompleter(self.completer)

        # Setup layout
        layout.addWidget(self.search_input)
        self.setLayout(layout)
        self.add_actions(actions, layout)
        self.search_filter = SearchFilter(admin)
        CrudSignalHandler().connect_signals(self)

    def set_field_attributes(self, **kwargs):
        super(Many2OneEditor, self).set_field_attributes(**kwargs)
        set_background_color_palette(self.search_input, kwargs.get('background_color'))
        self.search_input.setToolTip(kwargs.get('tooltip') or '')
        self.search_input.setEnabled(kwargs.get('editable', False))
        self.update_actions()

    def on_arrow_down_key_pressed(self):
        self.arrow_down_key_pressed.emit()

    def textEdited(self, text):
        self._last_highlighted_entity_getter = None
        text = six.text_type( self.search_input.text() )

        def create_search_completion(text):
            return lambda: self.search_completions(text)

        post(
            create_search_completion(six.text_type(text)),
            self.display_search_completions
        )
        self.completer.complete()

    def search_completions(self, text):
        """Search for object that match text, to fill the list of completions

        :return: a list of tuples of (dict_of_object_representation, object)
        """
        query = self.admin.get_query()
        query = self.search_filter.decorate_query(query, text)

        sresult = [
            self.admin.get_search_identifiers(e)
            for e in query.limit(20).all()
        ]
        return text, sresult


    def display_search_completions(self, prefix_and_completions):
        assert object_thread( self )
        prefix, completions = prefix_and_completions
        self.completer.model().setCompletions(completions)
        self.completer.setCompletionPrefix(prefix)
        self.completer.complete()

    def completionActivated(self, index):
        obj = index.data(Qt.EditRole)
        self.set_object(variant_to_py(obj))

    def completion_highlighted(self, index ):
        obj = index.data(Qt.EditRole)
        self._last_highlighted_entity_getter = variant_to_py(obj)

    @QtCore.qt_slot(object, tuple)
    def objects_updated(self, sender, objects):
        value = self.get_value()
        for obj in objects:
            if obj is value:
                self.set_object(obj, False)

    @QtCore.qt_slot(object, tuple)
    def objects_deleted(self, sender, objects):
        value = self.get_value()
        for obj in objects:
            if obj is value:
                self.set_object(None, False)

    @QtCore.qt_slot(object, tuple)
    def objects_created(self, sender, objects):
        for obj in objects:
            if obj is self.new_value:
                self.new_value = None
                self.set_object(obj)

    def search_input_editing_finished(self):
        if self.obj is None:
            # Only try to 'guess' what the user meant when no entity is set
            # to avoid inappropriate removal of data, (eg when the user presses
            # Esc, editingfinished will be called as well, and we should not
            # overwrite the current entity set)
            if self._last_highlighted_entity_getter:
                self.set_object(self._last_highlighted_entity_getter)
            elif self.completer.model().rowCount()==1:
                # There is only one possible option
                index = self.completer.model().index(0,0)
                entity_getter = variant_to_py(index.data(Qt.EditRole))
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

    @QtCore.qt_slot(tuple)
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
                return (self.admin.get_verbose_object_name(obj), propagate)
            return (None, propagate)

        post( update_wrapper( partial( get_instance_representation,
                                       obj,
                                       propagate ),
                              get_instance_representation ),
              self.set_instance_representation)

    selected_object = property(fset=set_object)

