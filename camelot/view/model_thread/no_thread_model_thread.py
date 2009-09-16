'''
Created on Sep 12, 2009

@author: tw55413
'''

from signal_slot_model_thread import AbstractModelThread, Task, setup_model

class NoThreadModelThread(AbstractModelThread):
  
  def __init__(self, response_signaler, setup_thread = setup_model ):
    self.responses = []
    AbstractModelThread.__init__(self, response_signaler, setup_thread = setup_model )
    
  def start(self):
    pass
  
  def post_response( self, response, arg ):
    response(arg)

  def post( self, request, response = lambda result:None,
           exception = lambda exc:None ):
    task = Task(request)
    task.connect(task, task.finished, response)
    task.connect(task, task.exception, exception)
    task.execute()
    
  def process_responses(self):
    while self.responses:
      response,result = self.responses.pop(0)
      response(result)
      
  def isRunning(self):
    return True