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
      from camelot.model.authentication import Person
      from camelot.view.proxy.queryproxy import QueryTableProxy
      from camelot.view.application_admin import ApplicationAdmin
      self.app_admin = ApplicationAdmin([])
      self.mt = get_model_thread()
      self.block = self.mt.post_and_block
      person_admin = self.app_admin.getEntityAdmin(Person)
      self.person_proxy = QueryTableProxy(person_admin, Person.query, person_admin.getFields)
      # get the columns of the proxy
      self.columns = dict((c[0],i) for i,c in enumerate(self.block(lambda:self.person_proxy.getColumns())))
      self.rows_before_insert = 0
      self.rows_after_insert = 0
      self.rows_after_delete = 0
      self.new_person = None
    def listPersons(self):
      from camelot.model.authentication import Person
      
      def create_list():
        print '<persons>'
        for p in Person.query.all():
          print p.id, unicode(p)
        print '</persons>'
      
      self.block(create_list)
    def numberOfPersons(self):
      return self.block(lambda:self.person_proxy.getRowCount())
    def insertNewPerson(self, valid):
      from camelot.model.authentication import Person
      self.rows_before_insert = self.numberOfPersons()
      self.new_person = self.block(lambda:Person(username={True:u'test', False:None}[valid]))
      self.person_proxy.insertRow(0, create_getter(self.new_person))
      self.rows_after_insert = self.numberOfPersons()
      self.assertTrue( self.rows_after_insert > self.rows_before_insert)
    def updateNewPerson(self):
      rows_before_update = self.numberOfPersons()
      self.assertNotEqual( self.block(lambda:self.new_person.last_name), u'Testers')
      index = self.person_proxy.index(self.rows_before_insert, self.columns['last_name'])
      self.person_proxy.setData(index, lambda:u'Testers')
      self.assertEqual( self.block(lambda:self.new_person.last_name), u'Testers')
      self.assertEqual(rows_before_update, self.numberOfPersons())
    def updateNewPersonToValid(self):
      index = self.person_proxy.index(self.rows_before_insert, self.columns['username'])
      self.person_proxy.setData(index, lambda:u'test')
    def updateNewPersonToInvalid(self):
      index = self.person_proxy.index(self.rows_before_insert, self.columns['username'])
      self.person_proxy.setData(index, lambda:None)
    def deleteNewPerson(self):
      self.person_proxy.removeRow(self.rows_before_insert)
      self.rows_after_delete = self.numberOfPersons()
      self.assertTrue( self.rows_after_delete < self.rows_after_insert )
    def testCreateUpdateDeleteValidData(self):
      self.insertNewPerson(valid=True)
      self.assertTrue( self.block(lambda:self.new_person.id) != None )
      self.updateNewPerson()
      self.deleteNewPerson()
    def testCreateUpdateDeleteInvalidData(self):
      self.insertNewPerson(valid=False)
      self.assertTrue( self.block(lambda:self.new_person.id) == None )
      self.updateNewPerson()
      self.deleteNewPerson()
    def testCreateInvalidDataUpdateToValidAndDelete(self):
      self.insertNewPerson(valid=False)
      self.assertTrue( self.block(lambda:self.new_person.id) == None )
      self.updateNewPersonToValid()
      self.assertTrue( self.block(lambda:self.new_person.id) != None )
      self.deleteNewPerson()
    def testCreateValidDataUpdateToInvalidAndDelete(self):
      self.insertNewPerson(valid=False)
      self.updateNewPersonToInvalid()
      self.deleteNewPerson()
                  
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