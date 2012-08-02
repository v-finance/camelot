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
