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
import logging
import gc

from PyQt4 import QtCore

LOGGER = logging.getLogger('camelot.view.model_thread.garbage_collector')

class GarbageCollector(QtCore.QObject):
    """
    Disable automatic garbage collection and instead collect manually
    every INTERVAL milliseconds.

    This is done to ensure that garbage collection only happens in the GUI
    thread, as otherwise Qt can crash.
    
    This code is serves as a workaround for a bug in PyQt:
    
    
    and is modeled after the original code of Kovid Goyal
    """

    INTERVAL = 5000

    def __init__(self, parent, debug=False):
        super( GarbageCollector, self ).__init__( parent )
        self._threshold = gc.get_threshold()
        self._debug = debug
        self.destroyed.connect( self._destroyed )
        gc.disable()
        timer = QtCore.QTimer(self)
        timer.timeout.connect(self._check)
        timer.start( self.INTERVAL )

    @QtCore.pyqtSlot()
    def _destroyed( self ):
        LOGGER.debug( 'custom garbage collector destroyed' )
        
    @QtCore.pyqtSlot()
    def _check(self):
        l0, l1, l2 = gc.get_count()
        if self._debug:
            LOGGER.debug( 'gc_check called : %s %s %s'%( l0, l1, l2 ) )
        if l0 > self._threshold[0]:
            num = gc.collect(0)
            if self._debug:
                LOGGER.debug('collecting gen 0, found: %s unreachable'%num)
            if l1 > self._threshold[1]:
                num = gc.collect(1)
                if self._debug:
                    LOGGER.debug('collecting gen 1, found: %s unreachable'%num)
                if l2 > self._threshold[2]:
                    num = gc.collect(2)
                    if self._debug:
                        LOGGER.debug('collecting gen 2, found: %s unreachable'%num)

