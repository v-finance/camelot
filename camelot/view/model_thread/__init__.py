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

import logging

from ...core.qt import QtCore

logger = logging.getLogger('camelot.view.model_thread')

_model_thread_ = []

# this might be set to False, for unittesting purpose
verify_threads = True

class ModelThreadException(Exception):
    pass

def object_thread( self ):
    """Funtion to verify if a call to an object is made in the thread of this
    object, to be used in assert statements.  Example ::
    
        class FooObject( QtCore.QObject ):
        
            def do_something( self ):
                assert object_thread( self )
                print 'safe method call'
    
    :param self: a :class:`QtCore.QObject` instance.
    :return True: if the thread of self is the current thread 
    
    The approach with assert statements is prefered over decorators,
    since decorators hide part of the method signature from the sphinx
    documentation.
    """
    return self.thread() == QtCore.QThread.currentThread()

def gui_thread():
    """function to verify if a call is made in the GUI thread of the application
    """
    app = QtCore.QCoreApplication.instance()
    return object_thread(app)

class AbstractModelThread(QtCore.QThread):
    """Abstract implementation of a model thread class
    Thread in which the model runs, all requests to the model should be
    posted to the the model thread.

    This class ensures the gui thread doesn't block when the model needs
    time to complete tasks by providing asynchronous communication between
    the model thread and the gui thread
    
    The Model thread class provides a number of signals :
    
    *thread_busy_signal*
    
    indicates if the model thread is working in the background
    
    *setup_exception_signal*
    
    this signal is emitted when there was an exception setting up the model
    thread, eg no connection to the database could be made.  this exception
    is mostly fatal for the application.
    """

    thread_busy_signal = QtCore.qt_signal(bool)
    setup_exception_signal = QtCore.qt_signal(object)

    def __init__(self):
        super(AbstractModelThread, self).__init__()
        self.logger = logging.getLogger(logger.name + '.%s' % id(self))
        self._exit = False
        self._traceback = ''
        self.logger.debug('model thread constructed')

    def run(self):
        pass

    def traceback(self):
        """The formatted traceback of the last exception in the model thread"""
        return self._traceback

    def wait_on_work(self):
        """Wait for all work to be finished, this function should only be used
    to do unit testing and such, since it will block the calling thread until
    all work is done"""
        pass

    def post(self, request, response=None, exception=None, args=()):
        """Post a request to the model thread, request should be a function
        that takes no arguments. The request function will be called within the
        model thread. When the request is finished, on first occasion, the
        response function will be called within the gui thread. The response
        function takes as arguments, the results of the request function.

        :param request: function to be called within the model thread
        :param response: a slot that will be called with the result of the
        request function
        :param exception: a slot that will be called in case request throws an
        exception
        :param args: arguments with which the request function will be called        
        """
        raise NotImplementedError

    def busy(self):
        """Return True or False indicating wether either the model or the gui
        thread is doing something"""
        return False
    
    def stop(self):
        """Stop the model thread from accepting any further posts.
        """
        return True

def has_model_thread():
    return len(_model_thread_) > 0

def get_model_thread():
    try:
        return _model_thread_[0]
    except IndexError:
        from .signal_slot_model_thread import SignalSlotModelThread
        _model_thread_.insert(0, SignalSlotModelThread())
        _model_thread_[0].start()
        return _model_thread_[0]

def post(request, response=None, exception=None, args=()):
    """Post a request and a response to the default model thread"""
    mt = get_model_thread()
    mt.post(request, response, exception, args)



