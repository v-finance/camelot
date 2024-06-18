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

"""ModelContext, GuiContext and Actions that are used in the context of
editing a single field on a form or in a table.  This module contains the
various actions that are beyond the icons shown in the editors of a form.
"""

import os

from sqlalchemy import orm

from ...core.qt import QtWidgets, QtGui
from ...core.utils import ugettext_lazy as _
from ...admin.icon import Icon
from .base import Action, RenderHint
from .list_action import AddNewObjectMixin
from .application_action import ApplicationActionModelContext


class FieldActionModelContext(ApplicationActionModelContext):
    """The context for a :class:`Action` on a field.  On top of the attributes of the
    :class:`camelot.admin.action.application_action.ApplicationActionModelContext`,
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

    def __init__(self, admin):
        super( FieldActionModelContext, self ).__init__(admin)
        self.obj = None
        self.field = None
        self.value = None
        self.field_attributes = {}


class EditFieldAction(Action):
    """A base class for an action that will modify the model, it will be
    disabled when the field_attributes for the field are set to  not-editable
    or the admin is not editable"""

    name = '_edit_field'

    def get_state(self, model_context):
        assert isinstance(model_context, FieldActionModelContext)
        state = super().get_state(model_context)
        # editability at the level of the field
        state.enabled = model_context.field_attributes.get('editable', False)
        return state

class SelectObject(EditFieldAction):
    """Allows the user to select an object, and set the selected object as
    the new value of the editor"""

    icon = Icon('search') # 'tango/16x16/actions/system-search.png'
    tooltip = _('select existing')
    name = 'select_object'
    render_hint = RenderHint.TOOL_BUTTON

    def model_run(self, model_context, mode):
        from camelot.view import action_steps
        field_admin = model_context.field_attributes.get('admin')
        if field_admin is not None:
            selected_object = yield action_steps.SelectObject(field_admin.get_query(), field_admin)
            if selected_object is not None:
                model_context.admin.set_field_value(
                    model_context.obj, model_context.field, selected_object
                )
                model_context.admin.set_defaults(model_context.obj)
                yield None

    def get_state(self, model_context):
        state = super().get_state(model_context)
        state.visible = (model_context.value is None)
        return state

class OpenObject(SelectObject):
    """Open the value of an editor in a form view"""

    icon = Icon('folder-open') # 'tango/16x16/places/folder.png'
    tooltip = _('open')
    name = 'open_object'

    def model_run(self, model_context, mode):
        from camelot.view import action_steps
        obj = model_context.value
        # Disregard the case of having no value, or having multiple defined.
        if obj is not None and not isinstance(obj, list):
            admin = model_context.field_attributes['admin']
            admin = admin.get_related_admin(obj.__class__)
            yield action_steps.OpenFormView(obj, admin)

    def get_state(self, model_context):
        state = super(OpenObject, self).get_state(model_context)
        obj = model_context.value
        state.visible = (obj is not None and not isinstance(obj, list))
        state.enabled = (obj is not None and not isinstance(obj, list))
        return state

class ClearObject(EditFieldAction):
    """Set the new value of the editor to `None`"""

    icon = Icon('eraser') # 'tango/16x16/actions/edit-clear.png'
    tooltip = _('clear')
    name = 'clear_object'

    def model_run(self, model_context, mode):
        field_admin = model_context.field_attributes.get('admin')
        if field_admin is not None:
            model_context.admin.set_field_value(
                model_context.obj, model_context.field, None
            )
            yield None

    def get_state(self, model_context):
        state = super(ClearObject, self).get_state(model_context)
        state.visible = (model_context.value is not None)
        return state

class UploadFile(EditFieldAction):
    """Upload a new file into the storage of the field"""

    icon = Icon('plus') # 'tango/16x16/actions/list-add.png'
    tooltip = _('Attach file')
    file_name_filter = 'All files (*)'
    name = 'attach_file'
    render_hint = RenderHint.TOOL_BUTTON

    def model_run(self, model_context, mode):
        from camelot.view import action_steps
        filenames = yield action_steps.SelectFile(self.file_name_filter)
        storage = model_context.field_attributes['storage']
        for file_name in filenames:
            # the storage cannot checkin empty file names
            if not file_name:
                continue
            remove = False
            if model_context.field_attributes.get('remove_original'):
                reply = yield action_steps.MessageBox(
                    text = _('Do you want to remove the original file?'),
                    icon = Icon('question'),
                    title = _('The file will be stored.'),
                    standard_buttons = [QtWidgets.QMessageBox.StandardButton.No, QtWidgets.QMessageBox.StandardButton.Yes]
                    )
                if reply == QtWidgets.QMessageBox.StandardButton.Yes:
                    remove = True
            yield action_steps.UpdateProgress(text='Attaching file')
            stored_file = storage.checkin(file_name)
            model_context.admin.set_field_value(
                model_context.obj, model_context.field, stored_file
            )
            if remove:
                os.remove(file_name)

    def get_state(self, model_context):
        state = super().get_state(model_context)
        state.enabled = (state.enabled is True) and (model_context.value is None)
        state.visible = (model_context.value is None)
        return state

class DetachFile(EditFieldAction):
    """Set the new value of the editor to `None`, leaving the
    actual file in the storage alone"""

    icon = Icon('trash') # 'tango/16x16/actions/edit-delete.png'
    tooltip = _('Detach file')
    message_title = _('Detach this file ?')
    message_text = _('If you continue, you will no longer be able to open this file.')
    name = 'detach_file'
    render_hint = RenderHint.TOOL_BUTTON

    def model_run(self, model_context, mode):
        from camelot.view import action_steps
        buttons = [QtWidgets.QMessageBox.StandardButton.Yes, QtWidgets.QMessageBox.StandardButton.No]
        answer = yield action_steps.MessageBox(title=self.message_title,
                                               text=self.message_text,
                                               standard_buttons=buttons)
        if answer == QtWidgets.QMessageBox.StandardButton.Yes:
            model_context.admin.set_field_value(
                model_context.obj, model_context.field, None
            )
            yield None

    def get_state(self, model_context):
        state = super().get_state(model_context)
        state.enabled = (state.enabled is True) and (model_context.value is not None)
        state.visible = (model_context.value is not None)
        return state

class OpenFile(Action):
    """Open the file shown in the editor"""

    icon = Icon('folder-open') # 'tango/16x16/actions/document-open.png'
    tooltip = _('Open file')
    name = 'open_file'
    render_hint = RenderHint.TOOL_BUTTON

    def model_run(self, model_context, mode):
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

    icon = Icon('save') # 'tango/16x16/actions/document-save-as.png'
    tooltip = _('Save as')
    name = 'file_save_as'

    def model_run(self, model_context, mode):
        from camelot.view import action_steps
        stored_file = model_context.value
        storage = model_context.field_attributes['storage']
        local_path = yield action_steps.SaveFile()
        with open(local_path, 'wb') as destination:
            yield action_steps.UpdateProgress(text=_('Saving file'))
            destination.write(storage.checkout_stream(stored_file).read())


class AddNewObject(AddNewObjectMixin, EditFieldAction):
    """Add a new object to a collection. Depending on the
    'create_inline' field attribute, a new form is opened or not.

    This action will also set the default values of the new object, add the
    object to the session, and flush the object if it is valid.
    """

    shortcut = QtGui.QKeySequence.StandardKey.New
    icon = Icon('plus-circle') # 'tango/16x16/actions/document-new.png'
    tooltip = _('New')
    verbose_name = _('New')
    name = 'new_object'
    render_hint = RenderHint.TOOL_BUTTON

    def get_proxy(self, model_context, admin):
        return model_context.value

    def get_default_admin(self, model_context, mode=None):
        return model_context.field_attributes.get('admin')

    def get_state(self, model_context):
        assert isinstance(model_context, FieldActionModelContext)
        state = super().get_state(model_context)
        admin = model_context.field_attributes.get('admin')
        if (admin is not None) and not admin.is_editable():
            state.visible = False
            state.enabled = False
        return state

add_new_object = AddNewObject()

class AddExistingObject(EditFieldAction):
    """Add an existing object to a list if it is not yet in the
    list"""
    
    tooltip = _('Add')
    verbose_name = _('Add')
    icon = Icon('plus') # 'tango/16x16/actions/list-add.png'
    name = 'add_object'
    
    def model_run( self, model_context, mode ):
        from camelot.view import action_steps
        super().model_run(model_context, mode)
        field_admin = model_context.field_attributes.get('admin')
        if field_admin is not None:
            objs_to_add = yield action_steps.SelectObjects(field_admin.get_query(), field_admin)
            # filter out objects already in model_context.value
            objs_to_add = [obj for obj in objs_to_add if obj not in model_context.value]
            if not objs_to_add:
                return
            for obj_to_add in objs_to_add:
                model_context.value.append(obj_to_add)
            yield action_steps.UpdateObjects(objs_to_add)
            for obj_to_add in objs_to_add:
                yield action_steps.FlushSession(orm.object_session(obj_to_add))
                break

add_existing_object = AddExistingObject()
