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

from ...core.qt import Qt, QtWidgets

from camelot.admin.action import ActionStep, Action
from camelot.admin.not_editable_admin import ReadOnlyAdminDecorator
from camelot.core.exception import CancelRequest
from camelot.core.utils import ugettext as _
from camelot.view.art import Icon
from camelot.view.action_runner import hide_progress_dialog
from camelot.view.controls.tableview import TableView

from .item_view import OpenTableView

class SetSelectedObjects(ActionStep):

    def __init__(self, objects):
        self.objects = objects

    def gui_run(self, gui_context):
        dialog = gui_context.view.parent()
        dialog.objects = self.objects
        dialog.accept()

class ConfirmSelection(Action):

    verbose_name = _('OK')
    icon = Icon('tango/16x16/emblems/emblem-symbolic-link.png')

    def model_run(self, model_context):
        yield SetSelectedObjects(list(model_context.get_selection()))

class CancelSelection(Action):

    verbose_name = _('Cancel')

    def gui_run(self, gui_context):
        gui_context.view.parent().reject()

class SelectAdminDecorator(ReadOnlyAdminDecorator):

    list_action = ConfirmSelection()

    def __init__(self, original_admin, show_subclasses):
        super(SelectAdminDecorator, self).__init__(original_admin)
        self.show_subclasses = show_subclasses

    def get_list_actions(self, *a, **kwa):
        return [CancelSelection(), ConfirmSelection()]
    
    
    def get_related_admin(self, cls):
        admin = self._original_admin.get_related_admin(cls)
        # this admin will end up in the model context of the next
        # step
        return admin
    
    def get_subclass_tree(self):
        new_subclasses = []
        if self.show_subclasses == True:
            subclasses = self._original_admin.get_subclass_tree()
            for admin, tree in subclasses:
                new_admin = SelectAdminDecorator(admin, True)
                new_subclasses.append([new_admin, new_admin.get_subclass_tree()])
        return new_subclasses

class SelectDialog(QtWidgets.QDialog):
    
    def __init__(self, gui_context, admin, search_text, parent = None):
        super( SelectDialog, self ).__init__( parent )
        layout = QtWidgets.QVBoxLayout()
        layout.setContentsMargins( 0, 0, 0, 0 )
        layout.setSpacing( 0 )
        self.setWindowTitle( _('Select %s') % admin.get_verbose_name() )
        self.setSizeGripEnabled(True)
        table = TableView(gui_context, admin, search_text=search_text, parent=self)
        table.setObjectName('table_view')
        layout.addWidget(table)
        self.setLayout( layout )
        self.objects = []
        self.setWindowState(Qt.WindowMaximized)

class SelectObjects( OpenTableView ):
    """Select one or more object from a query.  The `yield` of this action step
    return a list of objects.

    :param admin: a :class:`camelot.admin.object_admin.ObjectAdmin` object
    :param search_text: a default string on which to search for in the selection
        dialog
    :param value: a query or a list of object from which the selection should
        be made.  If none is given, the default query from the admin is taken.
    """

    def __init__(self, admin, search_text=None, value=None):
        show_subclasses = False
        if value is None:
            value = admin.get_query()
            # only able to construct subclass query whern
            # the default query is used
            show_subclasses = True
        select_admin = SelectAdminDecorator(admin, show_subclasses)
        super(SelectObjects, self).__init__(select_admin, value)
        self.search_text = search_text

    def render(self, gui_context):
        dialog = SelectDialog(gui_context, self.admin, self.search_text)
        table_view = dialog.findChild(QtWidgets.QWidget, 'table_view')
        table_view.set_subclass_tree(self.subclasses)
        self.update_table_view(table_view)
        return dialog

    def gui_run( self, gui_context ):
        dialog = self.render(gui_context)
        with hide_progress_dialog(gui_context):
            if dialog.exec_() == QtWidgets.QDialog.Rejected:
                raise CancelRequest()
            return dialog.objects


