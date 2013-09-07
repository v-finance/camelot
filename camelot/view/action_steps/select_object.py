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

from PyQt4 import QtGui
from PyQt4.QtCore import Qt

from camelot.admin.action import ActionStep, Action
from camelot.admin.not_editable_admin import ReadOnlyAdminDecorator
from camelot.core.exception import CancelRequest
from camelot.core.utils import ugettext as _
from camelot.view.art import Icon
from camelot.view.action_runner import hide_progress_dialog
from camelot.view.controls.tableview import TableView

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

    def get_list_actions(self, *a, **kwa):
        return [CancelSelection(), ConfirmSelection()]

class SelectDialog(QtGui.QDialog):
    
    def __init__(self, gui_context, admin, search_text, parent = None):
        super( SelectDialog, self ).__init__( parent )
        layout = QtGui.QVBoxLayout()
        layout.setContentsMargins( 0, 0, 0, 0 )
        layout.setSpacing( 0 )
        self.setWindowTitle( _('Select %s') % admin.get_verbose_name() )
        self.setSizeGripEnabled(True)
        table = TableView(gui_context, admin, search_text=search_text, parent=self)
        layout.addWidget(table)
        self.setLayout( layout )
        self.objects = []
        self.setWindowState(Qt.WindowMaximized)

class SelectObjects( ActionStep ):
    """Select one or more object from a query.  The `yield` of this action step
    return a list of objects.

    :param admin: a :class:`camelot.admin.object_admin.ObjectAdmin` object
    :param search_text: a default string on which to search for in the selection
        dialog
    """

    def __init__(self, admin, search_text=None):
        self.admin = SelectAdminDecorator(admin)
        self.search_text = search_text

    def render(self, gui_context):
        return SelectDialog(gui_context, self.admin, self.search_text)

    def gui_run( self, gui_context ):
        dialog = self.render(gui_context)
        with hide_progress_dialog(gui_context):
            if dialog.exec_() == QtGui.QDialog.Rejected:
                raise CancelRequest()
            return dialog.objects

