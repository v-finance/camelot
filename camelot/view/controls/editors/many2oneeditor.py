#  ============================================================================
#
#  Copyright (C) 2007-2012 Conceptive Engineering bvba. All rights reserved.
#  www.conceptive.be / project-camelot@conceptive.be
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
#  visit www.python-camelot.com or contact project-camelot@conceptive.be
#
#  This file is provided AS IS with NO WARRANTY OF ANY KIND, INCLUDING THE
#  WARRANTY OF DESIGN, MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE.
#
#  For use of this library in commercial applications, please contact
#  project-camelot@conceptive.be
#
#  ============================================================================

from functools import update_wrapper, partial

from PyQt4 import QtGui
from PyQt4 import QtCore
from PyQt4.QtCore import Qt

from camelot.view.art import Icon
from camelot.view.model_thread import post, object_thread, model_function
from camelot.view.search import create_entity_search_query_decorator
from camelot.view.controls.decorated_line_edit import DecoratedLineEdit

from camelot.core.utils import ugettext as _
from camelot.core.utils import variant_to_pyobject
from camelot.core.utils import create_constant_function

from customeditor import CustomEditor, set_background_color_palette

import logging
logger = logging.getLogger('camelot.view.controls.editors.many2oneeditor')


class Many2OneEditor( CustomEditor ):
    """Widget for editing many 2 one relations"""

    new_icon = Icon('tango/16x16/actions/document-new.png')
    search_icon = Icon('tango/16x16/actions/system-search.png')

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
                 **kwargs):
        """:param entity_admin : The Admin interface for the object on the one
        side of the relation
        """

        CustomEditor.__init__(self, parent)
        self.setObjectName( field_name )
        self.admin = admin
        self.entity_set = False
        self._editable = editable
        self._entity_representation = ''
        self.entity_instance_getter = None
        self._last_highlighted_entity_getter = None

        self.layout = QtGui.QHBoxLayout()
        self.layout.setSpacing(0)
        self.layout.setContentsMargins( 0, 0, 0, 0)

        # Search button
        self.search_button = QtGui.QToolButton()
        self.search_button.setAutoRaise(True)
        self.search_button.setFocusPolicy(Qt.ClickFocus)
        self.search_button.setFixedHeight(self.get_height())
        self.search_button.clicked.connect(self.searchButtonClicked)
        self.search_button.setIcon(
            Icon('tango/16x16/actions/edit-clear.png').getQIcon()
        )
        self.search_button.setToolTip(unicode(_('clear')))

        # Open button
        self.open_button = QtGui.QToolButton()
        self.open_button.setAutoRaise(True)
        self.open_button.setFocusPolicy(Qt.ClickFocus)
        self.open_button.setFixedHeight(self.get_height())
        self.open_button.clicked.connect(self.openButtonClicked)
        self.open_button.setIcon( self.new_icon.getQIcon() )
        self.open_button.setToolTip(unicode(_('new')))

        # Search input
        self.search_input = DecoratedLineEdit(self)
        self.search_input.set_background_text(_('Search...'))
        self.search_input.textEdited.connect(self.textEdited)
        self.search_input.set_minimum_width( 20 )
        self.search_input.arrow_down_key_pressed.connect(self.on_arrow_down_key_pressed)
        # suppose garbage was entered, we need to refresh the content
        self.search_input.editingFinished.connect( self.search_input_editing_finished )
        self.setFocusProxy(self.search_input)

        # Search Completer
        self.completer = QtGui.QCompleter()
        self.completions_model = self.CompletionsModel(self.completer)
        self.completer.setModel(self.completions_model)
        self.completer.setCaseSensitivity(Qt.CaseInsensitive)
        self.completer.setCompletionMode(
            QtGui.QCompleter.UnfilteredPopupCompletion
        )
        #self.completer.activated.connect(self.completionActivated)
        #self.completer.highlighted.connect(self.completion_highlighted)
        self.completer.activated[QtCore.QModelIndex].connect(self.completionActivated)
        self.completer.highlighted[QtCore.QModelIndex].connect(self.completion_highlighted)
        self.search_input.setCompleter(self.completer)

        # Setup layout
        self.layout.addWidget(self.search_input)
        self.layout.addWidget(self.search_button)
        self.layout.addWidget(self.open_button)
        self.setLayout(self.layout)

    def set_field_attributes(self, editable = True, 
                                   background_color = None,
                                   tooltip = None, **kwargs):
        self.set_editable(editable)
        set_background_color_palette( self.search_input, background_color )
        self.search_input.setToolTip(unicode(tooltip or ''))

    def set_editable(self, editable):
        self._editable = editable
        self.search_input.setEnabled(editable)
        self.search_button.setEnabled(editable)

    def on_arrow_down_key_pressed(self):
        self.arrow_down_key_pressed.emit()

    def textEdited(self, text):
        self._last_highlighted_entity_getter = None
        text = self.search_input.user_input()

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

        :return: a list of tuples of (object_representation, object_getter)
        """
        search_decorator = create_entity_search_query_decorator(
            self.admin, text
        )
        if search_decorator:
            sresult = [
                (unicode(e), create_constant_function(e))
                for e in search_decorator(self.admin.entity.query).limit(20)
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
        object_getter = index.data(Qt.EditRole)
        self.setEntity(variant_to_pyobject(object_getter))

    def completion_highlighted(self, index ):
        object_getter = index.data(Qt.EditRole)
        pyob = variant_to_pyobject(object_getter)
        self._last_highlighted_entity_getter = pyob

    def openButtonClicked(self):
        if self.entity_set:
            return self.createFormView()
        else:
            return self.createNew()

    def createSelectView(self):
        from camelot.view.action_steps.select_object import SelectDialog
        select_dialog = SelectDialog( self.admin, self )
        select_dialog.exec_()
        if select_dialog.object_getter != None:
            self.select_object( select_dialog.object_getter )
            
    def returnPressed(self):
        if not self.entity_set:
            self.createSelectView()

    def searchButtonClicked(self):
        if self.entity_set:
            self.setEntity(lambda:None)
        else:
            self.createSelectView()

    def trashButtonClicked(self):
        self.setEntity(lambda:None)

    def createNew(self):
        assert object_thread( self )

        @model_function
        def get_has_subclasses():
            return len(self.admin.get_subclass_tree())

        post(get_has_subclasses, self.show_new_view)

    def show_new_view(self, has_subclasses):
        assert object_thread( self )
        from camelot.view.workspace import show_top_level
        selected = QtGui.QDialog.Accepted
        admin = self.admin
        if has_subclasses:
            from camelot.view.controls.inheritance import SubclassDialog
            select_subclass = SubclassDialog(self, self.admin)
            select_subclass.setWindowTitle(_('select'))
            selected = select_subclass.exec_()
            admin = select_subclass.selected_subclass
        if selected:
            form = admin.create_new_view()
            form.entity_created_signal.connect( self.select_object )
            show_top_level( form, self )

    def createFormView(self):
        if self.entity_instance_getter:

            def get_admin_and_title():
                obj = self.entity_instance_getter()
                admin = self.admin.get_related_admin(obj.__class__)
                return admin, ''

            post(get_admin_and_title, self.show_form_view)

    def show_form_view(self, admin_and_title):
        from camelot.view.workspace import show_top_level
        admin, title = admin_and_title

        def create_collection_getter(instance_getter):
            return lambda:[instance_getter()]

        from camelot.view.proxy.collection_proxy import CollectionProxy

        model = CollectionProxy(
            admin,
            create_collection_getter(self.entity_instance_getter),
            admin.get_fields
        )
        model.dataChanged.connect(self.dataChanged)
        form = admin.create_form_view(title, model, 0)
        # @todo : dirty trick to keep reference
        #self.__form = form
        show_top_level( form, self )

    def dataChanged(self, index1, index2):
        self.setEntity(self.entity_instance_getter, False)

    def search_input_editing_finished(self):
        if not self.entity_set:
            # Only try to 'guess' what the user meant when no entity is set
            # to avoid inappropriate removal of data, (eg when the user presses
            # Esc, editingfinished will be called as well, and we should not
            # overwrite the current entity set)
            if self._last_highlighted_entity_getter:
                self.setEntity(self._last_highlighted_entity_getter)
            elif not self.entity_set and self.completions_model.rowCount()==1:
                # There is only one possible option
                index = self.completions_model.index(0,0)
                entity_getter = variant_to_pyobject(index.data(Qt.EditRole))
                self.setEntity(entity_getter)
        self.search_input.set_user_input(self._entity_representation)

    def set_value(self, value):
        """:param value: either ValueLoading, or a function that returns None
        or the entity to be shown in the editor"""
        self._last_highlighted_entity_getter = None
        value = CustomEditor.set_value(self, value)
        if value:
            self.setEntity(value, propagate = False)

    def get_value(self):
        """:return: a function that returns the selected entity or ValueLoading
        or None"""
        value = CustomEditor.get_value(self)
        if not value:
            value = self.entity_instance_getter
        return value

    @QtCore.pyqtSlot(tuple)
    def set_instance_representation(self, representation_and_propagate):
        """Update the gui"""
        ((desc, pk), propagate) = representation_and_propagate
        self._entity_representation = desc
        self.search_input.set_user_input(desc)

        if pk != False:
            self.open_button.setIcon(
                Icon('tango/16x16/places/folder.png').getQIcon()
            )
            self.open_button.setToolTip(unicode(_('open')))
            self.open_button.setEnabled(True)

            self.search_button.setIcon(
                Icon('tango/16x16/actions/edit-clear.png').getQIcon()
            )
            self.search_button.setToolTip(unicode(_('clear')))
            self.entity_set = True
        else:
            self.open_button.setIcon( self.new_icon.getQIcon() )
            self.open_button.setToolTip(unicode(_('new')))
            self.open_button.setEnabled(self._editable)

            self.search_button.setIcon( self.search_icon.getQIcon() )
            self.search_button.setToolTip(_('Search'))
            self.entity_set = False

        if propagate:
            self.editingFinished.emit()

    def setEntity(self, entity_instance_getter, propagate=True):
        self.entity_instance_getter = entity_instance_getter
        
        def get_instance_representation( entity_instance_getter, propagate ):
            """Get a representation of the instance

            :return: (unicode, pk) its unicode representation and its primary
            key or ('', False) if the instance was None"""
            
            entity = entity_instance_getter()
            if entity and hasattr(entity, 'id'):
                return ((unicode(entity), entity.id), propagate)
            elif entity:
                return ((unicode(entity), False), propagate)
            return ((None, False), propagate)

        post( update_wrapper( partial( get_instance_representation,
                                       entity_instance_getter,
                                       propagate ),
                              get_instance_representation ), 
              self.set_instance_representation)

    def select_object( self, entity_instance_getter ):
        self.setEntity(entity_instance_getter)
