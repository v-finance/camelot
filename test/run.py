import logging
import settings
import unittest
import sys
logger = logging.getLogger('unittest')

from PyQt4.QtCore import *
from PyQt4.QtGui import *
           
logger = logging.getLogger('view.unittests')   
def testSuites():

  from camelot.view.model_thread import get_model_thread, construct_model_thread
  from camelot.view.response_handler import ResponseHandler
    
  construct_model_thread(ResponseHandler())
  get_model_thread().start()
  
  class model_thread_tests(unittest.TestCase):
      def setUp(self):
        self.mt = get_model_thread()
      def testRequestAndResponseInDifferentThread(self):
        """Test if the request function is really executed in another thread"""
        
        def get_request_thread():
          import threading
          return threading.currentThread()
        
        def compare_with_response_thread(thread):
          import threading
          self.assertNotEqual(thread, threading.currentThread())
          
        event = self.mt.post( get_request_thread, compare_with_response_thread )
        event.wait()
        self.mt.process_responses()
        
  import inspect
  for c in locals().values():
    if inspect.isclass(c):
      yield unittest.makeSuite(c, 'test')
      
if __name__ == '__main__':
  logger.info('running unit tests')
  runner=unittest.TextTestRunner()
  for s in testSuites():
    runner.run(s)  