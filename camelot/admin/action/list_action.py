#  ============================================================================
#
#  Copyright (C) 2007-2011 Conceptive Engineering bvba. All rights reserved.
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

"""
This is part of a test implementation of the new actions draft, it is not
intended for production use
"""

from ApplicationAction import ApplicationActionGuiContext

class ListActionGuiContext( ApplicationActionGuiContext ):
    """The context for an :class:`ListAction`.  On top of the attributes
    of the :class:`camelot.admin.action.application_action.ApplicationActionGuiContext`, this context contains :
    
    .. attribute:: selection_model
    
       the :class:`QtGui.QItemSelectionModel` class that relates to the table 
       view on which the widget will be placed.
       
    .. attribute:: admin
    
       the admin object used to for the table view.
    """
    
    def __init__( self ):
        super( ListActionGuiContext, self ).__init__()
        self.workspace = None
        self.admin = None
        self.selection_model = None
