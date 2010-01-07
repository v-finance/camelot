'''
Created on Sep 12, 2009

@author: tw55413
'''

import logging
logger = logging.getLogger('camelot.view.model_thread.no_thread_model_thread')

from signal_slot_model_thread import AbstractModelThread, setup_model

class NoThreadModelThread(AbstractModelThread):

    def __init__(self, setup_thread = setup_model ):
        self.responses = []
        AbstractModelThread.__init__(self, setup_thread = setup_model )
        self._setup_thread()

    def start(self):
        pass

    def post( self, request, response = None, exception = None ):
        try:
            result = request()
            response( result )
        except Exception, e:
            if exception:
                logger.error( 'exception caught in model thread while executing %s'%self._name, exc_info = e )
                import traceback, cStringIO
                sio = cStringIO.StringIO()
                traceback.print_exc(file=sio)
                traceback_print = sio.getvalue()
                sio.close()
                exception_info = (e, traceback_print)
                exception(exception_info)

    def wait_on_work(self):
        from PyQt4 import QtCore
        app = QtCore.QCoreApplication.instance()
        while app.hasPendingEvents():
            app.processEvents()
            
    def isRunning(self):
        return True
