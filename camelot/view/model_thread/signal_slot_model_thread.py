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
'''
Created on Sep 9, 2009

@author: tw55413
'''
import json
import logging

logger = logging.getLogger('camelot.view.model_thread.signal_slot_model_thread')
REQUEST_LOGGER = logging.getLogger('request')

from ..action_runner import action_runner
from ..requests import CancelAction
from ..responses import Busy
from ...core.qt import QtCore, is_deleted
from ...core.serializable import NamedDataclassSerializable
from ...core.threading import synchronized
from ...view.model_thread import AbstractModelThread

cancel_action_prefix = CancelAction(run_name=[])._to_bytes()[:13]

class TaskHandler(QtCore.QObject):
    """A task handler is an object that handles tasks that appear in a queue,
    when its handle_task method is called, it will sequentially handle all tasks
    that are in the queue.
    """

    def __init__(self, queue):
        """:param queue: the queue from which to pop a task when handle_task
        is called"""
        QtCore.QObject.__init__(self)
        self._mutex = QtCore.QMutex()
        self._queue = queue
        logger.debug("TaskHandler created.")

    def has_cancel_request(self):
        for request in self._queue._request_queue:
            # TODO : the cancel request stays in the request queue, and will
            # be handled after the action has stopped, this will result in a
            # run name not found error message
            if request.startswith(cancel_action_prefix):
                return True
        return False

    @QtCore.qt_slot()
    def handle_task(self):
        """Handle all tasks that are in the queue"""
        request = self._queue.pop()
        action_runner.send_response(Busy(True))
        while request:
            try:
                assert isinstance(request, bytes)
                request_type_name, request_data = json.loads(request)
                request_type = NamedDataclassSerializable.get_cls_by_name(
                    request_type_name
                )
                request_type.execute(request_data, action_runner, self)
            except Exception as e:
                logger.fatal('Unhandled exception in model thread', exc_info=e)
            except:
                logger.fatal('Unhandled something in model thread')
            request = self._queue.pop()
        action_runner.send_response(Busy(False))

class SignalSlotModelThread( AbstractModelThread ):
    """A model thread implementation that uses signals and slots
    to communicate between the model thread and the gui thread

    there is no explicit model thread verification on these methods,
    since this model thread might not be THE model thread.
    """

    task_available = QtCore.qt_signal()

    def __init__( self ):
        super(SignalSlotModelThread, self).__init__()
        self._task_handler = None
        self._mutex = QtCore.QMutex()
        self._request_queue = []
        self._connected = False

    def _init_model_thread(self):
        """
        Initialize the objects that live in the model thread
        """
        self._task_handler = TaskHandler(self)

    def run( self ):
        self.logger.debug( 'model thread started' )
        self._init_model_thread()
        # Some tasks might have been posted before the signals were connected
        # to the task handler, so once force the handling of tasks
        self._task_handler.handle_task()
        self.exec()
        self.logger.debug('model thread stopped')

    @synchronized
    def post(self, request):
        if not self._connected and self._task_handler:
            # creating this connection in the model thread throws QT exceptions
            self.task_available.connect( self._task_handler.handle_task, QtCore.Qt.ConnectionType.QueuedConnection )
            self._connected = True
        serialized_request = request._to_bytes()
        if REQUEST_LOGGER.isEnabledFor(logging.DEBUG):
            REQUEST_LOGGER.debug(serialized_request)
        self._request_queue.append(serialized_request)
        if not is_deleted(self):
            self.task_available.emit()
        return ['thread', str(id(self))]

    @synchronized
    def stop( self ):
        self.quit()
        return True
    
    @synchronized
    def pop( self ):
        """Pop a task from the queue, return None if the queue is empty"""
        if len(self._request_queue):
            task = self._request_queue.pop(0)
            return task
