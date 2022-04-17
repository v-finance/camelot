#  ============================================================================
#
#  Copyright (C) 2007-2016 Conceptive Engineering bvba.
#  www.conceptive.be / info@conceptive.be
#
#  Redistribution and use in source and binary forms, with or without
#  modification, are permitted provided that the following conditions are met:
#      * Redistributions of source code must retain the above copyright
#        notice, this list of conditions and the following disclaimer.
#      * Redistributions in binary form must reproduce the above copyright
#        notice, this list of conditions and the following disclaimer in the
#        documentation and/or other materials provided with the distribution.
#      * Neither the name of Conceptive Engineering nor the
#        names of its contributors may be used to endorse or promote products
#        derived from this software without specific prior written permission.
#  
#  THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
#  ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
#  WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
#  DISCLAIMED. IN NO EVENT SHALL <COPYRIGHT HOLDER> BE LIABLE FOR ANY
#  DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
#  (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
#  LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
#  ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
#  (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
#  SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#
#  ============================================================================
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
periodically sends them to an http server in the background::
    
    handler = ThreadedHttpHandler('www.example.com:80', '/my_logs/')
    handler.setLevel(logging.INFO)
    logging.root.addHandler(handler)

The logging url could include a part indentifying the user and as such assisting
first line support.
"""

from .qt import QtCore

import logging

LOGGER = logging.getLogger('camelot.core.logging')

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
        self.exec()

class ThreadedHandler(logging.Handler):
    """A threaded Logging handler that does the logging itself in a different 
    thread, to prevent slow down of the main thread.
    
    :param handler: the handler to send the logs to
    """

    def __init__(self, handler):
        super(ThreadedHandler, self).__init__()
        self.handler = handler
        self._records_to_emit = []
        self._threaded_timer = ThreadedTimer(1000, self)
        self._threaded_timer.start()

    @QtCore.qt_slot()
    def timeout(self):
        while len(self._records_to_emit):
            record = self._records_to_emit.pop()
            self.handler.emit(record)

    def emit(self, record):
        self._records_to_emit.append(record)

