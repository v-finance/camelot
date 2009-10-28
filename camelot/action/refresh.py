#  ==================================================================================
#
#  Copyright (C) 2007-2008 Conceptive Engineering bvba. All rights reserved.
#  www.conceptive.be / project-camelot@conceptive.be
#
#  This file is part of the Camelot Library.
#
#  This file may be used under the terms of the GNU General Public
#  License version 2.0 as published by the Free Software Foundation
#  and appearing in the file LICENSE.GPL included in the packaging of
#  this file.  Please review the following information to ensure GNU
#  General Public Licensing requirements will be met:
#  http://www.trolltech.com/products/qt/opensource.html
#
#  If you are unsure which license is appropriate for your use, please
#  review the following information:
#  http://www.trolltech.com/products/qt/licensing.html or contact
#  project-camelot@conceptive.be.
#
#  This file is provided AS IS with NO WARRANTY OF ANY KIND, INCLUDING THE
#  WARRANTY OF DESIGN, MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE.
#
#  For use of this library in commercial applications, please contact
#  project-camelot@conceptive.be
#
#  ==================================================================================

"""The action module contains various QAction classes, representing commands that
can be invoked via menus, toolbar buttons, and keyboard shortcuts."""

from PyQt4.QtCore import Qt
from PyQt4 import QtGui, QtCore

from camelot.view.art import Icon
from camelot.view.model_thread import post

import logging
logger = logging.getLogger( 'camelot.action.refresh' )

class SessionRefresh( QtGui.QAction ):
    """Session refresh expires all objects in the current session and sends
    a local entity update signal via the remote_signals mechanism"""

    def __init__( self, parent ):
        super( SessionRefresh, self ).__init__( 'Refresh', parent )
        self.setShortcut( Qt.Key_F9 )
        self.setIcon( Icon( 'tango/16x16/actions/view-refresh.png' ).getQIcon() )
        self.connect( self, QtCore.SIGNAL( 'triggered(bool)' ), self.sessionRefresh )
        from camelot.view.remote_signals import get_signal_handler
        self.signal_handler = get_signal_handler()

    def refreshed(self, refreshed_objects ):
        for o in refreshed_objects:
            self.signal_handler.sendEntityUpdate( self, o )

    def sessionRefresh( self, checked ):
        logger.debug( 'session refresh requested' )

        def refresh_objects():
            from elixir import session
            refreshed_objects = []

            for _key, value in session.identity_map.items():
                session.refresh( value )
                refreshed_objects.append( value )

            return refreshed_objects


        post( refresh_objects, self.refreshed)
