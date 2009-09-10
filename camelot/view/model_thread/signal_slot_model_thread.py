'''
Created on Sep 9, 2009

@author: tw55413
'''
import Queue
import logging
from PyQt4 import QtCore

from camelot.view.model_thread import AbstractModelThread, gui_function, setup_model

logger = logging.getLogger('camelot.view.model_thread.signal_slot_model_thread')

class Task(QtCore.QObject):
  
  finished = QtCore.SIGNAL('finished')
  exception = QtCore.SIGNAL('exception')
  
  def __init__(self, request):
    QtCore.QObject.__init__(self)
    self.request = request
    
  def execute(self):
    try:
      result = self.request()
      self.emit(self.finished, result)
    except Exception, e:
      logger.error( 'exception caught in model thread', exc_info = e )
      exception_info = (e, '')
      self.emit(self.exception, exception_info)
          
class SignalSlotModelThread( QtCore.QThread, AbstractModelThread ):
  """A model thread implementation that uses signals and slots
  to communicate between the model thread and the gui thread
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
    self._request_queue = Queue.Queue()
    AbstractModelThread.__init__( self, response_signaler, setup_thread )
    
  def run( self ):
    self.logger.debug( 'model thread started' )
    try:
      while not self._exit:
        try:
          try:
            task = self._request_queue.get(timeout = 5)
            task.execute()
            self._request_queue.task_done()
          except Queue.Empty, e:
            self.logger.debug('model thread still allive, nothing in queue')
        except Exception, e:
          self.logger.error( 'exception caught in model thread', exc_info = e )            
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

  def post( self, request, response = lambda result:None,
           exception = lambda exc:None , dependency = None ):
    self.logger.debug( 'post request %s %s with response %s %s' % ( id( request ), request.__name__, id( response ), response.__name__ ) )
    task = Task(request)
    task.connect(task, task.finished, response)
    task.connect(task, task.exception, exception)
    self._request_queue.put_nowait( task )

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