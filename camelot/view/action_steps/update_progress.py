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

from dataclasses import dataclass
import json
import typing

from camelot.core.exception import CancelRequest
from camelot.core.qt import QtCore, QtWidgets, transferto
from camelot.core.utils import ugettext_lazy
from camelot.admin.action import ActionStep
from ...core.serializable import DataclassSerializable
from .. import gui_naming_context
from camelot.core.backend import cpp_action_step, is_cpp_gui_context_name


_detail_format = u'Update Progress {0:03d}/{1:03d} {2.text} {2.detail}'


@dataclass
class PushProgressLevel(ActionStep, DataclassSerializable):

    verbose_name: str
    blocking: bool = False

    @classmethod
    def gui_run(cls, gui_context_name, serialized_step):
        # @TODO : this needs to be handled in the action runner
        if is_cpp_gui_context_name(gui_context_name):
            cpp_action_step(gui_context_name, 'PushProgressLevel', serialized_step)
            return
        gui_context = gui_naming_context.resolve(gui_context_name)
        if gui_context is None:
            return
        progress_dialog = gui_context.get_progress_dialog()
        if progress_dialog is not None:
            step = json.loads(serialized_step)
            progress_dialog.push_level(step['verbose_name'])


@dataclass
class PopProgressLevel(ActionStep, DataclassSerializable):

    blocking: bool = False

    @classmethod
    def gui_run(cls, gui_context_name, serialized_step):
        # @TODO : this needs to be handled in the action runner
        if is_cpp_gui_context_name(gui_context_name):
            cpp_action_step(gui_context_name, 'PopProgressLevel', serialized_step)
            return
        gui_context = gui_naming_context.resolve(gui_context_name)
        if gui_context is None:
            return
        progress_dialog = gui_context.get_progress_dialog()
        if progress_dialog is not None:
            progress_dialog.pop_level()

@dataclass
class UpdateProgress(ActionStep, DataclassSerializable):
    """
Inform the user about the progress the application is making
while executing an action.  This ActionStep is not blocking.  So it can
be used inside transactions and will result in a minimum of delay when
yielded.  Each time an object is yielded, the progress dialog will be
updated.

.. image:: /_static/controls/progress_dialog.png

:param value: the current step
:param maximum: the maximum number of steps that will be executed. set it
    to 0 to display a busy indicator instead of a progres bar
:param text: the text to be displayed inside the progres bar
:param detail: the text to be displayed below the progres bar, this text is
    appended to the text already there
:param clear_details: clear the details text already there before putting 
    the new detail text.
:param title: the text to be displayed in the window's title bar
:param blocking: wait until the user presses `OK`, for example to review the
    details.
:param enlarge: increase the size of the window to two thirds of the screen,
    useful when there are a lot of details displayed.
"""

    value: typing.Optional[int] = None
    maximum: typing.Optional[int] = None
    text: typing.Union[str, ugettext_lazy, None] = None
    detail: typing.Union[str, ugettext_lazy, None] = None
    clear_details: bool = False
    title: typing.Union[str, ugettext_lazy, None] = None
    enlarge: bool = False
    blocking: bool = False
    cancelable: bool = True

    def __str__(self):
        return _detail_format.format(self.value or 0, self.maximum or 0, self)

    @classmethod
    def gui_run(cls, gui_context_name, serialized_step):
        """This method will update the progress dialog, if such dialog exists
        within the GuiContext
        
        :param gui_context: a :class:`camelot.admin.action.GuiContext` instance
        """
        # @TODO : this needs to be handled in the action runner
        if is_cpp_gui_context_name(gui_context_name):
            # C++ QmlProgressDialog
            response = cpp_action_step(gui_context_name, 'UpdateProgress', serialized_step)
            if response['was_canceled']:
                # reset progress dialog
                reset_step = QtCore.QByteArray(json.dumps({ 'reset': True }).encode())
                cpp_action_step(gui_context_name, 'UpdateProgress', reset_step)
                raise CancelRequest()
            return
        gui_context = gui_naming_context.resolve(gui_context_name)
        if gui_context is None:
            return
        progress_dialog = gui_context.get_progress_dialog()
        if progress_dialog:
            if isinstance(progress_dialog, QtWidgets.QProgressDialog):
                step = json.loads(serialized_step)
                # QProgressDialog
                if step["maximum"] is not None:
                    progress_dialog.setMaximum(step["maximum"])
                if step["value"] is not None:
                    progress_dialog.setValue(step["value"])
                progress_dialog.set_cancel_hidden(not step["cancelable"])
                if step["text"] is not None:
                    progress_dialog.setLabelText(step["text"])
                if step["clear_details"] is True:
                    progress_dialog.clear_details()
                if step["detail"] is not None:
                    progress_dialog.add_detail(step["detail"])
                if step["title"] is not None:
                    progress_dialog.title = step["title"]
                if step["enlarge"]:
                    progress_dialog.enlarge()
                if step["blocking"]:
                    progress_dialog.set_ok_hidden(False)
                    progress_dialog.set_cancel_hidden(True)
                    progress_dialog.exec()
                    # https://vfinance.atlassian.net/browse/VFIN-1844
                    transferto(progress_dialog, progress_dialog)
                    progress_dialog.set_ok_hidden(True)
                    progress_dialog.set_cancel_hidden(False)
                if progress_dialog.wasCanceled():
                    progress_dialog.reset()
                    raise CancelRequest()

@dataclass
class SetProgressAnimate(ActionStep, DataclassSerializable):

    animate: bool
