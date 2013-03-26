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
"""
Helper classes for reloading parts of the application when the
source code has changed.

This module contains the singleton `auto_reload` object whose `reload` slot
will be emitted when the application needs to be reloaded.
"""

import logging
import sys

from PyQt4 import QtCore

from sqlalchemy import event

LOGGER = logging.getLogger( 'camelot.core.auto_reload' )

class AutoReloadEvents( event.Events ):
    """Devinition of AutoReloadEvents
    """
    
    def before_reload( self ):
        """Before the reload is triggered, use this event to properly clear
        resources"""
        
    def after_reload( self ):
        """After the reload of the modules has happened, reconstruct.
        """
    
class AutoReload( QtCore.QFileSystemWatcher ):
    """Monitors the source code and emits the `reload` signal whenever
    the source code has changed and the model thread was restarted.
    """
    
    dispatch = event.dispatcher( AutoReloadEvents )
    
    reload = QtCore.pyqtSignal()

    def __init__( self, parent = None ):
        super( AutoReload, self ).__init__( None )
        self.fileChanged.connect( self.source_changed )
        self.directoryChanged.connect( self.source_changed )

    @QtCore.pyqtSlot( str )
    def source_changed( self, changed ):
        LOGGER.warn( u'%s changed, reload application'%changed )
        for fn in self.dispatch.before_reload:
            fn()
        #
        # reload previously imported modules
        #
        from types import ModuleType
        for name, module in sys.modules.items():
            if not isinstance( module, ModuleType ):
                continue
            if not name.startswith( 'camelot' ):
                continue
            print name
            reload( module )
        self.reload.emit()
        
auto_reload = AutoReload()

