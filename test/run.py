# -*- coding: utf-8 -*-


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
  
#  class model_thread_tests(unittest.TestCase):
#      def setUp(self):
#        self.mt = get_model_thread()
#      def testRequestAndResponseInDifferentThread(self):
#        """Test if the request function is really executed in another thread"""
#        
#        def get_request_thread():
#          import threading
#          return threading.currentThread()
#        
#        def compare_with_response_thread(thread):
#          import threading
#          self.assertNotEqual(thread, threading.currentThread())
#          
#        event = self.mt.post( get_request_thread, compare_with_response_thread )
#        event.wait()
#        self.mt.process_responses()
        
  class ProxyEntityTest(unittest.TestCase):
    """Test the functionality of the proxies to perform CRUD operations on stand
    alone data"""
    def setUp(self):
      from camelot.model.authentication import Person, PartyAddressRoleType
      from camelot.view.proxy.queryproxy import QueryTableProxy
      from camelot.view.application_admin import ApplicationAdmin
      self.app_admin = ApplicationAdmin()
      self.mt = get_model_thread()
      self.block = self.mt.post_and_block
      person_admin = self.app_admin.getEntityAdmin(Person)
      party_address_role_type_admin = self.app_admin.getEntityAdmin(PartyAddressRoleType)
      self.person_proxy = QueryTableProxy(person_admin, lambda:Person.query, person_admin.getFields)
      self.party_address_role_type_proxy = QueryTableProxy(party_address_role_type_admin, lambda:PartyAddressRoleType.query, party_address_role_type_admin.getFields)
      # get the columns of the proxy
      self.person_columns = dict((c[0],i) for i,c in enumerate(self.block(lambda:self.person_proxy.getColumns())))
      self.rows_before_insert = 0
      self.rows_after_insert = 0
      self.rows_after_delete = 0
      self.new_person = None
      # make sure nothing is running in the model thread any more
      self.block(lambda:None)
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
      self.new_person = self.block(lambda:Person(first_name={True:u'test', False:None}[valid]))
      self.person_proxy.insertRow(0, create_getter(self.new_person))
      self.rows_after_insert = self.numberOfPersons()
      self.assertTrue( self.rows_after_insert > self.rows_before_insert)
    def updateNewPerson(self):
      rows_before_update = self.numberOfPersons()
      self.assertNotEqual( self.block(lambda:self.new_person.last_name), u'Testers')
      index = self.person_proxy.index(self.rows_before_insert, self.person_columns['last_name'])
      self.person_proxy.setData(index, lambda:u'Testers')
      self.assertEqual( self.block(lambda:self.new_person.last_name), u'Testers')
      self.assertEqual(rows_before_update, self.numberOfPersons())
    def updateNewPersonToValid(self):
      index = self.person_proxy.index(self.rows_before_insert, self.person_columns['first_name'])
      self.person_proxy.setData(index, lambda:u'test')
      index = self.person_proxy.index(self.rows_before_insert, self.person_columns['last_name'])
      self.person_proxy.setData(index, lambda:u'test')      
    def updateNewPersonToInvalid(self):
      index = self.person_proxy.index(self.rows_before_insert, self.person_columns['first_name'])
      self.person_proxy.setData(index, lambda:None)
      index = self.person_proxy.index(self.rows_before_insert, self.person_columns['last_name'])
      self.person_proxy.setData(index, lambda:None)      
    def deleteNewPerson(self):
      self.person_proxy.removeRow(self.rows_before_insert)
      self.rows_after_delete = self.numberOfPersons()
      self.assertTrue( self.rows_after_delete < self.rows_after_insert )
    def testCreateDataWithoutRequiredFields(self):
      """Create a record that has no required fields, so the creation
      should be instantaneous as opposed to delayed until all required fields are filled"""
      from camelot.model.authentication import PartyAddressRoleType
      rows_before_insert = self.block(lambda:self.party_address_role_type_proxy.getRowCount())
      new_party_address_role_type_proxy = self.block(lambda:PartyAddressRoleType())
      self.party_address_role_type_proxy.insertRow(0, create_getter(new_party_address_role_type_proxy))
      self.assertNotEqual( self.block(lambda:new_party_address_role_type_proxy.id), None )
      rows_after_insert = self.block(lambda:self.party_address_role_type_proxy.getRowCount())
      self.assertTrue( rows_after_insert > rows_before_insert)      
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
                  
  class ProxyOneToManyTest(ProxyEntityTest):
    """Test the functionality of the proxies to perform CRUD operations on related
    data"""
    def setUp(self):
      super(ProxyOneToManyTest, self).setUp()
      from elixir import session
      from camelot.view.proxy.queryproxy import QueryTableProxy
      from camelot.model.authentication import Country, City, Address, PartyAddress
      party_address_admin = self.app_admin.getEntityAdmin(PartyAddress)
      self.party_address_proxy = QueryTableProxy(party_address_admin, PartyAddress.query, party_address_admin.getFields)
      self.party_address_columns = dict((c[0],i) for i,c in enumerate(self.block(lambda:self.party_address_proxy.getColumns())))
      self.country = self.block(lambda:Country(code=u'BE', name=u'Belgium'))
      self.city = self.block(lambda:City(code=u'2000', name=u'Antwerp', country=self.country))
      self.address = self.block(lambda:Address(street1=u'Teststreet', city=self.city))
      self.block(lambda:session.flush([self.country, self.city, self.address]))
    def insertRelatedPartyAddress(self, valid):
      from camelot.model.authentication import PartyAddress
      index = self.person_proxy.index(self.rows_before_insert, self.person_columns['addresses'])
      self.block(lambda:None)
      self.related_party_address_proxy = self.person_proxy.data(index, Qt.EditRole).toPyObject()
      self.block(lambda:None)
      self.related_party_address_proxy = self.person_proxy.data(index, Qt.EditRole).toPyObject()
      self.assertNotEqual(self.related_party_address_proxy, None)
      self.party_address = self.block({True:lambda:PartyAddress(address=self.address), False:lambda:PartyAddress()}[valid])
      self.related_party_address_proxy.insertRow(0, create_getter(self.party_address))
      self.block(lambda:None)
    def testCreateBothValidDataUpdateDelete(self):
      self.insertNewPerson(valid=True)
      self.insertRelatedPartyAddress(valid=True)
      self.assertNotEqual(self.party_address.id, None)
      self.deleteNewPerson()
    def testCreateValidPersonInvalidPartyAddressUpdateDelete(self):
      self.insertNewPerson(valid=True)
      self.insertRelatedPartyAddress(valid=False)
      self.assertEqual(self.party_address.id, None)
      self.deleteNewPerson()
    def testCreateInvalidPersonValidPartyAddressUpdateDelete(self):
      self.insertNewPerson(valid=False)
      self.insertRelatedPartyAddress(valid=False)
      self.assertEqual(self.party_address.id, None)
      self.deleteNewPerson()
