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

"""ModelContext and Actions that are used in the context of
editing a single field on a form or in a table.  This module contains the
various actions that are beyond the icons shown in the editors of a form.
"""

from camelot.core.orm import Entity, EntityBase

from sqlalchemy import orm
from typing import Generator

from ...core.qt import QtGui
from ...core.utils import ugettext_lazy as _
from ...admin.icon import Icon
from .base import EndpointAction, RenderHint
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


class EditFieldAction(EndpointAction):
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

    def get_endpoint(self, model_context):
        from vfinance.model.endpoint import Endpoint
        cls = model_context.obj.__class__
        if issubclass(cls, EntityBase):
            return Endpoint.get_or_raise(cls)

    def get_operation_targets(self, model_context) -> Generator[Entity, None, None]:
        yield model_context.admin.get_subsystem_object(model_context.obj)


class SelectObject(EditFieldAction):
    """Allows the user to select an object, and set the selected object as
    the new value of the editor"""

    icon = Icon('search') # 'tango/16x16/actions/system-search.png'
    tooltip = _('select existing')
    name = 'select_object'
    render_hint = RenderHint.TOOL_BUTTON

    def model_run(self, model_context, mode):
        from camelot.view import action_steps
        yield from super().model_run(model_context, mode)
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


class ToggleForeverAction(EditFieldAction):

    icon = Icon('calendar')
    tooltip = _('Forever')
    name = 'toggle_forever'
    render_hint = RenderHint.TOOL_BUTTON

    def model_run(self, model_context, mode):
        yield from super().model_run(model_context, mode)
        forever = model_context.field_attributes.get('forever')
        if forever is not None:
            if model_context.value == forever:
                model_context.admin.set_field_value(
                    model_context.obj, model_context.field, None
                )
            else:
                model_context.admin.set_field_value(
                    model_context.obj, model_context.field, forever
                )
            yield None

toggle_forever = ToggleForeverAction()

class OpenObject(SelectObject):
    """Open the value of an editor in a form view"""

    icon = Icon('folder-open') # 'tango/16x16/places/folder.png'
    tooltip = _('open')
    name = 'open_object'

    def model_run(self, model_context, mode):
        from camelot.view import action_steps
        yield from super().model_run(model_context, mode)
        obj = model_context.value
        # Disregard the case of having no value, or having multiple defined.
        if obj is not None and not isinstance(obj, list):
            admin = model_context.field_attributes['admin']
            admin = admin.get_related_admin(obj.__class__)
            yield action_steps.OpenFormView(obj, admin)

    def get_state(self, model_context):
        state = super().get_state(model_context)
        obj = model_context.value
        if state.enabled:
            state.enabled = (obj is not None and not isinstance(obj, list))
        return state

class ClearObject(EditFieldAction):
    """Set the new value of the editor to `None`"""

    icon = Icon('eraser') # 'tango/16x16/actions/edit-clear.png'
    tooltip = _('clear')
    name = 'clear_object'

    def model_run(self, model_context, mode):
        yield from super().model_run(model_context, mode)
        field_admin = model_context.field_attributes.get('admin')
        if field_admin is not None:
            model_context.admin.set_field_value(
                model_context.obj, model_context.field, None
            )
            yield None

    def get_state(self, model_context):
        state = super().get_state(model_context)
        state.visible = (model_context.value is not None)
        return state


class AddNewObject(EditFieldAction, AddNewObjectMixin):
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

    operation = 'CREATE'

    def model_run(self, model_context, mode):
        yield from super().model_run(model_context, mode)
        yield from super().add_new_object(model_context, mode)

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

    def get_endpoint(self, model_context):
        return self.get_default_admin(model_context).endpoint

    def get_authorization_messages(self, model_context) -> Generator[str, None, None]:
        from vfinance.data.types import crud_types
        if endpoint := self.get_endpoint(model_context):
            for instance in self.get_operation_targets(model_context):
                yield from endpoint.get_authorization_messages(crud_types[self.operation], parents=[instance])

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
        yield from super().model_run(model_context, mode)
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
