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

"""Helper classes to create unit tests for Actions."""

from sqlalchemy import orm

from ..core.qt import QtGui
from ..admin.action.list_action import ListActionGuiContext

class MockModelContext( object ):
    """Model Context to be used in unit tests
    
    :param session: the session attributed to this model context, if `None` is
        given, the session of the object is used.
    """
    
    def __init__( self, session=None ):
        self._model = []
        self.obj = None
        self.selection = []
        self.admin = None
        self.mode_name = None
        self.collection_count = 1
        self.selection_count = 1
        self.current_row = 0
        self.current_column = None
        self.current_field_name = None
        self.field_attributes = {}
        self._session = session
        
    def get_object( self ):
        return self.obj
        
    def get_selection( self, yield_per = None ):
        if self.obj is not None:
            return [self.obj]
        return self.selection

    def get_collection( self, yield_per = None ):
        return self.get_selection(yield_per=yield_per)

    @property
    def session( self ):
        return self._session or orm.object_session( self.obj )

class MockListActionGuiContext( ListActionGuiContext ):
    
    def __init__( self ):
        super(MockListActionGuiContext, self).__init__()
        self.item_view = QtGui.QTableWidget( 4, 4 )

