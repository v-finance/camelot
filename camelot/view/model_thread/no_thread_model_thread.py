'''
Created on Sep 12, 2009

@author: tw55413
'''

from signal_slot_model_thread import AbstractModelThread, Task, setup_model

class NoThreadModelThread(AbstractModelThread):

    def __init__(self, setup_thread = setup_model ):
        self.responses = []
        AbstractModelThread.__init__(self, setup_thread = setup_model )
        self._setup_thread()

    def start(self):
        pass

    def post( self, request, response = lambda result:None,
             exception = lambda exc:None ):
        task = Task(request)
        if response:
            task.connect(task, task.finished, response)
        if exception:
            task.connect(task, task.exception, exception)
        task.execute()

    def isRunning(self):
        return True
