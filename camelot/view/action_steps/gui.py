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
import functools
import json
from typing import List, Tuple

from dataclasses import dataclass, field

from camelot.admin.action.base import ActionStep
from camelot.core.exception import CancelRequest
from camelot.core.utils import ugettext_lazy as _
from camelot.view.controls import editors
from camelot.view.controls.standalone_wizard_page import StandaloneWizardPage
from camelot.view.action_runner import hide_progress_dialog
from camelot.view.qml_view import qml_action_step
from ...core.qt import QtCore, QtWidgets, is_deleted
from ...core.serializable import DataclassSerializable


@dataclass
class Refresh( ActionStep, DataclassSerializable ):
    """Refresh all the open screens on the desktop, this will reload queries
    from the database"""

    @classmethod
    def gui_run(self, gui_context, serialized_step):
        if gui_context.workspace:
            gui_context.workspace.refresh()

class ItemSelectionDialog(StandaloneWizardPage):

    def __init__( self,
                  window_title=None,
                  autoaccept=False,
                  parent=None):
        """
        :param autoaccept: if True, the value of the ComboBox is immediately
        accepted after selecting it.
        """
        super(ItemSelectionDialog, self).__init__( window_title = window_title,
                                                   parent = parent )
        self.autoaccept = autoaccept
        self.set_default_buttons()
        layout = QtWidgets.QVBoxLayout()
        combobox = editors.ChoicesEditor(action_routes=[])
        combobox.setObjectName( 'combobox' )
        combobox.editingFinished.connect( self._combobox_activated )
        layout.addWidget( combobox )
        self.main_widget().setLayout(layout)

    @QtCore.qt_slot()
    def _combobox_activated(self):
        if self.autoaccept:
            self.accept()

    def set_choices(self, choices):
        combobox = self.findChild( QtWidgets.QWidget, 'combobox' )
        if combobox != None:
            combobox.set_choices(choices)

    def get_value(self):
        combobox = self.findChild( QtWidgets.QWidget, 'combobox' )
        if combobox != None:
            return combobox.get_value()

    def set_value(self, value):
        combobox = self.findChild( QtWidgets.QWidget, 'combobox' )
        if combobox != None:
            return combobox.set_value(value)

@dataclass
class SelectItem(ActionStep):
    """This action step pops up a single combobox dialog in which the user can
    select one item from a list of items.

    :param items: a list of tuples with values and the visible name of the items
       from which the user can select, such as `[(1, 'first'), (2,'second')]
    :param value: the value that should be selected when the dialog pops up
    :param autoaccept: if `True` the dialog closes immediately after the user
       selected an option.  When this is `False`, the user should press
       :guilabel:`OK` first.
    """

    items: List[Tuple]
    value: str = None

    title = _('Please select')
    subtitle = _('Make a selection and press the OK button')

    def __post_init__(self):
        self.autoaccept = True

    def render(self):
        dialog = ItemSelectionDialog( autoaccept = self.autoaccept )
        dialog.set_choices(self.items)
        dialog.set_value(self.value)
        dialog.setWindowTitle( str( self.title ) )
        dialog.set_banner_subtitle( str( self.subtitle ) )
        return dialog

    def gui_run(self, gui_context):
        dialog = self.render()
        result = dialog.exec()
        if result == QtWidgets.QDialog.DialogCode.Rejected:
            raise CancelRequest()
        return dialog.get_value()


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

    accept: bool = True

    @classmethod
    def gui_run( cls, gui_context, serialized_step ):
        if gui_context.context_id is None:
            # python implementation, still used for FormView
            step = json.loads(serialized_step)
            view = gui_context.view
            if view is not None and not is_deleted(view):
                view.close_view( step["accept"] )
        else:
            qml_action_step(gui_context, 'CloseView', serialized_step, keep_context_id=True)


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

    text: _
    icon: QtWidgets.QMessageBox.Icon = QtWidgets.QMessageBox.Icon.Information
    title: _ = _('Message')
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
    def render(cls, step):
        """create the message box. this method is used to unit test
        the action step."""
        message_box = QtWidgets.QMessageBox(QtWidgets.QMessageBox.Icon(step["icon"]),
                                            step["title"],
                                            step["text"],
                                            QtWidgets.QMessageBox.StandardButton(
                                                functools.reduce(lambda a, b: a | b, step["standard_buttons"])))
        message_box.setInformativeText(str(step["informative_text"]))
        message_box.setDetailedText(str(step["detailed_text"]))
        return message_box

    @classmethod
    def show_message_box(cls, step):
        message_box = cls.render(step)
        result = message_box.exec()
        if result == QtWidgets.QMessageBox.StandardButton.Cancel:
            raise CancelRequest()
        return result

    @classmethod
    def gui_run(cls, gui_context, serialized_step):
        step = json.loads(serialized_step)
        if step['hide_progress']:
            with hide_progress_dialog(gui_context):
                cls.show_message_box(step)
        else:
            cls.show_message_box(step)
