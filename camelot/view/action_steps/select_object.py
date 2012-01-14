#  ============================================================================
#
#  Copyright (C) 2007-2012 Conceptive Engineering bvba. All rights reserved.
#  www.conceptive.be / project-camelot@conceptive.be
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
#  visit www.python-camelot.com or contact project-camelot@conceptive.be
#
#  This file is provided AS IS with NO WARRANTY OF ANY KIND, INCLUDING THE
#  WARRANTY OF DESIGN, MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE.
#
#  For use of this library in commercial applications, please contact
#  project-camelot@conceptive.be
#
#  ============================================================================

from PyQt4 import QtCore, QtGui

from camelot.admin.action import ActionStep
from camelot.core.exception import CancelRequest
from camelot.core.utils import ugettext as _

class SelectDialog( QtGui.QDialog ):
    
    def __init__( self, admin, query, parent = None ):
        super( SelectDialog, self ).__init__( parent )
        layout = QtGui.QVBoxLayout()
        layout.setContentsMargins( 0, 0, 0, 0 )
        layout.setSpacing( 0 )
        self.setWindowTitle( _('Select %s') % admin.get_verbose_name() )
        select = admin.create_select_view(
            query,
            parent = self,
            search_text = u''
        )
        layout.addWidget( select )
        self.setLayout( layout )
        self.object_getter = None
        select.entity_selected_signal.connect( self.object_selected )
        
    @QtCore.pyqtSlot(object)
    def object_selected( self, object_getter ):
        self.object_getter = object_getter
        self.accept()

class SelectObject( ActionStep ):
    """Select an object from a list
    
    :param admin: a :class:`camelot.admin.object_admin.ObjectAdmin` object
    """
    
    def __init__( self, admin ):
        self.admin = admin
        self.query = admin.get_query()
        
    def gui_run( self, gui_context ):
        select_dialog = SelectDialog( self.admin, self.query )
        select_dialog.exec_()
        if select_dialog.object_getter:
            return select_dialog.object_getter
        raise CancelRequest()

