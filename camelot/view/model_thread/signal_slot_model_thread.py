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
import logging
import sys
import time

logger = logging.getLogger('camelot.view.model_thread.signal_slot_model_thread')

import six

from ...core.qt import QtCore
from ...core.threading import synchronized
from ...view.model_thread import AbstractModelThread, object_thread
from ...view.controls.exception import register_exception


class Task(QtCore.QObject):

    finished = QtCore.qt_signal(object)
    exception = QtCore.qt_signal(object)

    def __init__(self, request, name='', args=()):
        """A task to be executed in a different thread
        :param request: the function to execture
        :param name: a string with the name of the task to be used in the gui
        :param args: a tuple with the arguments to be passed to the request
        """
        QtCore.QObject.__init__(self)
        self._request = request
        self._name = name
        self._args = args

    def clear(self):
        """clear this tasks references to other objects"""
        self._request = None
        self._name = None
        self._args = None

    def execute(self):
        logger.debug('executing %s' % (self._name))
        try:
            result = self._request( *self._args )
            self.finished.emit( result )
        #
        # don't handle StopIteration as a normal exception, but return a new
        # instance of StopIteration (in order to not keep alive a stack trace),
        # and to signal to the caller that an iterator has ended
        #
        except StopIteration:
            self.finished.emit( StopIteration() )
        except Exception as e:
            exc_info = register_exception(logger, 'exception caught in model thread while executing %s'%self._name, e)
            self.exception.emit( exc_info )
            self.clear_exception_info()
        except:
            logger.error( 'unhandled exception in model thread' )
            exc_info = ( 'Unhandled exception', 
                         sys.exc_info()[0], 
                         None, 
                         'Please contact the application developer', '')
            # still emit the exception signal, to allow the gui to clean up things (such as closing dialogs)
            self.exception.emit( exc_info )
            self.clear_exception_info()
            
    def clear_exception_info( self ):
        # the exception info contains a stack that might contain references to 
        # Qt objects which could be kept alive this way
        if not six.PY3:
            sys.exc_clear()

class TaskHandler(QtCore.QObject):
    """A task handler is an object that handles tasks that appear in a queue,
    when its handle_task method is called, it will sequentially handle all tasks
    that are in the queue.
    """

    task_handler_busy_signal = QtCore.qt_signal(bool)

    def __init__(self, queue):
        """:param queue: the queue from which to pop a task when handle_task
        is called"""
        QtCore.QObject.__init__(self)
        self._mutex = QtCore.QMutex()
        self._queue = queue
        self._tasks_done = []
        self._busy = False
        logger.debug("TaskHandler created.")

    def busy(self):
        """:return True/False: indicating if this task handler is busy"""
        return self._busy

    @QtCore.qt_slot()
    def handle_task(self):
        """Handle all tasks that are in the queue"""
        self._busy = True
        self.task_handler_busy_signal.emit( True )
        task = self._queue.pop()
        while task:
            task.execute()
            # we keep track of the tasks done to prevent them being garbage collected
            # apparently when they are garbage collected, they are recycled, but their
            # signal slot connections seem to survive this recycling.
            # @todo: this should be investigated in more detail, since we are causing
            #        a deliberate memory leak here
            #
            # not keeping track of the tasks might result in corruption
            #
            # see : http://www.riverbankcomputing.com/pipermail/pyqt/2011-August/030452.html
            #
            task.clear()
            self._tasks_done.append(task)
            task = self._queue.pop()
        self.task_handler_busy_signal.emit( False )
        self._busy = False

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
        self._task_handler.task_handler_busy_signal.connect(self._thread_busy, QtCore.Qt.QueuedConnection)

    def run( self ):
        self.logger.debug( 'model thread started' )
        self._init_model_thread()
        # Some tasks might have been posted before the signals were connected
        # to the task handler, so once force the handling of tasks
        self._task_handler.handle_task()
        self.exec_()
        self.logger.debug('model thread stopped')

    @QtCore.qt_slot( bool )
    def _thread_busy(self, busy_state):
        self.thread_busy_signal.emit( busy_state )

    @synchronized
    def post( self, request, response = None, exception = None, args = () ):
        if not self._connected and self._task_handler:
            # creating this connection in the model thread throws QT exceptions
            self.task_available.connect( self._task_handler.handle_task, QtCore.Qt.QueuedConnection )
            self._connected = True
        # response should be a slot method of a QObject
        name = request.__name__
        task = Task(request, name = name, args = args)
        # QObject::connect is a thread safe function
        if response:
            assert getattr( response, six._meth_self ) != None
            assert isinstance( getattr( response, six._meth_self ), 
                               QtCore.QObject )
            # verify if the response has been defined as a slot
            #assert hasattr(response, '__pyqtSignature__')
            task.finished.connect(response, QtCore.Qt.QueuedConnection)
        if exception:
            task.exception.connect( exception, QtCore.Qt.QueuedConnection )
        # task.moveToThread(self)
        # only put the task in the queue when it is completely set up
        self._request_queue.append(task)
        #print 'task created --->', id(task)
        self.task_available.emit()

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

    @synchronized
    def busy( self ):
        """Return True or False indicating wether either the model or the
        gui thread is doing something"""
        while not self._task_handler:
            time.sleep(0.1)
        return len(self._request_queue) or self._task_handler.busy()

    def wait_on_work(self):
        """Wait for all work to be finished, this function should only be used
        to do unit testing and such, since it will block the calling thread until
        all work is done"""
        assert object_thread( self )
        while self.busy():
            time.sleep(0.1)




