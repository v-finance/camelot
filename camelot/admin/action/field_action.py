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
editing a single field on a form or in a table.
"""

from PyQt4.QtCore import Qt

from ...core.utils import ugettext_lazy as _
from ...view.art import Icon
from .base import Action
from .application_action import (ApplicationActionModelContext,
                                 ApplicationActionGuiContext)


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
    """

    def __init__(self):
        super( FieldActionModelContext, self ).__init__()
        self.obj = None
        self.field = None
        self.value = None

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
        return context

    def copy( self, base_class = None ):
        new_context = super( FieldActionGuiContext, self ).copy( base_class )
        new_context.editor = self.editor
        return new_context

class SelectObject(Action):
    """Allows the user to select an object, and set the selected object as
    the new value of the editor"""

    icon = Icon('tango/16x16/actions/system-search.png')
    tooltip = _('select existing')

    def render( self, gui_context, parent ):
        from ...view.controls.action_widget import ActionToolbutton
        button = ActionToolbutton(self, gui_context, parent)
        button.setAutoRaise(True)
        button.setFocusPolicy(Qt.ClickFocus)
        return button

    def model_run(self, model_context):
        from camelot.view import action_steps
        selected_objects = yield action_steps.SelectObjects(model_context.admin)
        for selected_object in selected_objects:
            yield action_steps.UpdateEditor('selected_object', selected_object)
            break

    def get_state(self, model_context):
        state = super(SelectObject, self).get_state(model_context)
        state.visible = (model_context.value is None)
        return state

class NewObject(SelectObject):
    """Open a form for the creation of a new object, and set this
    object as the new value of the editor"""

    icon = Icon('tango/16x16/actions/document-new.png')
    tooltip = _('create new')

    def model_run(self, model_context):
        from camelot.view import action_steps
        admin = yield action_steps.SelectSubclass(model_context.admin)
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
            admin = model_context.admin.get_related_admin(obj.__class__)
            yield action_steps.OpenFormView([obj], admin)

    def get_state(self, model_context):
        state = super(OpenObject, self).get_state(model_context)
        state.visible = (model_context.value is not None)
        return state

class ClearObject(OpenObject):
    """Set the new value of the editor to `None`"""

    icon = Icon('tango/16x16/actions/edit-clear.png')
    tooltip = _('clear')

    def model_run(self, model_context):
        from camelot.view import action_steps
        yield action_steps.UpdateEditor('selected_object', None)