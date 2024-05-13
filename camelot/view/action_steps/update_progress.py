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

import logging
import typing

from camelot.core.utils import ugettext_lazy
from camelot.admin.action import ActionStep
from ...core.serializable import DataclassSerializable
from camelot.core.backend import cpp_action_step


_detail_format = u'Update Progress {0:03d}/{1:03d} {2.text} {2.detail}'


@dataclass
class PushProgressLevel(ActionStep, DataclassSerializable):

    verbose_name: str
    blocking: bool = False

    @classmethod
    def gui_run(cls, gui_context_name, serialized_step):
        # Always send to C++ (even if gui_context_name comes from python)
        cpp_action_step(gui_context_name, 'PushProgressLevel', serialized_step)


@dataclass
class PopProgressLevel(ActionStep, DataclassSerializable):

    blocking: bool = False

    @classmethod
    def gui_run(cls, gui_context_name, serialized_step):
        # Always send to C++ (even if gui_context_name comes from python)
        cpp_action_step(gui_context_name, 'PopProgressLevel', serialized_step)


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
:param detail_level: maps to the loglevels from the logging module and indicates the cause for the message.
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
    detail_level: int = logging.INFO # To be determined - we currently map to the loglevels from the logging module

    def __str__(self):
        return _detail_format.format(self.value or 0, self.maximum or 0, self)

    @classmethod
    def gui_run(cls, gui_context_name, serialized_step):
        # Always send to C++ (even if gui_context_name comes from python)
        return cpp_action_step(gui_context_name, 'UpdateProgress', serialized_step)

@dataclass
class SetProgressAnimate(ActionStep, DataclassSerializable):

    animate: bool
