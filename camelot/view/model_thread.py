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
import Queue
import sip

from PyQt4 import QtCore

logger = logging.getLogger( 'camelot.view.model_thread' )

_model_thread_ = []

class ModelThreadException( Exception ):
  pass

def model_function( original_function ):
  """Decorator to ensure a function is only called from within the model
  thread.  If this function is called in another thread, an exception will be 
  thrown
  """

  def new_function( *args, **kwargs ):
    current_thread = QtCore.QThread.currentThread()
    if current_thread != get_model_thread():
      message = '%s was called outside the model thread' % original_function.__name__
      logger.error( message )
      logger.error( 'calling thread is %s' % id( current_thread ) )
      raise ModelThreadException( message )
    return original_function( *args, **kwargs )

  new_function.__name__ = original_function.__name__

  return new_function

def gui_function( original_function ):
  """Decorator to ensure a function is only called from within the gui thread.
  If this function is called in another thread, an exception will be thrown

  @todo: now it only checks if the function is not called within the model
  thread, this is incomplete
  """

  def new_function( *args, **kwargs ):
    current_thread = QtCore.QThread.currentThread()
    if current_thread == get_model_thread():
      logger.error( '%s was called outside the gui thread' %
                   ( original_function.__name__ ) )
      raise ModelThreadException()
    return original_function( *args, **kwargs )

  new_function.__name__ = original_function.__name__

  return new_function


def setup_model():
  """Call the setup_model function in the settings"""
  from settings import setup_model
  setup_model()

class ModelThread( QtCore.QThread ):
  """Thread in which the model runs, all requests to the model should be
  posted to the the model thread.

  This class ensures the gui thread doesn't block when the model needs
  time to complete tasks by providing asynchronous communication between
  the model thread and the gui thread
  """

  def __init__( self, response_signaler, setup_thread = setup_model ):
    """
    @param response_signaler: an object with methods called :
      responseAvailable(self, model_thread) : this method will be called when a response is available
      startProcessingRequest(self, model_thread),
      stopProcessingRequest(self, model_thread),
    @param setup_thread: function to be called at startup of the thread to initialize
    everything, by default this will setup the model.  set to None if nothing should
    be done. 
    """
    QtCore.QThread.__init__( self )
    self.logger = logging.getLogger( logger.name + '.%s' % id( self ) )
    self._setup_thread = setup_thread
    self._exit = False
    self._request_queue = Queue.Queue( 1000 )
    self._response_queue = Queue.Queue( 1000 )
    self._response_signaler = response_signaler
    self._traceback = ''
    self.post( setup_thread )
    self.logger.debug( 'model thread constructed' )

  def run( self ):
    self.logger.debug( 'model thread started' )
    try:
#      if self._setup_thread:
#        self._setup_thread()
#      self.logger.debug( 'start handling requests' )
      while not self._exit:
        try:
          try:
            ( request, response, exception, dependency ) = self._request_queue.get(timeout = 5)
            #self.logger.debug( 'execute request %s' % id( request ) )
            #self._response_queue.join()
            #self.logger.debug( 'start handling request' )
  #          import inspect
  #          print inspect.getsource(request)
            self._response_signaler.startProcessingRequest( self )
            result = request()
            self._response_queue.put( ( result, response, dependency ), timeout = 10 )
            self._request_queue.task_done()
            self._response_signaler.responseAvailable( self )
            self._response_signaler.stopProcessingRequest( self )
            #self.logger.debug( 'finished handling request' )            
          except Queue.Empty, e:
            self.logger.debug('model thread still allive, nothing in queue')
        except Exception, e:
          import traceback, cStringIO
          sio = cStringIO.StringIO()
          traceback.print_exc( file = sio )
          self._traceback = sio.getvalue()
          sio.close()
          self.logger.error( 'exception caught in model thread', exc_info = e )
          exception_info = ( e, self )
          self._response_queue.put( ( exception_info, exception, dependency ), timeout = 10 )
          self._request_queue.task_done()
          self._response_signaler.responseAvailable( self )
          self._response_signaler.stopProcessingRequest( self )
          self.logger.error( 'function causing exception was %s' % ( request.__name__ ) )
        except:
          self.logger.error( 'unhandled exception in model thread' )
    except Exception, e:
      self.logger.error( 'exception caught in model thread', exc_info = e )
    except:
      self.logger.error( 'unhandled exception' )
    # empty the request queue, before tearing down
    self.logger.debug('tearing down')
    while not self._request_queue.empty():
      _element = self._request_queue.get()
      self._request_queue.task_done()
    self.logger.debug('finished')

  def traceback( self ):
    """The formatted traceback of the last exception in the model thread"""
    return self._traceback

  def process_responses( self ):
    """Process all responses that are generated by completed requests
    from the ModelThread.  This method should be called from time
    to time from within the GUI thread.
    """
    try:
      while True:
        ( result, response, dependency ) = self._response_queue.get_nowait()
        self.logger.debug( 'execute response %s' % id( response ) )
        try:
            if dependency != None:
                if sip.isdeleted( dependency ):
                    pass
                else:
                    response( result )
            else:
                response( result )
        except Exception, e:
          self.logger.error( 'exception in response %s' % id( response ), exc_info = e )
        self._response_queue.task_done()
    except Queue.Empty, e:
      pass

  def post( self, request, response = lambda result:None,
           exception = lambda exc:None , dependency = None ):
    """Post a request to the model thread, request should be
    a function that takes no arguments.  The request function
    will be called within the model thread.  When the request
    is finished, on first occasion, the response function will be
    called within the gui thread.  The response function takes as
    arguments, the results of the request function.
    @param request: function to be called within the model thread
    @param response: function to be called within the gui thread, when
    the request function is finished, the response function takes
    as its argument the result of the request function
    @param exception: function to be called in case of an exception in the
    request function
    @param dependency: The dependent posting object. Usually this will be self.
    """
    self.logger.debug( 'post request %s %s with response %s %s' % ( id( request ), request.__name__, id( response ), response.__name__ ) )
    self._request_queue.put_nowait( ( request, response, exception, dependency ) )

  def post_response( self, response, arg ):
    """Post a function to the response queue
    @param response: function to be called within the gui thread
    @param arg: the argument to use when calling the response function
    @return a threading Event object which will be set to True when the
    response function is finished
    """
    self._response_queue.put( ( arg, response ) )
    self._response_signaler.responseAvailable( self )
    self._response_signaler.stopProcessingRequest( self )

  @gui_function
  def wait_on_work(self):
    """Wait for all work to be finished, this function should only be used
    to do unit testing and such, since it will block the calling thread until
    all work is done"""
    from PyQt4.QtCore import QCoreApplication
    app = QCoreApplication.instance()
    self._request_queue.join()
    while not self._response_queue.empty():
      logger.debug('queues not yet empty : %s requests and %s responses'%(self._request_queue.qsize(), self._response_queue.qsize()))
      self.process_responses()
      app.processEvents()
      self._request_queue.join()
      
  def exit( self ):
    """Ask the model thread to exit"""
    self._exit = True

    def exit_message():
      self.logger.debug( 'exit requested' )

    self.post( exit_message )

def construct_model_thread( *args, **kwargs ):
  _model_thread_.insert( 0, ModelThread( *args, **kwargs ) )

def has_model_thread():
  return len( _model_thread_ ) > 0

def get_model_thread():
  return _model_thread_[0]
