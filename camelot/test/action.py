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

"""Helper classes to create unit tests for Actions."""

from PyQt4 import QtGui

from camelot.admin.action.list_action import ListActionGuiContext

class MockModelContext( object ):
    """Model Context to be used in unit tests
    """
    
    def __init__( self ):
        self.obj = None
        self.admin = None
        
    def get_object( self ):
        return self.obj
        
    def get_selection( self ):
        return [self.obj]

    def get_collection( self ):
        return [self.obj]

    @property
    def session( self ):
        from sqlalchemy.orm.session import object_session
        return object_session( self.obj )

class MockListActionGuiContext( ListActionGuiContext ):
    
    def __init__( self ):
        super(MockListActionGuiContext, self).__init__()
        self.item_view = QtGui.QTableWidget( 4, 4 )