#    def testCreateBothInvalidUpdateDelete(self):
#      self.insertNewPerson(valid=False)
#      self.insertRelatedPartyAddress(valid=False)
#      #self.assertEqual(self.party_address.id, None)
#      self.deleteNewPerson()
    def tearDown(self):
      from elixir import session
      self.block(lambda:self.address.delete())
      self.block(lambda:self.city.delete())
      self.block(lambda:self.country.delete())
      self.block(lambda:session.flush([self.country, self.city, self.address]))
    
  import inspect
  for c in locals().values():
    if inspect.isclass(c):
      yield unittest.makeSuite(c, 'test')
      
class EditorTest(unittest.TestCase):
  """
Test the basic functionality of the editors :

- get_value
- set_value
- support for ValueLoading
"""
  
  from camelot.view.controls import editors
  from camelot.view.proxy import ValueLoading
  
  def testDateEditor(self):
    import datetime
    editor = self.editors.DateEditor()
    self.assertEqual( editor.get_value(), self.ValueLoading )
    editor.set_value( None )
    self.assertEqual( editor.get_value(), None )
    editor.set_value( datetime.date(1980, 12, 31) )
    self.assertEqual( editor.get_value(), datetime.date(1980, 12, 31) )
    editor.set_value( self.ValueLoading )
    self.assertEqual( editor.get_value(), self.ValueLoading )
    
  def testTextLineEditor(self):
    editor = self.editors.TextLineEditor(parent=None, length=10)
    self.assertEqual( editor.get_value(), self.ValueLoading )
    editor.set_value( u'za coś tam' )
    self.assertEqual( editor.get_value(), u'za coś tam' )
    editor.set_value( self.ValueLoading )
    self.assertEqual( editor.get_value(), self.ValueLoading )
 
  def testStarEditor(self):
    editor = self.editors.StarEditor(parent=None, maximum=5)
    self.assertEqual( editor.get_value(), self.ValueLoading )
    editor.set_value( 4 )
    self.assertEqual( editor.get_value(), 4 )
    editor.set_value( self.ValueLoading )
    self.assertEqual( editor.get_value(), self.ValueLoading )
         
  def testBoolEditor(self):
    editor = self.editors.BoolEditor(parent=None, editable=True)
    self.assertEqual( editor.get_value(), self.ValueLoading )
    editor.set_value( True )
    self.assertEqual( editor.get_value(), True )
    editor.set_value( False )
    self.assertEqual( editor.get_value(), False )
    editor.set_value( self.ValueLoading )
    self.assertEqual( editor.get_value(), self.ValueLoading )
    
  def testCodeEditor(self):
    editor = self.editors.CodeEditor(parent=None, parts=['AAA', '999'])
    self.assertEqual( editor.get_value(), self.ValueLoading )
    editor.set_value( ['XYZ', '123'] )
    self.assertEqual( editor.get_value(), ['XYZ', '123'] )
    editor.set_value( self.ValueLoading )
    self.assertEqual( editor.get_value(), self.ValueLoading )     

  def testColorEditor(self):
    editor = self.editors.ColorEditor(parent=None, editable=True)
    self.assertEqual( editor.get_value(), self.ValueLoading )
    editor.set_value( (255, 255, 255, 255) )
    self.assertEqual( editor.get_value(), (255, 255, 255, 255) )
    editor.set_value( self.ValueLoading )
    self.assertEqual( editor.get_value(), self.ValueLoading )
     
  def testColoredFloatEditor(self):
    editor = self.editors.ColoredFloatEditor(parent=None, editable=True)
    self.assertEqual( editor.get_value(), self.ValueLoading )
    editor.set_value( 0.0 )
    self.assertEqual( editor.get_value(), 0.0 )    
    editor.set_value( 3.14 )
    self.assertEqual( editor.get_value(), 3.14 )
    editor.set_value( self.ValueLoading )
    self.assertEqual( editor.get_value(), self.ValueLoading )
    
  def testChoicesEditor(self):
    from PyQt4 import QtCore
    editor = self.editors.ChoicesEditor(parent=None, editable=True)
    for i,(name,value) in enumerate([(u'A',1), (u'B',2), (u'C',3)]):
      editor.insertItem(i, name, QtCore.QVariant(value))
    self.assertEqual( editor.get_value(), self.ValueLoading )
    editor.set_value( 2 )
    self.assertEqual( editor.get_value(), '2' )
    editor.set_value( self.ValueLoading )
    self.assertEqual( editor.get_value(), self.ValueLoading )
    
  def testFileEditor(self):
    editor = self.editors.FileEditor(parent=None, editable=True)
    self.assertEqual( editor.get_value(), self.ValueLoading )
    editor.set_value( self.ValueLoading )
    self.assertEqual( editor.get_value(), self.ValueLoading )
    
  def testDateTimeEditor(self):
    import datetime
    editor = self.editors.DateTimeEditor(parent=None, editable=True)
    self.assertEqual( editor.get_value(), self.ValueLoading )
    editor.set_value( (2009, 7, 19, 21, 5, 10, 0) )
    self.assertEqual( editor.get_value(), datetime.datetime(2009, 7, 19, 21, 5, 0 ) )
    editor.set_value( self.ValueLoading )
    self.assertEqual( editor.get_value(), self.ValueLoading )        
       
  def testFloatEditor(self):
    editor = self.editors.FloatEditor(parent=None, editable=True)
    self.assertEqual( editor.get_value(), self.ValueLoading )
    editor.set_value( 0.0 )
    self.assertEqual( editor.get_value(), 0.0 )    
    editor.set_value( 3.14 )
    self.assertEqual( editor.get_value(), 3.14 )
    editor.set_value( self.ValueLoading )
    self.assertEqual( editor.get_value(), self.ValueLoading )
    editor.set_value('string')
    
  def testImageEditor(self):
    editor = self.editors.ImageEditor(parent=None, editable=True)
    self.assertEqual( editor.get_value(), self.ValueLoading )
    editor.set_value( self.ValueLoading )
    self.assertEqual( editor.get_value(), self.ValueLoading )
 
  def testIntegerEditor(self):
    editor = self.editors.IntegerEditor(parent=None, editable=True)
    self.assertEqual( editor.get_value(), self.ValueLoading )
    editor.set_value( 0 )
    self.assertEqual( editor.get_value(), 0 )    
    editor.set_value( 3 )
    self.assertEqual( editor.get_value(), 3 )
    editor.set_value( self.ValueLoading )
    self.assertEqual( editor.get_value(), self.ValueLoading )
 
  def testRichTextEditor(self):
    editor = self.editors.RichTextEditor(parent=None)
    self.assertEqual( editor.get_value(), self.ValueLoading )
    editor.set_value( u'<h1>Rich Text Editor</h1>' )
    self.assertTrue( u'Rich Text Editor' in editor.get_value() )
    editor.set_value( self.ValueLoading )
    self.assertEqual( editor.get_value(), self.ValueLoading )
    
  def testTimeEditor(self):
    import datetime
    editor = self.editors.TimeEditor(parent=None, editable=True)
    self.assertEqual( editor.get_value(), self.ValueLoading )
    editor.set_value( datetime.time(21, 5, 0) )
    self.assertEqual( editor.get_value(), datetime.time(21, 5, 0) )
    editor.set_value( self.ValueLoading )
    self.assertEqual( editor.get_value(), self.ValueLoading )
    
  def testVirtualAddressEditor(self):
    editor = self.editors.VirtualAddressEditor(parent=None)
    self.assertEqual( editor.get_value(), self.ValueLoading )
    editor.set_value( ('email','project-camelot@conceptive.be') )
    self.assertEqual( editor.get_value(),  ('email','project-camelot@conceptive.be') )
    editor.set_value( self.ValueLoading )
    self.assertEqual( editor.get_value(), self.ValueLoading )    
                            
