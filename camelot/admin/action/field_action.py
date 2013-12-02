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

"""ModelContext, GuiContext and Actions that are used in the context of
editing a single field on a form or in a table.  This module contains the
various actions that are beyond the icons shown in the editors of a form.
"""

import inspect
import os

from PyQt4.QtCore import Qt
from PyQt4 import QtGui

from ...core.utils import ugettext_lazy as _
from ...view.art import Icon
from .base import Action
from .application_action import (ApplicationActionModelContext,
                                 ApplicationActionGuiContext)

import six

class FieldActionModelContext( ApplicationActionModelContext ):
    """The context for a :class:`Action` on a field.  On top of the attributes of the
    :class:`camelot.admin.action.application_action.ApplicationActionGuiContext`,
    this context contains :

    .. attribute:: obj

       the object of which the field displays a field

    .. attribute:: field

       the name of the field that is being displayed

       attribute:: value

       the value of the field as it is displayed in the editor

    .. attribute:: field_attributes

        A dictionary of field attributes of the field to which the context
        relates.

    """

    def __init__(self):
        super( FieldActionModelContext, self ).__init__()
        self.obj = None
        self.field = None
        self.value = None
        self.field_attributes = {}

class FieldActionGuiContext( ApplicationActionGuiContext ):
    """The context for an :class:`Action` on a field.  On top of the attributes of the
    :class:`camelot.admin.action.application_action.ApplicationActionGuiContext`,
    this context contains :

    .. attribute:: editor

       the editor through which the field is edited.

    """

    model_context = FieldActionModelContext

    def __init__( self ):
        super( FieldActionGuiContext, self ).__init__()
        self.editor = None

    def create_model_context( self ):
        context = super( FieldActionGuiContext, self ).create_model_context()
        context.value = self.editor.get_value()
        context.field_attributes = self.editor.get_field_attributes()
        return context

    def copy( self, base_class = None ):
        new_context = super( FieldActionGuiContext, self ).copy( base_class )
        new_context.editor = self.editor
        return new_context

class FieldAction(Action):
    """Action class that renders itself as a toolbutton, small enough to
    fit in an editor"""

    def render( self, gui_context, parent ):
        from ...view.controls.action_widget import ActionToolbutton
        button = ActionToolbutton(self, gui_context, parent)
        button.setAutoRaise(True)
        button.setFocusPolicy(Qt.ClickFocus)
        return button

class ShowFieldAttributes(Action):
    
    def model_run(self, model_context):
        from camelot.view import action_steps
        from camelot.admin.object_admin import ObjectAdmin

        class Attribute(object):
            """Helper class representing a field attribute's name and its value"""
            def __init__(self, name, value):
                self.name = six.text_type(name)
                if inspect.isclass(value):
                    self.value = value.__name__
                else:
                    self.value = six.text_type(value)
                        
            class Admin(ObjectAdmin):
                list_display = ['name', 'value']
                field_attributes = {'name':{'minimal_column_width':25},
                                    'value':{'minimal_column_width':25}}
        
        attributes = [Attribute(key,value) for key,value in six.iteritems(model_context.field_attributes.items)]
        yield action_steps.ChangeObjects(attributes, 
                                         model_context.admin.get_related_admin(Attribute))

class SelectObject(FieldAction):
    """Allows the user to select an object, and set the selected object as
    the new value of the editor"""

    icon = Icon('tango/16x16/actions/system-search.png')
    tooltip = _('select existing')

    def model_run(self, model_context):
        from camelot.view import action_steps
        admin = model_context.field_attributes['admin']
        selected_objects = yield action_steps.SelectObjects(admin)
        for selected_object in selected_objects:
            yield action_steps.UpdateEditor('selected_object', selected_object)
            break

    def get_state(self, model_context):
        state = super(SelectObject, self).get_state(model_context)
        state.visible = (model_context.value is None)
        state.enabled = model_context.field_attributes.get('editable', False)
        return state

class NewObject(SelectObject):
    """Open a form for the creation of a new object, and set this
    object as the new value of the editor"""

    icon = Icon('tango/16x16/actions/document-new.png')
    tooltip = _('create new')

    def model_run(self, model_context):
        from camelot.view import action_steps
        admin = model_context.field_attributes['admin']
        admin = yield action_steps.SelectSubclass(admin)
        obj = admin.entity()
        # Give the default fields their value
        admin.add(obj)
        admin.set_defaults(obj)
        yield action_steps.UpdateEditor('new_value', obj)
        yield action_steps.OpenFormView([obj], admin)

