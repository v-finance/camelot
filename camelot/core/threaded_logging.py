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

from PyQt4 import QtCore

import getpass
import logging
from logging import handlers
import sys

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
        self.exec_()

class ThreadedHttpHandler(handlers.HTTPHandler):
    """An Http Logging handler that does the logging itself in a different 
    thread, to prevent slow down of the main thread"""

    def __init__(self, host, url, method='GET'):
        handlers.HTTPHandler.__init__(self, host, url, method)
        self._records_to_emit = []
        self._threaded_timer = ThreadedTimer(1000, self)
        self._threaded_timer.start()

    @QtCore.pyqtSlot()
    def timeout(self):
        while len(self._records_to_emit):
            record = self._records_to_emit.pop()
            handlers.HTTPHandler.emit(self, record)

    def emit(self, record):
        self._records_to_emit.append(record)

class ThreadedAwsHandler(logging.Handler):
    """A logging handler that sends the logs to an AWS queue through the
    SQS, this handler requires the boto library"""
    
    def __init__(self, access_key, secret_access_key, queue_name, 
                 revision=0, connection_kwargs={}):
        """:param connection_kwargs: arguments to be used when creating the
        underlying boto connection to aws"""
        logging.Handler.__init__(self)
        self._access_key = access_key
        self._secret_access_key = secret_access_key
        self._connection_kwargs = connection_kwargs
        self._queue_name = queue_name
        self._records_to_emit = []
        self._queue = None
        self._connected = True
        self._threaded_timer = ThreadedTimer(1000, self)
        self._threaded_timer.start()
        try:
            if sys.platform.startswith('win'):
                # on windows getuser() uses the USERNAME env var
                # from sys.getfilesystemencoding documentation:
                # On Windows NT+, file names are Unicode natively, so no conversion is performed. 
                # getfilesystemencoding() still returns 'mbcs', as this is the encoding that applications 
                # should use when they explicitly want to convert Unicode strings 
                # to byte strings that are equivalent when used as file names.
                self._user = getpass.getuser().decode('mbcs')
            else:
                self._user = getpass.getuser()
        except Exception:
            self._user = getpass.getuser().encode('ascii', 'ignore')
        self._revision = revision
        
    def emit(self, record):
        # inspired by the code in logging.handlers.SocketHandler
        import json
        ei = record.exc_info
        #
        # prevent infinite loops when the boto lib logs something when
        # a log is sent to the queue
        #
        if record.name and record.name.startswith('boto'):
            return
        if ei:
            self.format(record)
            record.exc_info = None
        record_dict = dict( user=self._user, revision=self._revision )
        record_dict.update( record.__dict__ )
        self._records_to_emit.append( json.dumps( record_dict ) )
        if ei:
            record.exc_info = ei  # for next handler
        
    @QtCore.pyqtSlot()
    def timeout(self):
        from boto.sqs.message import Message
        if not self._queue and self._connected:
            try:
                from boto.sqs.connection import SQSConnection
                sqs_connection = SQSConnection(self._access_key, 
                                               self._secret_access_key,
                                               **self._connection_kwargs)
                self._queue = sqs_connection.get_queue( self._queue_name )
            except Exception, e:
                LOGGER.error('Could not connect to logging queue %s'%self._queue_name, exc_info=e)
                self._connected = False
        while len(self._records_to_emit) and self._connected:
            record = self._records_to_emit.pop()
            self._queue.write( Message(body=record) )

class CloudLaunchHandler(ThreadedAwsHandler):
    """A logging handler that sends the logs to the Cloud Launch service,
    requires the cloudlaunch library, and only works with applications tested
    or deployed through cloudlaunch
    
    The cloudlaunch record can be obtained using the get_cloud_record
    method of the cloudlaunch.resources module.
    """
    
    def __init__(self, cloud_record, connection_kwargs={}):
        """:param cloud_record: the cloud record describing the application
        """
        queue_name = 'cloudlaunch-%s-%s-logging'%(cloud_record.author.replace(' ','_'), cloud_record.name.replace(' ','_') )
        ThreadedAwsHandler.__init__(self, 
                                    cloud_record.public_access_key, 
                                    cloud_record.public_secret_key, 
                                    queue_name,
                                    revision = cloud_record.revision,
                                    connection_kwargs = connection_kwargs)

