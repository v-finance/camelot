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



from camelot.admin.icon import Icon
from camelot.admin.action.base import Action
from camelot.core.qt import QtGui, QtWidgets
from camelot.core.utils import ugettext as _

from .base import RenderHint

class CloseForm( Action ):
    """Validte the form can be closed, and close it"""

    render_hint = RenderHint.CLOSE_BUTTON
    shortcut = QtGui.QKeySequence.StandardKey.Close
    icon = Icon('times-circle') # 'tango/16x16/actions/system-log-out.png'
    verbose_name = _('Close')
    tooltip = _('Close this form')
    name = 'close_form'
    
    def step_when_valid(self):
        """
        :return: the `ActionStep` to take when the current object is valid
        """
        from camelot.view import action_steps
        return action_steps.CloseView()

    def model_run( self, model_context, mode ):
        from camelot.view import action_steps
        yield action_steps.UpdateProgress( text = _('Closing form') )
        validator = model_context.admin.get_validator()
        obj = model_context.get_object()
        admin  = model_context.admin
        subsystem_obj = admin.get_subsystem_object(obj)
        if obj is None:
            yield self.step_when_valid()
            return
        #
        # validate the object, and if the object is valid, simply close
        # the view
        #
        messages = validator.validate_object( obj )
        valid = ( len( messages ) == 0 )
        if valid:
            yield self.step_when_valid()
        else:
            #
            # if the object is not valid, request the user what to do
            #
            message = action_steps.MessageBox(
                '\n'.join( messages ),
                Icon('recycle'),
                _('Invalid form'),
                [QtWidgets.QMessageBox.StandardButton.Ok, QtWidgets.QMessageBox.StandardButton.Discard] )
            reply = yield message
            if reply == QtWidgets.QMessageBox.StandardButton.Discard:
                if admin.is_persistent( obj ):
                    admin.refresh( obj )
                    yield action_steps.UpdateObjects((subsystem_obj,))
                else:
                    depending_objects = list(admin.get_depending_objects(obj))
                    model_context.proxy.remove(obj)
                    yield action_steps.DeleteObjects((subsystem_obj,))
                    admin.expunge(obj)
                    yield action_steps.UpdateObjects(depending_objects)
                # only close the form after the object has been discarded or
                # deleted, to avoid yielding action steps after the widget mapper
                # has been garbage collected
                yield self.step_when_valid()

close_form = CloseForm()
