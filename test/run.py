import logging
import settings
import unittest
import sys
logger = logging.getLogger('unittest')

from PyQt4.QtCore import *
from PyQt4.QtGui import *
           
logger = logging.getLogger('view.unittests')

def create_getter(getable):
  
  def getter():
    return getable
  
  return getter
  
def testSuites():

  from camelot.view.model_thread import get_model_thread, construct_model_thread
  from camelot.view.response_handler import ResponseHandler
  from camelot.view.remote_signals import construct_signal_handler
  rh = ResponseHandler()
  construct_model_thread(rh)
  construct_signal_handler()
  construct_model_thread(rh)
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
        

  class proxy_tests(unittest.TestCase):
    """Test the functionality of the proxies to perform CRUD operations on data"""
    def setUp(self):
      from camelot.view.application_admin import ApplicationAdmin
      self.app_admin = ApplicationAdmin([])
      self.mt = get_model_thread()
      self.block = self.mt.post_and_block
    def testCreateUpdateDeleteValidData(self):
      from camelot.model.authentication import Person
      from camelot.view.proxy.queryproxy import QueryTableProxy
      person_admin = self.app_admin.getEntityAdmin(Person)
      person_proxy1 = QueryTableProxy(person_admin, Person.query, person_admin.getFields)
      rows_before_insert = self.block(lambda:person_proxy1.getRowCount())
      # get the columns of the proxy
      columns = dict((c[0],i) for i,c in enumerate(self.block(lambda:person_proxy1.getColumns())))
      # Create a new person
      new_person = self.block(lambda:Person(username=u'test'))
      person_proxy1.insertRow(0, create_getter(new_person))
      rows_after_insert = self.block(lambda:person_proxy1.getRowCount())
      self.assertTrue( self.block(lambda:new_person.id) != None )
      self.assertTrue( rows_after_insert > rows_before_insert)
      # Update a new person
      index = person_proxy1.index(rows_before_insert, columns['last_name'])
      person_proxy1.setData(index, lambda:u'Testers')
      self.assertEqual( self.block(lambda:new_person.last_name), u'Testers')
      # Delete this person
      person_proxy1.removeRow(rows_before_insert)
      rows_after_delete = self.block(lambda:person_proxy1.getRowCount())
      self.assertTrue( rows_after_delete < rows_after_insert )
    def testCreateUpdateDeleteInvalidData(self):
      pass
      
  import inspect
  for c in locals().values():
    if inspect.isclass(c):
      yield unittest.makeSuite(c, 'test')
      
if __name__ == '__main__':
  logger.info('running unit tests')
  import sys
  app = QApplication(sys.argv)  
  runner=unittest.TextTestRunner()
  for s in testSuites():
    runner.run(s)  