class DelegateTest(unittest.TestCase):
  """Test the basic functionallity of the delegates :
- createEditor
- setEditorData
- setModelData
"""
 
  from camelot.view.controls import delegates
  from camelot.view.controls import editors
    
  def setUp(self):
    self.kwargs = dict(editable=True)

  def testPlainTextColumnDelegate(self):
    delegate = self.delegates.PlainTextColumnDelegate(parent=None,
                                                      length=True,
                                                      **self.kwargs)
    editor = delegate.createEditor(None, None, None)
    self.assertTrue(isinstance(editor, self.editors.TextLineEditor))

  def testTextEditColumnDelegate(self):
    from PyQt4.QtGui import QTextEdit
    delegate = self.delegates.TextEditColumnDelegate(parent=None, **self.kwargs)
    editor = delegate.createEditor(None, None, None)
    self.assertTrue(isinstance(editor, QTextEdit))

  def testRichTextColumnDelegate(self):
    delegate = self.delegates.RichTextColumnDelegate(parent=None, **self.kwargs)
    editor = delegate.createEditor(None, None, None)
    self.assertTrue(isinstance(editor, self.editors.RichTextEditor))
    
  def testBoolColumnDelegate(self):
    delegate = self.delegates.BoolColumnDelegate(parent=None, **self.kwargs)
    editor = delegate.createEditor(None, None, None)
    self.assertTrue(isinstance(editor, self.editors.BoolEditor))
  
  def testDateColumnDelegate(self):
    delegate = self.delegates.DateColumnDelegate(parent=None, **self.kwargs)
    editor = delegate.createEditor(None, None, None)
    self.assertTrue(isinstance(editor, self.editors.DateEditor))

  def testDateTimeColumnDelegate(self):
    delegate = self.delegates.DateTimeColumnDelegate(parent=None, **self.kwargs)
    editor = delegate.createEditor(None, None, None)
    self.assertTrue(isinstance(editor, self.editors.DateTimeEditor))

  def testTimeColumnDelegate(self):
    delegate = self.delegates.TimeColumnDelegate(parent=None, **self.kwargs)
    editor = delegate.createEditor(None, None, None)
    self.assertTrue(isinstance(editor, self.editors.TimeEditor))

  def testIntegerColumnDelegate(self):
    delegate = self.delegates.IntegerColumnDelegate(parent=None, **self.kwargs)
    editor = delegate.createEditor(None, None, None)
    self.assertTrue(isinstance(editor, self.editors.IntegerEditor))

  def testFloatColumnDelegate(self):
    from camelot.core.constants import camelot_minfloat, camelot_maxfloat
    delegate = self.delegates.FloatColumnDelegate(parent=None, **self.kwargs)
    editor = delegate.createEditor(None, None, None)
    self.assertTrue(isinstance(editor, self.editors.FloatEditor))
    self.assertEqual(delegate.minimum, camelot_minfloat)
    self.assertEqual(delegate.maximum, camelot_maxfloat)

  def testColoredFloatColumnDelegate(self):
    delegate = self.delegates.ColoredFloatColumnDelegate(parent=None,
                                                         **self.kwargs)
    editor = delegate.createEditor(None, None, None)
    self.assertTrue(isinstance(editor, self.editors.ColoredFloatEditor))
  
  def testStarDelegate(self):
    delegate = self.delegates.StarDelegate(parent=None, **self.kwargs)
    editor = delegate.createEditor(None, None, None)
    self.assertTrue(delegate.maximum, 5)
    self.assertTrue(isinstance(editor, self.editors.StarEditor))

  def testFileDelegate(self):
    delegate = self.delegates.FileDelegate(parent=None, **self.kwargs)
    editor = delegate.createEditor(None, None, None)
    self.assertTrue(isinstance(editor, self.editors.FileEditor))

  def testColorColumnDelegate(self):
    delegate = self.delegates.ColorColumnDelegate(parent=None, **self.kwargs)
    editor = delegate.createEditor(None, None, None)
    self.assertTrue(isinstance(editor, self.editors.ColorEditor))
  
  def testCodeColumnDelegate(self):
    delegate = self.delegates.CodeColumnDelegate(parent=None, **self.kwargs)
    editor = delegate.createEditor(None, None, None)
    self.assertTrue(isinstance(editor, self.editors.CodeEditor))
  
  def testComboBoxColumnDelegate(self):
    CHOICES = ('1', '2', '3')
    delegate = self.delegates.ComboBoxColumnDelegate(parent=None,
                                                     choices=CHOICES,
                                                     **self.kwargs)
    editor = delegate.createEditor(None, None, None)
    self.assertTrue(isinstance(editor, self.editors.ChoicesEditor))

  def testImageColumnDelegate(self):
    delegate = self.delegates.ImageColumnDelegate(parent=None, **self.kwargs)
    editor = delegate.createEditor(None, None, None)
    self.assertTrue(isinstance(editor, self.editors.ImageEditor))

  def testVirtualAddressColumnDelegate(self):
    delegate = self.delegates.VirtualAddressColumnDelegate(parent=None,
                                                           **self.kwargs)
    editor = delegate.createEditor(None, None, None)
    self.assertTrue(isinstance(editor, self.editors.VirtualAddressEditor))


if __name__ == '__main__':
  logger.info('running unit tests')
  import sys
  app = QApplication(sys.argv)
  
  editor_test =  unittest.makeSuite(EditorTest, 'test')
  runner=unittest.TextTestRunner(verbosity=2)
  runner.run(editor_test)
  editor_test =  unittest.makeSuite(DelegateTest, 'test')
  runner=unittest.TextTestRunner(verbosity=2)
  runner.run(editor_test)  
  sys.exit()
