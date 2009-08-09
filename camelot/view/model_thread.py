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

import os
import sys
import logging
import threading
import Queue

logger = logging.getLogger('camelot.view.model_thread')

_model_thread_ = []

class ModelThreadException(Exception):
  pass

def model_function(original_function):
  """Decorator to ensure a function is only called from within the model
  thread.  If this function is called in another thread, an exception will be 
  thrown
  """
  
  def new_function(*args, **kwargs):
    if threading.currentThread() != get_model_thread():
      logger.error('%s was called outside the model thread' % 
                   (original_function.__name__))
      raise ModelThreadException()
    return original_function(*args, **kwargs)
  
  new_function.__name__ = original_function.__name__
  
  return new_function
  
def gui_function(original_function):
  """Decorator to ensure a function is only called from within the gui thread.
  If this function is called in another thread, an exception will be thrown

  @todo: now it only checks if the function is not called within the model
  thread, this is incomplete
  """  

  def new_function(*args, **kwargs):
    if threading.currentThread() == get_model_thread():
      logger.error('%s was called outside the gui thread' %
                   (original_function.__name__))
      raise ModelThreadException()
    return original_function(*args, **kwargs)
  
  new_function.__name__ = original_function.__name__
  
  return new_function


def setup_model():
  """Call the setup_model function in the settings"""
  from settings import setup_model
  setup_model()
  
class ModelThread(threading.Thread):
  """Thread in which the model runs, all requests to the model should be
  posted to the the model thread.

  This class ensures the gui thread doesn't block when the model needs
  time to complete tasks by providing asynchronous communication between
  the model thread and the gui thread
  """

  def __init__(self, response_signaler, setup_thread=setup_model):
    """
    @param response_signaler: an object with methods called :
      responseAvailable(self, model_thread) : this method will be called when a response is available
      startProcessingRequest(self, model_thread),
      stopProcessingRequest(self, model_thread),
    @param setup_thread: function to be called at startup of the thread to initialize
    everything, by default this will setup the model.  set to None if nothing should
    be done. 
    """
    self.logger = logging.getLogger(logger.name + '.%s'%id(self))
    self._setup_thread = setup_thread
    self._exit = False
    threading.Thread.__init__(self)
    self._request_queue = Queue.Queue()
    self._response_queue = Queue.Queue()
    self._response_signaler = response_signaler
    self._traceback = ''
    self.post(setup_thread)
    self.logger.debug('model thread constructed')

  def run(self):
    self.logger.debug('model thread started')
    try:
      if self._setup_thread:
        self._setup_thread()
      self.logger.debug('start handling requests')
      while not self._exit:
        new_event = threading.Event()
        try:
          (event, request, response, exception) = self._request_queue.get()
          self.logger.debug('execute request %s'%id(request))
          #self._response_queue.join()
          self.logger.debug('start handling request')
#          import inspect
#          print inspect.getsource(request)
          self._response_signaler.startProcessingRequest(self)
          result = request()
          self._response_queue.put((new_event, result, response))
          self._request_queue.task_done()
          self._response_signaler.responseAvailable(self)
          self._response_signaler.stopProcessingRequest(self)
          self.logger.debug('finished handling request')
          event.set()
          #self._response_queue.join()
        except Exception, e:
          import traceback, sys, cStringIO
          sio = cStringIO.StringIO()
          traceback.print_exc(file=sio)
          self._traceback = sio.getvalue()
          sio.close()
          self.logger.error('exception caught in model thread', exc_info=e)
          exception_info = (e, self)
          self._response_queue.put((new_event, exception_info, exception))
          self._request_queue.task_done()
          self._response_signaler.responseAvailable(self)
          self._response_signaler.stopProcessingRequest(self)
          event.set()
        except:
          self.logger.error('unhandled exception in model thread')
    except Exception, e:
      self.logger.error('1exception caught in model thread', exc_info=e)
    except:
      self.logger.error('unhandled exception')

  def traceback(self):
    """The formatted traceback of the last exception in the model thread"""
    return self._traceback
  
  def process_responses(self):
    """Process all responses that are generated by completed requests
    from the ModelThread.  This method should be called from time
    to time from within the GUI thread.
    """
    try:
      while True:
        (event, result, response) = self._response_queue.get_nowait()
        self.logger.debug('execute response %s'%id(response))
        try:
          response(result)
        except Exception, e:
          self.logger.error('exception in response %s'%id(response), exc_info=e)
        self._response_queue.task_done()
        event.set()
    except Queue.Empty, e:
      pass

  def post(self, request, response=lambda result:None,
           exception=lambda exc:None):
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
    @return a threading Event object which will be set to True when the
    request function is finished and the response has been put on the queue
    """
    self.logger.debug('post request %s %s with response %s %s'%(id(request), request.__name__, id(response), response.__name__))
    event = threading.Event()
    self._request_queue.put_nowait((event, request, response, exception))
    return event
  
  def post_response(self, response, arg):
    """Post a function to the response queue
    @param response: function to be called within the gui thread
    @param arg: the argument to use when calling the response function
    @return a threading Event object which will be set to True when the
    response function is finished
    """
    event = threading.Event()
    self._response_queue.put((event, arg, response))
    self._response_signaler.responseAvailable(self)
    self._response_signaler.stopProcessingRequest(self)
            
  def exit(self):
    """Ask the model thread to exit"""
    self._exit = True
    
    def exit_message():
      self.logger.debug('exit requested')
    
    self.post(exit_message)
    
  def post_and_block(self, request):
    """Post a request tot the model thread, block until it is finished, and
    then return it results.  This function only exists for testing purposes,
    it should never be used from within the gui thread
    """
    # make sure there are no responses in the queue
    self.process_responses()
    results = []
    
    def re_raise(exc):
      raise exc
    
    event = self.post(request,
                      lambda result:results.append(result),
                      exception=re_raise)
    event.wait()
    self.process_responses()
    return results[-1]
    
def construct_model_thread(*args, **kwargs):
  _model_thread_.insert(0, ModelThread(*args, **kwargs))
  
def get_model_thread():
  return _model_thread_[0]
