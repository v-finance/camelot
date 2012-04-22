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
'''
Created on Sep 9, 2009

@author: tw55413
'''
import logging
import sys
logger = logging.getLogger('camelot.view.model_thread.signal_slot_model_thread')

from PyQt4 import QtCore

from camelot.view.model_thread import ( AbstractModelThread, object_thread, 
                                        setup_model )
from camelot.core.threading import synchronized
from camelot.view.controls.exception import register_exception

class Task(QtCore.QObject):

    finished = QtCore.pyqtSignal(object)
    exception = QtCore.pyqtSignal(object)

    def __init__(self, request, name='', args=()):
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
        except Exception, e:
            exc_info = register_exception(logger, 'exception caught in model thread while executing %s'%self._name, e)
            self.exception.emit( exc_info )
            # the stack might contain references to QT objects which could be kept alive this way
            sys.exc_clear()
        except:
            logger.error( 'unhandled exception in model thread' )
            exc_info = ( 'Unhandled exception', 
                         sys.exc_info()[0], 
                         None, 
                         'Please contact the application developer', '')
            # still emit the exception signal, to allow the gui to clean up things (such as closing dialogs)
            self.exception.emit( exc_info )
            sys.exc_clear()

class TaskHandler(QtCore.QObject):
    """A task handler is an object that handles tasks that appear in a queue,
    when its handle_task method is called, it will sequentially handle all tasks
    that are in the queue.
    """

    task_handler_busy_signal = QtCore.pyqtSignal(bool)

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

    @QtCore.pyqtSlot()
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

    task_available = QtCore.pyqtSignal()

    def __init__( self, setup_thread = setup_model ):
        """
        @param setup_thread: function to be called at startup of the thread to initialize
        everything, by default this will setup the model.  set to None if nothing should
        be done.
        """
        from camelot.view.model_thread.garbage_collector import GarbageCollector
        super(SignalSlotModelThread, self).__init__( setup_thread )
        self._task_handler = None
        self._mutex = QtCore.QMutex()
        self._request_queue = []
        self._connected = False
        self._setup_busy = True
        GarbageCollector( self )

    def run( self ):
        self.logger.debug( 'model thread started' )
        self._task_handler = TaskHandler(self)
        self._task_handler.task_handler_busy_signal.connect(self._thread_busy, QtCore.Qt.QueuedConnection)
        self._thread_busy(True)
        try:
            self._setup_thread()
        except Exception, e:
            exc_info = register_exception(logger, 'Exception when setting up the SignalSlotModelThread', e)
            self.setup_exception_signal.emit( exc_info )
        self._thread_busy(False)
        self.logger.debug('thread setup finished')
        # Some tasks might have been posted before the signals were connected to the task handler,
        # so once force the handling of tasks
        self._task_handler.handle_task()
        self._setup_busy = False
        self.exec_()
        self.logger.debug('model thread stopped')

    @QtCore.pyqtSlot( bool )
    def _thread_busy(self, busy_state):
        self.thread_busy_signal.emit( busy_state )

    @synchronized
    def post( self, request, response = None, exception = None, args = () ):
        if not self._connected and self._task_handler:
            # creating this connection in the model thread throws QT exceptions
            self.task_available.connect( self._task_handler.handle_task, QtCore.Qt.QueuedConnection )
            self._connected = True
        # response should be a slot method of a QObject
        if response:
            name = '%s -> %s.%s'%(request.__name__, response.im_self.__class__.__name__, response.__name__)
        else:
            name = request.__name__
        task = Task(request, name=name, args=args)
        # QObject::connect is a thread safe function
        if response:
            assert response.im_self != None
            assert isinstance(response.im_self, QtCore.QObject)
            # verify if the response has been defined as a slot
            #assert hasattr(response, '__pyqtSignature__')
            task.finished.connect( response, QtCore.Qt.QueuedConnection )
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
            import time
            time.sleep(1)
        app = QtCore.QCoreApplication.instance()
        return app.hasPendingEvents() or len(self._request_queue) or self._task_handler.busy() or self._setup_busy

    def wait_on_work(self):
        """Wait for all work to be finished, this function should only be used
        to do unit testing and such, since it will block the calling thread until
        all work is done"""
        assert object_thread( self )
        app = QtCore.QCoreApplication.instance()
        while self.busy():
            app.processEvents()

