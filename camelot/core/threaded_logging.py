"""
Logging is an important aspect of every application, as logs provide valuable
feedback to developers and first line support.  Camelot adds some
additional functions on top of the standard Python logging library.

The added functionallity is needed for two reasons :
    
    * Camelot applications are often installed in a distributed fashion.  Thus
      the log files need to be collected to provide meaningfull information to
      the developer.
      
    * Logging should never slow down/freeze the application.  Even when logging
      to files this may happen, since the application never knows for sure if
      a file is really local, and network connections may turn slow at any
      time.

Both issues are resolved by using a logging handler that collects all logs, and
periodically sends them to an http server::
    
    handler = ThreadedHttpHandler('www.example.com:80', '/my_logs/')
    handler.setLevel(logging.INFO)
    logging.root.addHandler(handler)

The logging url could include a part indentifying the user and as such assisting
first line support.
"""

from PyQt4 import QtCore

import logging
from logging import handlers

logger = logging.getLogger('camelot.core.logging')

class ThreadedTimer( QtCore.QThread ):
    """Thread that checks every interval milli seconds if there 
    are logs to be sent to the server"""

    def __init__(self, interval, handler):
        QtCore.QThread.__init__(self)
        self._timer = None
        self._interval = interval
        self._handler = handler

    def run(self):
        self._timer = QtCore.QTimer()
        self._timer.timeout.connect( self._handler.timeout )
        self._timer.start(self._interval)
        self.exec_()

class ThreadedHttpHandler(handlers.HTTPHandler):
    """An Http Logging handler that does the logging itself in a different 
    thread, to prevent slow down of the main thread"""

    def __init__(self, host, url, method='GET'):
        handlers.HTTPHandler.__init__(self, host, url, method)
        self._records_to_emit = []
        self._threaded_timer = ThreadedTimer(1000, self)
        self._threaded_timer.start()

    def timeout(self):
        while len(self._records_to_emit):
            record = self._records_to_emit.pop()
            handlers.HTTPHandler.emit(self, record)

    def emit(self, record):
        self._records_to_emit.append(record)
