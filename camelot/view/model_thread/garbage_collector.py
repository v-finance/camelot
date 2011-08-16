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
