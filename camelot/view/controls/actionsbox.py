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

"""Actions box"""

import logging
LOGGER = logging.getLogger('controls.actionsbox')

from PyQt4 import QtGui

class ActionsBox( QtGui.QWidget ):
    """A box containing actions to be applied to a view

    :param gui_context: a :class:`camelot.admin.action.base.GuiContext` object
    :param parent: a :class:`PyQt4.QtGui.QWidget` object
    
    """

    def __init__( self, gui_context, parent ):
        LOGGER.debug( 'create actions box' )
        super( ActionsBox, self ).__init__( parent )
        self.gui_context = gui_context

    def set_actions( self, actions ):
        LOGGER.debug( 'setting actions' )
        layout = QtGui.QVBoxLayout()
        layout.setSpacing( 2 )
        for action in actions:
            action_widget = action.render( self.gui_context, self )
            layout.addWidget( action_widget )
        self.setLayout( layout )

