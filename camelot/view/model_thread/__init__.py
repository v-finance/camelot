#  ============================================================================
#
#  Copyright (C) 2007-2008 Conceptive Engineering bvba. All rights reserved.
#  www.conceptive.be / project-camelot@conceptive.be
#
#  This file is part of the Camelot Library.
#
#  This file may be used under the terms of the GNU General Public
#  License version 2.0 as published by the Free Software Foundation
#  and appearing in the file LICENSE.GPL included in the packaging of
#  this file.  Please review the following information to ensure GNU
#  General Public Licensing requirements will be met:
#  http://www.trolltech.com/products/qt/opensource.html
#
#  If you are unsure which license is appropriate for your use, please
#  review the following information:
#  http://www.trolltech.com/products/qt/licensing.html or contact
#  project-camelot@conceptive.be.
#
#  This file is provided AS IS with NO WARRANTY OF ANY KIND, INCLUDING THE
#  WARRANTY OF DESIGN, MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE.
#
#  For use of this library in commercial applications, please contact
#  project-camelot@conceptive.be
#
#  ============================================================================

import logging
from functools import wraps

from PyQt4 import QtCore, QtGui

logger = logging.getLogger( 'camelot.view.model_thread' )

_model_thread_ = []

class ModelThreadException( Exception ):
    pass

def model_function( original_function ):
    """Decorator to ensure a function is only called from within the model
    thread.  If this function is called in another thread, an exception will be
    thrown
    """

    def in_model_thread():
        """return wether current thread is model thread"""
        from no_thread_model_thread import NoThreadModelThread
        current_thread = QtCore.QThread.currentThread()
        model_thread = get_model_thread()
        return (current_thread==model_thread) or isinstance(model_thread, (NoThreadModelThread,))

    @wraps(original_function)
    def wrapper( *args, **kwargs ):
        assert in_model_thread()
        return original_function( *args, **kwargs )

    return wrapper

def gui_function( original_function ):
    """Decorator to ensure a function is only called from within the gui thread.
    If this function is called in another thread, an exception will be thrown
    """

    def in_gui_thread():
        """return wether current thread is gui thread"""
        gui_thread = QtGui.QApplication.instance().thread()
        current_thread = QtCore.QThread.currentThread()
        return gui_thread == current_thread

    @wraps( original_function )
    def wrapper( *args, **kwargs ):
        assert in_gui_thread()
        return original_function( *args, **kwargs )

    return wrapper

def setup_model():
    """Call the setup_model function in the settings"""
    from settings import setup_model
    setup_model()

class AbstractModelThread(object):
    """Abstract implementation of a model thread class
  Thread in which the model runs, all requests to the model should be
  posted to the the model thread.

  This class ensures the gui thread doesn't block when the model needs
  time to complete tasks by providing asynchronous communication between
  the model thread and the gui thread
  """

    thread_busy_signal = QtCore.SIGNAL('thread_busy')
    
    def __init__(self, setup_thread = setup_model ):
        """
        @param setup_thread: function to be called at startup of the thread to initialize
        everything, by default this will setup the model.  set to None if nothing should
        be done.
        """
        self.logger = logging.getLogger( logger.name + '.%s' % id( self ) )
        self._setup_thread = setup_thread
        self._exit = False
        self._traceback = ''
        self.logger.debug( 'model thread constructed' )

    def run(self):
        pass

    def traceback( self ):
        """The formatted traceback of the last exception in the model thread"""
        return self._traceback

    def wait_on_work(self):
        """Wait for all work to be finished, this function should only be used
    to do unit testing and such, since it will block the calling thread until
    all work is done"""
        pass

    def process_responses(self):
        pass

    def post_response( self, response, arg ):
        raise NotImplemented

    def post( self, request, response = None, exception = None ):
        """Post a request to the model thread, request should be
    a function that takes no arguments.  The request function
    will be called within the model thread.  When the request
    is finished, on first occasion, the response function will be
    called within the gui thread.  The response function takes as
    arguments, the results of the request function.
    @param request: function to be called within the model thread
    @param response: a slot that will be called with the result of the
    request function
    @param exception: a slot that will be called in case request throws
    an exception
        """
        raise NotImplemented

def construct_model_thread( *args, **kwargs ):
    from signal_slot_model_thread import SignalSlotModelThread
    _model_thread_.insert( 0, SignalSlotModelThread( *args, **kwargs ) )

def has_model_thread():
    return len( _model_thread_ ) > 0

def get_model_thread():
    return _model_thread_[0]

def post(request, response = None, exception = None):
    """Post a request and a response to the default model thread"""
    mt = get_model_thread()
    mt.post(request, response, exception)
