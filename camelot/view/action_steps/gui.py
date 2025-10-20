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

"""
Various ``ActionStep`` subclasses that manipulate the GUI of the application.
"""

import traceback
import typing
from dataclasses import dataclass, field
from io import StringIO
from typing import List, Union

from camelot.admin.action.base import ActionStep
from camelot.admin.icon import Icon
from camelot.core.exception import UserException
from camelot.core.naming import initial_naming_context
from camelot.core.utils import ugettext_lazy, ugettext_lazy as _
from .crud import CompletionValue
from ...core.qt import QtWidgets
from ...core.serializable import DataclassSerializable


@dataclass
class Refresh( ActionStep, DataclassSerializable ):
    """Refresh all the open screens on the desktop, this will reload queries
    from the database"""

    blocking: bool = False


@dataclass
class SelectItem(ActionStep, DataclassSerializable):
    """This action step pops up a single combobox dialog in which the user can
    select one item from a list of items.

    :param items: a list of tuples with values and the visible name of the items
       from which the user can select, such as `[(1, 'first'), (2,'second')]
    :param value: the value that should be selected when the dialog pops up
    :param autoaccept: if `True` the dialog closes immediately after the user
       selected an option.  When this is `False`, the user should press
       :guilabel:`OK` first.
    """

    items: List[CompletionValue]
    value: str = initial_naming_context._bind_object(None)
    autoaccept: bool = True

    title: Union[str, ugettext_lazy] = field(default_factory=lambda: _('Please select'))
    subtitle: Union[str, ugettext_lazy] = field(default_factory=lambda: _('Make a selection and press the OK button.'))

    @classmethod
    def deserialize_result(cls, gui_context_name, result):
        if result is not None:
            return tuple(result)

@dataclass
class CloseView(ActionStep, DataclassSerializable):
    """
    Close the view that triggered the action, if such a view is available.

    :param accept: a boolean indicating if the view's widget should accept the
        close event.  This defaults to :const:`True`, when this is set to
        :const:`False`, the view will trigger it's corresponding close action
        instead of accepting the close event.  The close action might involve
        validating if the view can be closed, or requesting confirmation from
        the user.
    """

    blocking: bool = False
    accept: bool = True


@dataclass
class MessageBox( ActionStep, DataclassSerializable ):
    """
    Popup a :class:`QtWidgets.QMessageBox` and send it result back.  The arguments
    of this action are the same as those of the :class:`QtWidgets.QMessageBox`
    constructor.

    :param text: the text to be displayed within the message box
    :param icon: one of the :class:`QtWidgets.QMessageBox.Icon` constants
    :param title: the window title of the message box
    :param standard_buttons: the buttons to be displayed on the message box,
        out of the :class:`QtWidgets.QMessageBox.StandardButton` enumeration. by
        default an :guilabel:`Ok` and a button :guilabel:`Cancel` will be shown.

    When the :guilabel:`Cancel` button is pressed, this action step will raise
    a :class:`camelot.core.exception.CancelRequest`

    .. image:: /_static/listactions/import_from_file_confirmation.png

    """

    text: typing.Union[str, ugettext_lazy]
    icon: Icon = field(default_factory=lambda: Icon('info'))
    title: typing.Union[str, ugettext_lazy] = field(default_factory=lambda: _('Message'))
    standard_buttons: list = field(default_factory=lambda: [QtWidgets.QMessageBox.StandardButton.Ok, QtWidgets.QMessageBox.StandardButton.Cancel])
    informative_text: str = field(init=False)
    detailed_text: str = field(init=False)
    hide_progress: bool = False

    def __post_init__(self):
        self.title = str(self.title)
        self.text = str(self.text)
        self.informative_text = ''
        self.detailed_text = ''

    @classmethod
    def deserialize_result(cls, gui_context_name, result):
        # the result might be empty in case step was send as non-blocking
        button = result.get("button")
        if button is None:
            return
        return QtWidgets.QMessageBox.StandardButton(button)

    @classmethod
    def from_exception(cls, logger, text, exception):
        """
        Turn an exception in a MessageBox action step
        """
        if isinstance(exception, UserException):
            # this exception is not supposed to generate any logging
            # or inform the developer about something
            step = cls(
                title=exception.title,
                text=exception.text,
                icon=exception.icon,
                standard_buttons=[QtWidgets.QMessageBox.StandardButton.Ok,],
            )
            step.informative_text=exception.resolution
            step.detailed_text=exception.detail
        else:
            logger.error(text, exc_info=exception)
            sio = StringIO()
            traceback.print_exc(file=sio)
            step = cls(
                title=_('Exception'),
                text=_('An unexpected event occurred'),
                icon=None,
                standard_buttons=[QtWidgets.QMessageBox.StandardButton.Ok,],
            )
            # chop the size of the text to prevent error dialogs larger than the screen
            step.informative_text=str(exception)[:1000]
            step.detailed_text=sio.getvalue()
            sio.close()
        return step