class OpenObject(SelectObject):
    """Open the value of an editor in a form view"""

    icon = Icon('tango/16x16/places/folder.png')
    tooltip = _('open')

    def model_run(self, model_context):
        from camelot.view import action_steps
        obj = model_context.value
        if obj is not None:
            admin = model_context.field_attributes['admin']
            admin = admin.get_related_admin(obj.__class__)
            yield action_steps.OpenFormView([obj], admin)

    def get_state(self, model_context):
        state = super(OpenObject, self).get_state(model_context)
        state.visible = (model_context.value is not None)
        state.enabled = (model_context.value is not None)
        return state

class ClearObject(OpenObject):
    """Set the new value of the editor to `None`"""

    icon = Icon('tango/16x16/actions/edit-clear.png')
    tooltip = _('clear')

    def model_run(self, model_context):
        from camelot.view import action_steps
        yield action_steps.UpdateEditor('selected_object', None)

    def get_state(self, model_context):
        state = super(ClearObject, self).get_state(model_context)
        state.enabled = model_context.field_attributes.get('editable', False)
        return state

class UploadFile(FieldAction):
    """Upload a new file into the storage of the field"""

    icon = Icon('tango/16x16/actions/list-add.png')
    tooltip = _('Attach file')
    file_name_filter = 'All files (*)'

    def model_run(self, model_context):
        from camelot.view import action_steps
        filenames = yield action_steps.SelectFile(self.file_name_filter)
        storage = model_context.field_attributes['storage']
        for file_name in filenames:
            remove = False
            if model_context.field_attributes.get('remove_original'):
                reply = yield action_steps.MessageBox(
                    text = _('Do you want to remove the original file?'),
                    icon = QtGui.QMessageBox.Warning,
                    title = _('The file will be stored.'),
                    standard_buttons = QtGui.QMessageBox.No | QtGui.QMessageBox.Yes
                    )
                if reply == QtGui.QMessageBox.Yes:
                    remove = True
            yield action_steps.UpdateProgress(text='Attaching file')
            stored_file = storage.checkin(file_name)
            yield action_steps.UpdateEditor('value', stored_file, propagate=True)
            if remove:
                os.remove(file_name)

    def get_state(self, model_context):
        state = super(UploadFile, self).get_state(model_context)
        state.enabled = model_context.field_attributes.get('editable', False)
        state.enabled = (state.enabled is True) and (model_context.value is None)
        state.visible = (model_context.value is None)
        return state

class DetachFile(FieldAction):
    """Set the new value of the editor to `None`, leaving the
    actual file in the storage alone"""

    icon = Icon('tango/16x16/actions/edit-delete.png')
    tooltip = _('Detach file')
    message_title = _('Detach this file ?')
    message_text = _('If you continue, you will no longer be able to open this file.')

    def model_run(self, model_context):
        from camelot.view import action_steps
        buttons = QtGui.QMessageBox.Yes|QtGui.QMessageBox.No
        answer = yield action_steps.MessageBox(title=self.message_title,
                                               text=self.message_text,
                                               standard_buttons=buttons)
        if answer == QtGui.QMessageBox.Yes:
            yield action_steps.UpdateEditor('value', None, propagate=True)

    def get_state(self, model_context):
        state = super(DetachFile, self).get_state(model_context)
        state.enabled = model_context.field_attributes.get('editable', False)
        state.enabled = (state.enabled is True) and (model_context.value is not None)
        state.visible = (model_context.value is not None)
        return state

class OpenFile(FieldAction):
    """Open the file shown in the editor"""

    icon = Icon('tango/16x16/actions/document-open.png')
    tooltip = _('Open file')

    def model_run(self, model_context):
        from camelot.view import action_steps
        yield action_steps.UpdateProgress(text=_('Checkout file'))
        storage = model_context.field_attributes['storage']
        local_path = storage.checkout(model_context.value)
        yield action_steps.UpdateProgress(text=_('Open file'))
        yield action_steps.OpenFile(local_path)

    def get_state(self, model_context):
        state = super(OpenFile, self).get_state(model_context)
        state.enabled = model_context.value is not None
        state.visible = state.enabled
        return state

class SaveFile(OpenFile):
    """Copy the file shown in the editor to another location"""

    icon = Icon('tango/16x16/actions/document-save-as.png')
    tooltip = _('Save as')

    def model_run(self, model_context):
        from camelot.view import action_steps
        stored_file = model_context.value
        storage = model_context.field_attributes['storage']
        local_path = yield action_steps.SaveFile()
        with open(local_path, 'wb') as destination:
            yield action_steps.UpdateProgress(text=_('Saving file'))
            destination.write(storage.checkout_stream(stored_file).read())

