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

from ...core.qt import QtCore, QtWidgets, is_deleted

import six

from camelot.admin.action.base import ActionStep
from camelot.core.exception import CancelRequest
from camelot.core.utils import ugettext, ugettext_lazy as _
from camelot.view.controls import editors
from camelot.view.controls.standalone_wizard_page import StandaloneWizardPage

class UpdateEditor(ActionStep):
    """This step should be used in the context of an editor action.  It
    will update an attribute of the editor.

    :param attribute: the name of the attribute of the editor to update
    :param value: the new value of the attribute
    :param propagate: set to `True` if the editor should notify the underlying
       model of it's change, so that the changes can be written to the model
    """

    def __init__(self, attribute, value, propagate=False):
        self.attribute = attribute
        self.value = value
        self.propagate = propagate

    def gui_run(self, gui_context):
        if is_deleted(gui_context.editor):
            return
        setattr(gui_context.editor, self.attribute, self.value)
        if self.propagate:
            gui_context.editor.editingFinished.emit()


class Refresh( ActionStep ):
    """Refresh all the open screens on the desktop, this will reload queries
    from the database"""

    def gui_run( self, gui_context ):
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
        combobox = editors.ChoicesEditor()
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

    def __init__( self, items, value=None ):
        self.items = items
        self.value = value
        self.autoaccept = True
        self.title =  _('Please select')
        self.subtitle = _('Make a selection and press the OK button')

    def render(self):
        dialog = ItemSelectionDialog( autoaccept = self.autoaccept )
        dialog.set_choices(self.items)
        dialog.set_value(self.value)
        dialog.setWindowTitle( six.text_type( self.title ) )
        dialog.set_banner_subtitle( six.text_type( self.subtitle ) )
        return dialog

    def gui_run(self, gui_context):
        dialog = self.render()
        result = dialog.exec_()
        if result == QtWidgets.QDialog.Rejected:
            raise CancelRequest()
        return dialog.get_value()

class SelectSubclass(SelectItem):
    """Allow the user to select a subclass out of a class hierarchy.  If the
    hierarch has only one class, this step returns immediately.

    :param admin: a :class:`camelot.admin.object_admin.ObjectAdmin` object

    yielding this step will return the admin for the subclass selected by the
    user.
    """

    def __init__(self, admin):
        self.admin = admin
        items = []
        self._append_subclass_tree_to_items(items, admin.get_subclass_tree())
        super().__init__(items)

    def _append_subclass_tree_to_items(self, items, subclass_tree):
        for admin, tree in subclass_tree:
            if len(tree):
                self._append_subclass_tree_to_items(items, tree)
            else:
                items.append((admin, admin.get_verbose_name_plural()))

    def gui_run(self, gui_context):
        if not len(self.items):
            return self.admin
        return super().gui_run(gui_context)


class CloseView( ActionStep ):
    """
    Close the view that triggered the action, if such a view is available.

    :param accept: a boolean indicating if the view's widget should accept the
        close event.  This defaults to :const:`True`, when this is set to
        :const:`False`, the view will trigger it's corresponding close action
        instead of accepting the close event.  The close action might involve
        validating if the view can be closed, or requesting confirmation from
        the user.
    """

    def __init__( self, accept = True ):
        self.accept = accept

    def gui_run( self, gui_context ):
        view = gui_context.view
        if view != None:
            view.close_view( self.accept )

class MessageBox( ActionStep ):
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

    default_buttons = QtWidgets.QMessageBox.Ok | QtWidgets.QMessageBox.Cancel

    def __init__( self,
                  text,
                  icon = QtWidgets.QMessageBox.Information,
                  title = _('Message'),
                  standard_buttons = default_buttons ):
        self.icon = icon
        self.title = six.text_type( title )
        self.text = six.text_type( text )
        self.standard_buttons = standard_buttons
        self.informative_text = ''
        self.detailed_text = ''

    def render( self ):
        """create the message box. this method is used to unit test
        the action step."""
        message_box =  QtWidgets.QMessageBox( self.icon,
                                          self.title,
                                          self.text,
                                          self.standard_buttons )
        message_box.setInformativeText(six.text_type(self.informative_text))
        message_box.setDetailedText(six.text_type(self.detailed_text))
        return message_box

    def gui_run( self, gui_context ):
        message_box = self.render()
        result = message_box.exec_()
        if result == QtWidgets.QMessageBox.Cancel:
            raise CancelRequest()
        return result


