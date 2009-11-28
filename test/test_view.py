# -*- coding: utf-8 -*-
from PyQt4 import QtGui

import logging
import unittest
import os

from camelot.test import ModelThreadTestCase, EntityViewsTest, SchemaTest
from PyQt4.QtGui import *
from PyQt4.QtCore import *

logger = logging.getLogger('view.unittests')

static_images_path = os.path.join(os.path.dirname(__file__), '..', 'doc', 'sphinx', 'source', '_static')

def create_getter(getable):
  
    def getter():
        return getable
    
    return getter
        
#class ProxyEntityTest(ModelThreadTestCase):
#  """Test the functionality of the proxies to perform CRUD operations on stand
#  alone data"""
#  def setUp(self):
#    ModelThreadTestCase.setUp(self)
#    from camelot.model.authentication import Person, PartyAddressRoleType
#    from camelot.view.proxy.queryproxy import QueryTableProxy
#    from camelot.view.application_admin import ApplicationAdmin
#    self.app_admin = ApplicationAdmin()
#    self.block = self.mt.post_and_block
#    person_admin = self.app_admin.getEntityAdmin(Person)
#    party_address_role_type_admin = self.app_admin.getEntityAdmin(PartyAddressRoleType)
#    self.person_proxy = QueryTableProxy(person_admin, lambda:Person.query, person_admin.get_fields)
#    self.party_address_role_type_proxy = QueryTableProxy(party_address_role_type_admin, lambda:PartyAddressRoleType.query, party_address_role_type_admin.get_fields)
#    # get the columns of the proxy
#    self.person_columns = dict((c[0],i) for i,c in enumerate(self.block(lambda:self.person_proxy.getColumns())))
#    self.rows_before_insert = 0
#    self.rows_after_insert = 0
#    self.rows_after_delete = 0
#    self.new_person = None
#    # make sure nothing is running in the model thread any more
#    self.block(lambda:None)
#  def listPersons(self):
#    from camelot.model.authentication import Person
#    
#    def create_list():
#      print '<persons>'
#      for p in Person.query.all():
#        print p.id, unicode(p)
#      print '</persons>'
#    
#    self.block(create_list)
#  def numberOfPersons(self):
#    return self.block(lambda:self.person_proxy.getRowCount())
#  def insertNewPerson(self, valid):
#    from camelot.model.authentication import Person
#    self.rows_before_insert = self.numberOfPersons()
#    self.new_person = self.block(lambda:Person(first_name={True:u'test', False:None}[valid], last_name='test'))
#    self.person_proxy.insertRow(0, create_getter(self.new_person))
#    self.rows_after_insert = self.numberOfPersons()
#    self.assertTrue( self.rows_after_insert > self.rows_before_insert)
#  def updateNewPerson(self):
#    rows_before_update = self.numberOfPersons()
#    self.assertNotEqual( self.block(lambda:self.new_person.last_name), u'Testers')
#    index = self.person_proxy.index(self.rows_before_insert, self.person_columns['last_name'])
#    self.person_proxy.setData(index, lambda:u'Testers')
#    self.assertEqual( self.block(lambda:self.new_person.last_name), u'Testers')
#    self.assertEqual(rows_before_update, self.numberOfPersons())
#  def updateNewPersonToValid(self):
#    index = self.person_proxy.index(self.rows_before_insert, self.person_columns['first_name'])
#    self.person_proxy.setData(index, lambda:u'test')
#    index = self.person_proxy.index(self.rows_before_insert, self.person_columns['last_name'])
#    self.person_proxy.setData(index, lambda:u'test')      
#  def updateNewPersonToInvalid(self):
#    index = self.person_proxy.index(self.rows_before_insert, self.person_columns['first_name'])
#    self.person_proxy.setData(index, lambda:None)
#    index = self.person_proxy.index(self.rows_before_insert, self.person_columns['last_name'])
#    self.person_proxy.setData(index, lambda:None)      
#  def deleteNewPerson(self):
#    self.person_proxy.removeRow(self.rows_before_insert)
#    self.rows_after_delete = self.numberOfPersons()
#    self.assertTrue( self.rows_after_delete < self.rows_after_insert )
#  def testCreateDataWithoutRequiredFields(self):
#    """Create a record that has no required fields, so the creation
#    should be instantaneous as opposed to delayed until all required fields are filled"""
#    from camelot.model.authentication import PartyAddressRoleType
#    rows_before_insert = self.block(lambda:self.party_address_role_type_proxy.getRowCount())
#    new_party_address_role_type_proxy = self.block(lambda:PartyAddressRoleType())
#    self.party_address_role_type_proxy.insertRow(0, create_getter(new_party_address_role_type_proxy))
#    self.assertNotEqual( self.block(lambda:new_party_address_role_type_proxy.id), None )
#    rows_after_insert = self.block(lambda:self.party_address_role_type_proxy.getRowCount())
#    self.assertTrue( rows_after_insert > rows_before_insert)      
#  def testCreateUpdateDeleteValidData(self):
#    self.insertNewPerson(valid=True)
#    self.assertTrue( self.block(lambda:self.new_person.id) != None )
#    self.updateNewPerson()
#    self.deleteNewPerson()
#  def testCreateUpdateDeleteInvalidData(self):
#    self.insertNewPerson(valid=False)
#    self.assertTrue( self.block(lambda:self.new_person.id) == None )
#    self.updateNewPerson()
#    self.deleteNewPerson()
#  def testCreateInvalidDataUpdateToValidAndDelete(self):
#    self.insertNewPerson(valid=False)
#    self.assertTrue( self.block(lambda:self.new_person.id) == None )
#    self.updateNewPersonToValid()
#    self.assertTrue( self.block(lambda:self.new_person.id) != None )
#    self.deleteNewPerson()
#  def testCreateValidDataUpdateToInvalidAndDelete(self):
#    self.insertNewPerson(valid=False)
#    self.updateNewPersonToInvalid()
#    self.deleteNewPerson()

                
#class ProxyOneToManyTest(ProxyEntityTest):
#  """Test the functionality of the proxies to perform CRUD operations on related
#  data"""
#  def setUp(self):
#    super(ProxyOneToManyTest, self).setUp()
#    from elixir import session
#    from camelot.view.proxy.queryproxy import QueryTableProxy
#    from camelot.model.authentication import Country, City, Address, PartyAddress
#    party_address_admin = self.app_admin.getEntityAdmin(PartyAddress)
#    self.party_address_proxy = QueryTableProxy(party_address_admin, PartyAddress.query, party_address_admin.get_fields)
#    self.party_address_columns = dict((c[0],i) for i,c in enumerate(self.block(lambda:self.party_address_proxy.getColumns())))
#    self.country = self.block(lambda:Country(code=u'BE', name=u'Belgium'))
#    self.city = self.block(lambda:City(code=u'2000', name=u'Antwerp', country=self.country))
#    self.address = self.block(lambda:Address(street1=u'Teststreet', city=self.city))
#    self.block(lambda:session.flush([self.country, self.city, self.address]))
#  def insertRelatedPartyAddress(self, valid):
#    from camelot.model.authentication import PartyAddress
#    index = self.person_proxy.index(self.rows_before_insert, self.person_columns['addresses'])
#    self.block(lambda:None)
#    self.related_party_address_proxy = self.person_proxy.data(index, Qt.EditRole).toPyObject()
#    self.block(lambda:None)
#    self.related_party_address_proxy = self.person_proxy.data(index, Qt.EditRole).toPyObject()
#    self.assertNotEqual(self.related_party_address_proxy, None)
#    self.party_address = self.block({True:lambda:PartyAddress(address=self.address), False:lambda:PartyAddress()}[valid])
#    self.related_party_address_proxy.insertRow(0, create_getter(self.party_address))
#    self.block(lambda:None)
#  def testCreateBothValidDataUpdateDelete(self):
#    self.insertNewPerson(valid=True)
#    self.insertRelatedPartyAddress(valid=True)
#    self.assertNotEqual(self.party_address.id, None)
#    self.deleteNewPerson()
#  def testCreateValidPersonInvalidPartyAddressUpdateDelete(self):
#    self.insertNewPerson(valid=True)
#    self.insertRelatedPartyAddress(valid=False)
#    self.assertEqual(self.party_address.id, None)
#    self.deleteNewPerson()
#  def testCreateInvalidPersonValidPartyAddressUpdateDelete(self):
#    self.insertNewPerson(valid=False)
#    self.insertRelatedPartyAddress(valid=False)
#    self.assertEqual(self.party_address.id, None)
#    self.deleteNewPerson()
#  def tearDown(self):
#    from elixir import session
#    self.block(lambda:self.address.delete())
#    self.block(lambda:self.city.delete())
#    self.block(lambda:self.country.delete())
#    self.block(lambda:session.flush([self.country, self.city, self.address]))
      
class EditorsTest(ModelThreadTestCase):
  """
Test the basic functionality of the editors :

- get_value
- set_value
- support for ValueLoading
"""
  
  images_path = static_images_path
  
  from camelot.view.controls import editors
  from camelot.view.proxy import ValueLoading

  def test_DateEditor(self):
    import datetime
    editor = self.editors.DateEditor()
    self.assertEqual( editor.get_value(), self.ValueLoading )
    editor.set_value( None )
    self.assertEqual( editor.get_value(), None )
    editor.set_value( datetime.date(1980, 12, 31) )
    self.grab_widget( editor, 'editable' )
    self.assertEqual( editor.get_value(), datetime.date(1980, 12, 31) )
    editor.set_value( self.ValueLoading )
    self.assertEqual( editor.get_value(), self.ValueLoading )
    editor = self.editors.DateEditor(editable=False)
    self.assertEqual( editor.get_value(), self.ValueLoading )
    editor.set_value( None )
    self.assertEqual( editor.get_value(), None )
    editor.set_value( datetime.date(1980, 12, 31) )
    self.grab_widget( editor, 'disabled' )
    self.assertEqual( editor.get_value(), datetime.date(1980, 12, 31) )
    editor.set_value( self.ValueLoading )
    self.assertEqual( editor.get_value(), self.ValueLoading )
    editor.set_value( datetime.date(2008, 3, 28) )
    editor.set_enabled( True )
    self.grab_widget( editor, 'set_enabled()_editable' )
    
  def test_TextLineEditor(self):
    editor = self.editors.TextLineEditor(parent=None, length=10)
    self.assertEqual( editor.get_value(), self.ValueLoading )
    editor.set_value( u'za coś tam' )
    self.grab_widget( editor, 'editable' )
    self.assertEqual( editor.get_value(), u'za coś tam' )
    editor.set_value( self.ValueLoading )
    self.assertEqual( editor.get_value(), self.ValueLoading )
    editor = self.editors.TextLineEditor(parent=None, length=10, editable=False)
    self.assertEqual( editor.get_value(), self.ValueLoading )
    editor.set_value( u'za coś tam' )
    self.grab_widget( editor, 'disabled' )
    self.assertEqual( editor.get_value(), u'za coś tam' )
    editor.set_value( self.ValueLoading )
    self.assertEqual( editor.get_value(), self.ValueLoading )
    editor.set_value( u'editor.set_enabled() Test' )
    editor.set_enabled( True )
    self.grab_widget( editor, 'set_enabled()_editable' )
 
  def test_StarEditor(self):
    editor = self.editors.StarEditor(parent=None, maximum=5)
    self.assertEqual( editor.get_value(), self.ValueLoading )
    editor.set_value( 4 )
    self.grab_widget( editor, 'editable' )
    self.assertEqual( editor.get_value(), 4 )
    editor.set_value( self.ValueLoading )
    self.assertEqual( editor.get_value(), self.ValueLoading )
    editor = self.editors.StarEditor(parent=None, maximum=5, editable=False)
    self.assertEqual( editor.get_value(), self.ValueLoading )
    editor.set_value( 4 )
    self.grab_widget( editor, 'disabled' )
    self.assertEqual( editor.get_value(), 4 )
    editor.set_value( self.ValueLoading )
    self.assertEqual( editor.get_value(), self.ValueLoading )
    editor.set_value( 5 )
    editor.set_enabled( True )
    self.grab_widget( editor, 'set_enabled()_editable' )
    
  def test_SmileyEditor(self):
    editor = self.editors.SmileyEditor(parent=None)
    self.assertEqual( editor.get_value(), self.ValueLoading )
    editor.set_value( 'face-devil-grin' )
    self.grab_widget( editor, 'editable' )
    self.assertEqual( editor.get_value(), 'face-devil-grin' )
    editor.set_value( self.ValueLoading )
    self.assertEqual( editor.get_value(), self.ValueLoading )
    editor = self.editors.SmileyEditor(parent=None, editable=False)
    self.assertEqual( editor.get_value(), self.ValueLoading )
    editor.set_value( 'face-kiss' )
    self.grab_widget( editor, 'disabled' )
    self.assertEqual( editor.get_value(), 'face-kiss' )
    editor.set_value( self.ValueLoading )
    self.assertEqual( editor.get_value(), self.ValueLoading )
    editor.set_value( 'face-monkey' )
    editor.set_enabled( True )
    self.grab_widget( editor, 'set_enabled()_editable' )
      
  def test_BoolEditor(self):
    editor = self.editors.BoolEditor(parent=None, editable=False)
    self.assertEqual( editor.get_value(), self.ValueLoading )
    editor.set_value( True )
    self.grab_widget( editor, 'editable' )
    self.assertEqual( editor.get_value(), True )
    editor.set_value( False )
    self.assertEqual( editor.get_value(), False )
    editor.set_value( self.ValueLoading )
    self.assertEqual( editor.get_value(), self.ValueLoading )
    editor = self.editors.BoolEditor(parent=None, editable=False)
    self.assertEqual( editor.get_value(), self.ValueLoading )
    editor.set_value( True )
    self.grab_widget( editor, 'disabled' )
    self.assertEqual( editor.get_value(), True )
    editor.set_value( False )
    self.assertEqual( editor.get_value(), False )
    editor.set_value( self.ValueLoading )
    self.assertEqual( editor.get_value(), self.ValueLoading )
    editor.set_value( True )
    editor.set_enabled( True )
    self.grab_widget( editor, 'set_enabled()_editable' )
    
  def test_CodeEditor(self):
    editor = self.editors.CodeEditor(parent=None, parts=['AAA', '999'])
    self.assertEqual( editor.get_value(), self.ValueLoading )
    editor.set_value( ['XYZ', '123'] )
    self.grab_widget( editor, 'editable' )
    self.assertEqual( editor.get_value(), ['XYZ', '123'] )
    editor.set_value( self.ValueLoading )
    self.assertEqual( editor.get_value(), self.ValueLoading ) 
    editor = self.editors.CodeEditor(parent=None, parts=['AAA', '999'], editable=False)
    self.assertEqual( editor.get_value(), self.ValueLoading )
    editor.set_value( ['XYZ', '123'] )
    self.grab_widget( editor, 'disabled' )
    self.assertEqual( editor.get_value(), ['XYZ', '123'] )
    editor.set_value( self.ValueLoading )
    self.assertEqual( editor.get_value(), self.ValueLoading )
    editor.set_value( ['SAM', '321'] )
    editor.set_enabled( True )
    self.grab_widget( editor, 'set_enabled()_editable' )    

  def test_ColorEditor(self):
    editor = self.editors.ColorEditor(parent=None, editable=True)
    self.assertEqual( editor.get_value(), self.ValueLoading )
    editor.set_value( (255, 200, 255, 255) )
    self.grab_widget( editor, 'editable' )
    self.assertEqual( editor.get_value(), (255, 200, 255, 255) )
    editor.set_value( self.ValueLoading )
    self.assertEqual( editor.get_value(), self.ValueLoading )
    editor = self.editors.ColorEditor(parent=None, editable=False)
    self.assertEqual( editor.get_value(), self.ValueLoading )
    editor.set_value( (255, 200, 255, 255) )
    self.grab_widget( editor, 'disabled' )
    self.assertEqual( editor.get_value(), (255, 200, 255, 255) )
    editor.set_value( self.ValueLoading )
    self.assertEqual( editor.get_value(), self.ValueLoading )
    editor.set_value( (150, 200, 100, 255) )
    editor.set_enabled( True )
    self.grab_widget( editor, 'set_enabled()_editable' )
     
  def test_ColoredFloatEditor(self):
    editor = self.editors.ColoredFloatEditor(parent=None, editable=True)
    self.assertEqual( editor.get_value(), self.ValueLoading )
    editor.set_value( 0.0 )
    self.assertEqual( editor.get_value(), 0.0 )    
    editor.set_value( 3.14 )
    self.grab_widget( editor, 'editable' )
    self.assertEqual( editor.get_value(), 3.14 )
    editor.set_value( self.ValueLoading )
    self.assertEqual( editor.get_value(), self.ValueLoading )
    editor = self.editors.ColoredFloatEditor(parent=None, editable=False)
    self.assertEqual( editor.get_value(), self.ValueLoading )
    editor.set_value( 0.0 )
    self.assertEqual( editor.get_value(), 0.0 )    
    editor.set_value( 3.14 )
    self.grab_widget( editor,'disabled' )
    self.assertEqual( editor.get_value(), 3.14 )
    editor.set_value( self.ValueLoading )
    self.assertEqual( editor.get_value(), self.ValueLoading )
    editor.set_value( -7.45 )
    editor.set_enabled( True )
    self.grab_widget( editor, 'set_enabled()_editable' )
    
  def test_ChoicesEditor(self):
    editor = self.editors.ChoicesEditor(parent=None, editable=True)
    choices1 = [(1,u'A'), (2,u'B'), (3,u'C')]
    editor.set_choices( choices1 )
    self.assertEqual( editor.get_value(), self.ValueLoading )
    editor.set_value( 2 )
    self.assertEqual(editor.get_choices(), choices1 )
    self.grab_widget( editor, 'editable' )
    self.assertEqual( editor.get_value(), 2 )
    # now change the choices
    choices2 = [(4,u'D'), (5,u'E'), (6,u'F')]
    editor.set_choices( choices2 )
    self.assertEqual(editor.get_choices(), choices2 + [(2,u'B')])
    editor.set_value( self.ValueLoading )
    self.assertEqual( editor.get_value(), self.ValueLoading )
    editor = self.editors.ChoicesEditor(parent=None, editable=False)
    editor.set_choices(choices1)
    self.assertEqual( editor.get_value(), self.ValueLoading )
    editor.set_value( 2 )
    self.grab_widget( editor, 'disabled' )
    self.assertEqual( editor.get_value(), 2 )
    editor.set_value( self.ValueLoading )
    self.assertEqual( editor.get_value(), self.ValueLoading )
    editor.set_value( 1 )
    editor.set_enabled( True )
    self.grab_widget( editor, 'set_enabled()_editable' )
    
  def test_FileEditor(self):
    editor = self.editors.FileEditor(parent=None, editable=True)
    self.assertEqual( editor.get_value(), self.ValueLoading )
    editor.set_value( self.ValueLoading )
    self.grab_widget( editor, 'editable' )
    self.assertEqual( editor.get_value(), self.ValueLoading )
    editor = self.editors.FileEditor(parent=None, editable=False)
    self.assertEqual( editor.get_value(), self.ValueLoading )
    editor.set_value( self.ValueLoading )
    self.grab_widget( editor, 'disabled' )
    self.assertEqual( editor.get_value(), self.ValueLoading )
    editor.set_enabled( True )
    self.grab_widget( editor, 'set_enabled()_editable' )
    
  def test_DateTimeEditor(self):
    import datetime
    editor = self.editors.DateTimeEditor(parent=None, editable=True)
    self.assertEqual( editor.get_value(), self.ValueLoading )
    editor.set_value( datetime.datetime(2009, 7, 19, 21, 5, 10, 0) )
    self.assertEqual( editor.get_value(), datetime.datetime(2009, 7, 19, 21, 5, 0 ) )
    self.grab_widget( editor, 'editable' )
    editor.set_value( self.ValueLoading )
    self.assertEqual( editor.get_value(), self.ValueLoading )    
    editor = self.editors.DateTimeEditor(parent=None, editable=False)
    self.assertEqual( editor.get_value(), self.ValueLoading )
    editor.set_value( datetime.datetime(2009, 7, 19, 21, 5, 10, 0) )
    self.assertEqual( editor.get_value(), datetime.datetime(2009, 7, 19, 21, 5, 0 ) )
    self.grab_widget( editor, 'disabled' )
    editor.set_value( self.ValueLoading )
    self.assertEqual( editor.get_value(), self.ValueLoading ) 
    editor.set_value( datetime.datetime(2009, 5, 21, 16, 16, 5, 0) )
    editor.set_enabled( True )
    self.grab_widget( editor, 'set_enabled()_editable' )   
       
  def test_FloatEditor(self):
    editor = self.editors.FloatEditor(parent=None, editable=True, prefix='prefix')
    self.assertEqual( editor.get_value(), self.ValueLoading )
    editor.set_value( 0.0 )
    self.assertEqual( editor.get_value(), 0.0 )    
    editor.set_value( 3.14 )
    self.grab_widget( editor, 'editable' )
    self.assertEqual( editor.get_value(), 3.14 )
    editor.set_value( self.ValueLoading )
    self.assertEqual( editor.get_value(), self.ValueLoading )
    editor = self.editors.FloatEditor(parent=None, editable=False, suffix='suffix')
    self.assertEqual( editor.get_value(), self.ValueLoading )
    editor.set_value( 0.0 )
    self.assertEqual( editor.get_value(), 0.0 )
    editor.set_value( 3.14 )
    self.grab_widget( editor, 'disabled' )
    self.assertEqual( editor.get_value(), 3.14 )
    editor.set_value( self.ValueLoading )
    self.assertEqual( editor.get_value(), self.ValueLoading )
    editor.set_value( 5.45 )
    editor.set_enabled( True )
    self.grab_widget( editor, 'set_enabled()_editable' )
    
  def test_ImageEditor(self):
    editor = self.editors.ImageEditor(parent=None, editable=True)
    self.assertEqual( editor.get_value(), self.ValueLoading )
    editor.set_value( self.ValueLoading )
    self.assertEqual( editor.get_value(), self.ValueLoading )
    self.grab_widget( editor, 'editable' )
    editor = self.editors.ImageEditor(parent=None, editable=False)
    self.assertEqual( editor.get_value(), self.ValueLoading )
    editor.set_value( self.ValueLoading )
    self.assertEqual( editor.get_value(), self.ValueLoading )
    self.grab_widget( editor, 'disabled' )
    editor.set_enabled( True )
    self.grab_widget( editor, 'set_enabled()_editable' )
 
  def test_IntegerEditor(self):
    editor = self.editors.IntegerEditor(parent=None, editable=True)
    self.assertEqual( editor.get_value(), self.ValueLoading )
    editor.set_value( 0 )
    self.assertEqual( editor.get_value(), 0 )    
    editor.set_value( 3 )
    self.grab_widget( editor, 'editable' )
    self.assertEqual( editor.get_value(), 3 )
    editor.set_value( self.ValueLoading )
    self.assertEqual( editor.get_value(), self.ValueLoading )
    editor = self.editors.IntegerEditor(parent=None, editable=False)
    self.assertEqual( editor.get_value(), self.ValueLoading )
    editor.set_value( 0 )
    self.assertEqual( editor.get_value(), 0 )    
    editor.set_value( 3 )
    self.grab_widget( editor, 'disabled' )
    self.assertEqual( editor.get_value(), 3 )
    editor.set_value( self.ValueLoading )
    self.assertEqual( editor.get_value(), self.ValueLoading )
    editor.set_value( 134 )
    editor.set_enabled( True )
    self.grab_widget( editor, 'set_enabled()_editable' )
 
  def test_RichTextEditor(self):
    editor = self.editors.RichTextEditor(parent=None)
    self.assertEqual( editor.get_value(), self.ValueLoading )
    editor.set_value( u'<h1>Rich Text Editor</h1>' )
    self.grab_widget( editor, 'editable' )
    self.assertTrue( u'Rich Text Editor' in editor.get_value() )
    editor.set_value( self.ValueLoading )
    self.assertEqual( editor.get_value(), self.ValueLoading )
    editor = self.editors.RichTextEditor(parent=None, editable=False)
    self.assertEqual( editor.get_value(), self.ValueLoading )
    editor.set_value( u'<h1>Rich Text Editor</h1>' )
    self.grab_widget( editor, 'disabled' )
    self.assertTrue( u'Rich Text Editor' in editor.get_value() )
    editor.set_value( self.ValueLoading )
    self.assertEqual( editor.get_value(), self.ValueLoading )
    editor.set_value( u'<h2>Rich Text Editor, set_enabled() test</h2>' )
    editor.set_enabled( True )
    self.grab_widget( editor, 'set_enabled()_editable' )
    
  def test_TimeEditor(self):
    import datetime
    editor = self.editors.TimeEditor(parent=None, editable=True)
    self.assertEqual( editor.get_value(), self.ValueLoading )
    editor.set_value( datetime.time(21, 5, 0) )
    self.grab_widget( editor, 'editable' )
    self.assertEqual( editor.get_value(), datetime.time(21, 5, 0) )
    editor.set_value( self.ValueLoading )
    self.assertEqual( editor.get_value(), self.ValueLoading )
    editor = self.editors.TimeEditor(parent=None, editable=False)
    self.assertEqual( editor.get_value(), self.ValueLoading )
    editor.set_value( datetime.time(21, 5, 0) )
    self.grab_widget( editor, 'disabled' )
    self.assertEqual( editor.get_value(), datetime.time(21, 5, 0) )
    editor.set_value( self.ValueLoading )
    self.assertEqual( editor.get_value(), self.ValueLoading )
    editor.set_value( datetime.time(15, 6, 3) )
    editor.set_enabled( True )
    self.grab_widget( editor, 'set_enabled()_editable' )
    
  def test_VirtualAddressEditor(self):
    editor = self.editors.VirtualAddressEditor(parent=None)
    self.assertEqual( editor.get_value(), self.ValueLoading )
    editor.set_value( ('im','test') )
    self.grab_widget( editor, 'editable' )
    self.assertEqual( editor.get_value(),  ('im','test') )
    editor.set_value( self.ValueLoading )
    self.assertEqual( editor.get_value(), self.ValueLoading )  
    editor = self.editors.VirtualAddressEditor(parent=None, editable=False)
    self.assertEqual( editor.get_value(), self.ValueLoading )
    editor.set_value( ('im','test') )
    self.grab_widget( editor, 'disabled' )
    self.assertEqual( editor.get_value(),  ('im','test') )
    editor.set_value( self.ValueLoading )
    self.assertEqual( editor.get_value(), self.ValueLoading )
    editor.set_value( ('email', 'test@conceptive.be') )
    editor.set_enabled( True )
    self.grab_widget( editor, 'set_enabled()_editable' )  
  
from camelot.view import forms
  
class FormTest(ModelThreadTestCase):
    
  images_path = static_images_path
  
  def setUp(self):
    ModelThreadTestCase.setUp(self)
    from camelot.view.controls.editors import TextLineEditor, DateEditor
    self.widgets = {
      'title':(QLabel('Title'), TextLineEditor(parent=None, editable=True)),
      'short_description':(QLabel('Short description'), TextLineEditor(parent=None, editable=True)),
      'director':(QLabel('Director'), TextLineEditor(parent=None, editable=True)),
      'release_date':(QLabel('Release date'), DateEditor(parent=None, editable=True)),
    }
    from elixir import entities
    self.entities = [e for e in entities]
    from camelot.admin.application_admin import ApplicationAdmin
    from camelot.model.authentication import Person
    self.app_admin = ApplicationAdmin()
    self.person_entity = Person
    self.collection_getter = lambda:[Person()]   
    
  def tearDown(self):
    #
    # The global list of entities should remain clean for subsequent tests
    #
    from elixir import entities
    for e in entities:
      if e not in self.entities:
        entities.remove(e)
    
  def test_form(self):
    from snippet.form.simple_form import Movie
    self.grab_widget(Movie.Admin.form_display.render(self.widgets))
    
  def test_tab_form(self):
    form = forms.TabForm([('First tab', ['title', 'short_description']),
                          ('Second tab', ['director', 'release_date'])])
    self.grab_widget(form.render(self.widgets))
    
  def test_group_box_form(self):
    form = forms.GroupBoxForm('Movie', ['title', 'short_description'])
    self.grab_widget(form.render(self.widgets))
    
  def test_grid_form(self):
    form = forms.GridForm([['title', 'short_description'], ['director','release_date']])
    self.grab_widget(form.render(self.widgets))
    
  def test_vbox_form(self):
    form = forms.VBoxForm([['title', 'short_description'], ['director', 'release_date']])
    self.grab_widget(form.render(self.widgets))
    
  def test_hbox_form(self):
    form = forms.HBoxForm([['title', 'short_description'], ['director', 'release_date']])
    self.grab_widget(form.render(self.widgets))
    
  def test_nested_form(self):
      from snippet.form.nested_form import Admin
      person_admin = Admin(self.app_admin, self.person_entity)
      self.grab_widget( person_admin.create_new_view() )
      
  def test_inherited_form(self):
      from snippet.form.inherited_form import InheritedAdmin
      person_admin = InheritedAdmin(self.app_admin, self.person_entity)
      self.grab_widget( person_admin.create_new_view() )
      
  def test_custom_layout(self):
      from snippet.form.custom_layout import Admin
      person_admin = Admin(self.app_admin, self.person_entity)
      self.grab_widget( person_admin.create_new_view() )      
                          
from camelot.admin import form_action
  
class FormActionTest(ModelThreadTestCase):
    
  images_path = static_images_path
  
  def test_print_html_form_action(self):
    action = form_action.PrintHtmlFormAction('Summary')
    widget = action.render(None, None)
    self.grab_widget(widget)
                            
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
    self.option = QtGui.QStyleOptionViewItem()
    # set version to 5 to indicate the widget will appear on a
    # a form view and not on a table view, so it should not
    # set its background
    self.option.version = 5

  def grab_delegate(self, delegate, data, suffix='editable'):
    import sys
    from camelot.view.controls.tableview import TableWidget
    from PyQt4.QtCore import Qt
    
    model = QStandardItemModel(1, 1)
    index = model.index(0, 0, QModelIndex())
    model.setData(index, QVariant(data))
    model.setData(index, QVariant(QtGui.QColor('white')), Qt.BackgroundRole)
    
    option = QtGui.QStyleOptionViewItem()
    
    if suffix == 'editable':
      self.assertTrue(delegate.sizeHint(option, index).height()>1)
    
    tableview = TableWidget()
    tableview.setModel(model)
    tableview.setItemDelegate(delegate)
    
    test_case_name = sys._getframe(1).f_code.co_name[4:]
    
    for state_name, state in zip(('selected', 'unselected'), 
                                 (QStyle.State_Selected, QStyle.State_None)):
      tableview.adjustSize()
      
      if state == QStyle.State_Selected:
        tableview.selectionModel().select(index, QItemSelectionModel.Select)
      else:
        tableview.selectionModel().select(index, QItemSelectionModel.Clear)
      
      cell_size = tableview.visualRect(index).size()
      
      headers_size = QSize(tableview.verticalHeader().width(),
                           tableview.horizontalHeader().height())
      
      extra_size = QSize(tableview.verticalScrollBar().width(),
                         tableview.horizontalScrollBar().height())

      tableview.resize(cell_size + headers_size + extra_size)

      # TODO checks if path exists
      delegate_images_path = os.path.join(static_images_path, 'delegates')
      if not os.path.exists(delegate_images_path):
        os.makedirs(delegate_images_path)
      pixmap = QPixmap.grabWidget(tableview)
      pixmap.save(os.path.join(delegate_images_path, '%s_%s_%s.png'%(test_case_name, state_name, suffix)),
                  'PNG')
            
  def testPlainTextDelegate(self):
    delegate = self.delegates.PlainTextDelegate(parent=None,
                                                length=30,
                                                editable=True)
    editor = delegate.createEditor(None, self.option, None)
    self.assertEqual(editor.maxLength(), 30)
    self.assertTrue(isinstance(editor, self.editors.TextLineEditor))
    self.grab_delegate(delegate, 'Plain Text')
    delegate = self.delegates.PlainTextDelegate(parent=None,
                                                length=20,
                                                editable=False)
    editor = delegate.createEditor(None, self.option, None)
    self.assertTrue(isinstance(editor, self.editors.TextLineEditor))
    self.grab_delegate(delegate, 'Plain Text', 'disabled')
    
  def testTextEditDelegate(self):
    from PyQt4.QtGui import QTextEdit
    delegate = self.delegates.TextEditDelegate(parent=None, **self.kwargs)
    editor = delegate.createEditor(None, self.option, None)
    self.assertTrue(isinstance(editor, QTextEdit))
    self.grab_delegate(delegate, 'Plain Text')
    delegate = self.delegates.TextEditDelegate(parent=None, editable=False)
    editor = delegate.createEditor(None, self.option, None)
    self.assertTrue(isinstance(editor, QTextEdit))
    self.grab_delegate(delegate, 'Plain Text', 'disabled')

  def testRichTextDelegate(self):
    delegate = self.delegates.RichTextDelegate(parent=None, **self.kwargs)
    editor = delegate.createEditor(None, self.option, None)
    self.assertTrue(isinstance(editor, self.editors.RichTextEditor))
    self.grab_delegate(delegate, '<b>Rich Text</b>')
    delegate = self.delegates.RichTextDelegate(parent=None, editable=False)
    editor = delegate.createEditor(None, self.option, None)
    self.assertTrue(isinstance(editor, self.editors.RichTextEditor))
    self.grab_delegate(delegate, '<b>Rich Text</b>', 'disabled')
    
  def testBoolDelegate(self):
    delegate = self.delegates.BoolDelegate(parent=None, **self.kwargs)
    editor = delegate.createEditor(None, self.option, None)
    self.assertTrue(isinstance(editor, self.editors.BoolEditor))
    self.grab_delegate(delegate, True)
    delegate = self.delegates.BoolDelegate(parent=None, editable=False)
    editor = delegate.createEditor(None, self.option, None)
    self.assertTrue(isinstance(editor, self.editors.BoolEditor))
    self.grab_delegate(delegate, True, 'disabled')
  
  def testDateDelegate(self):
    from datetime import date
    delegate = self.delegates.DateDelegate(parent=None, **self.kwargs)
    editor = delegate.createEditor(None, self.option, None)
    self.assertTrue(isinstance(editor, self.editors.DateEditor))
    date = date.today()
    self.grab_delegate(delegate, date)
    delegate = self.delegates.DateDelegate(parent=None, editable=False)
    editor = delegate.createEditor(None, self.option, None)
    self.assertTrue(isinstance(editor, self.editors.DateEditor))
    date = date.today()
    self.grab_delegate(delegate, date, 'disabled')
    #TODO  !!

  def testDateTimeDelegate(self):
    from datetime import datetime
    delegate = self.delegates.DateTimeDelegate(parent=None, **self.kwargs)
    editor = delegate.createEditor(None, self.option, None)
    self.assertTrue(isinstance(editor, self.editors.DateTimeEditor))
    DateTime = datetime.now()
    self.grab_delegate(delegate, DateTime)
    delegate = self.delegates.DateTimeDelegate(parent=None, editable=False)
    editor = delegate.createEditor(None, self.option, None)
    self.assertTrue(isinstance(editor, self.editors.DateTimeEditor))
    self.grab_delegate(delegate, DateTime, 'disabled')

  def testTimeDelegate(self):
    from datetime import time
    delegate = self.delegates.TimeDelegate(parent=None, editable=True)
    editor = delegate.createEditor(None, self.option, None)
    self.assertTrue(isinstance(editor, self.editors.TimeEditor))
    time = time(10, 30, 15)
    self.grab_delegate(delegate, time)
    delegate = self.delegates.TimeDelegate(parent=None, editable=False)
    editor = delegate.createEditor(None, self.option, None)
    self.assertTrue(isinstance(editor, self.editors.TimeEditor))
    #time = time(10, 30, 15)
    self.grab_delegate(delegate, time, 'disabled')
    
  def testIntegerDelegate(self):
    delegate = self.delegates.IntegerDelegate(parent=None, editable=True)
    editor = delegate.createEditor(None, self.option, None)
    self.assertTrue(isinstance(editor, self.editors.IntegerEditor))
    self.grab_delegate(delegate, 3)
    delegate = self.delegates.IntegerDelegate(parent=None, editable=False)
    editor = delegate.createEditor(None, self.option, None)
    self.assertTrue(isinstance(editor, self.editors.IntegerEditor))
    self.grab_delegate(delegate, 0, 'disabled')

  def testIntervalsDelegate(self):
    from camelot.container import IntervalsContainer, Interval
    intervals = IntervalsContainer(0, 24, [Interval(8, 18, 'work', (255,0,0,255)), Interval(19, 21, 'play', (0,255,0,255))])
    delegate = self.delegates.IntervalsDelegate(parent=None, editable=True)
    self.grab_delegate(delegate, intervals)
    delegate = self.delegates.IntervalsDelegate(parent=None, editable=False)
    self.grab_delegate(delegate, intervals, 'disabled')
    
  def testFloatDelegate(self):
    from camelot.core.constants import camelot_minfloat, camelot_maxfloat
    delegate = self.delegates.FloatDelegate(parent=None, suffix='euro', editable=True)
    editor = delegate.createEditor(None, self.option, None)
    self.assertTrue(isinstance(editor, self.editors.FloatEditor))
    self.assertEqual(editor.spinBox.minimum(), camelot_minfloat)
    self.assertEqual(editor.spinBox.maximum(), camelot_maxfloat)
    self.grab_delegate(delegate, 3.145)
    delegate = self.delegates.FloatDelegate(parent=None, prefix='prefix', editable=False)
    editor = delegate.createEditor(None, self.option, None)
    self.assertTrue(isinstance(editor, self.editors.FloatEditor))
    self.assertEqual(editor.spinBox.minimum(), camelot_minfloat)
    self.assertEqual(editor.spinBox.maximum(), camelot_maxfloat)
    self.grab_delegate(delegate, 0, 'disabled')

  def testColoredFloatDelegate(self):
    delegate = self.delegates.ColoredFloatDelegate(parent=None, precision=3, editable=True)
    editor = delegate.createEditor(None, self.option, None)
    self.assertTrue(isinstance(editor, self.editors.ColoredFloatEditor))
    self.grab_delegate(delegate, 3.14456)
    delegate = self.delegates.ColoredFloatDelegate(parent=None, editable=False)
    editor = delegate.createEditor(None, self.option, None)
    self.assertTrue(isinstance(editor, self.editors.ColoredFloatEditor))
    self.grab_delegate(delegate, 3.1, 'disabled')
  
  def testStarDelegate(self):
    delegate = self.delegates.StarDelegate(parent=None, **self.kwargs)
    editor = delegate.createEditor(None, self.option, None)
    self.assertTrue(delegate.maximum, 5)
    self.assertTrue(isinstance(editor, self.editors.StarEditor))
    self.grab_delegate(delegate, 5)
    delegate = self.delegates.StarDelegate(parent=None, editable=False)
    editor = delegate.createEditor(None, self.option, None)
    self.assertTrue(delegate.maximum, 5)
    self.assertTrue(isinstance(editor, self.editors.StarEditor))
    self.grab_delegate(delegate, 5, 'disabled')
    
  def testSmileyDelegate(self):
    delegate = self.delegates.SmileyDelegate(parent=None, **self.kwargs)
    editor = delegate.createEditor(None, self.option, None)
    self.assertTrue(isinstance(editor, self.editors.SmileyEditor))
    self.grab_delegate(delegate, 'face-glasses')
    delegate = self.delegates.SmileyDelegate(parent=None, editable=False)
    editor = delegate.createEditor(None, self.option, None)
    self.assertTrue(isinstance(editor, self.editors.SmileyEditor))
    self.grab_delegate(delegate, 'face-glasses', 'disabled')

  def testFileDelegate(self):
    delegate = self.delegates.FileDelegate(parent=None, **self.kwargs)
    editor = delegate.createEditor(None, self.option, None)
    self.assertTrue(isinstance(editor, self.editors.FileEditor))

  def testColorDelegate(self):
    delegate = self.delegates.ColorDelegate(parent=None, **self.kwargs)
    editor = delegate.createEditor(None, self.option, None)
    self.assertTrue(isinstance(editor, self.editors.ColorEditor))
    color = [255, 255, 0]
    self.grab_delegate(delegate, color)
    delegate = self.delegates.ColorDelegate(parent=None, editable=False)
    editor = delegate.createEditor(None, self.option, None)
    self.assertTrue(isinstance(editor, self.editors.ColorEditor))
    self.grab_delegate(delegate, color, 'disabled')
  
  def testCodeDelegate(self):
    delegate = self.delegates.CodeDelegate(parent=None, parts=['99','AA'], **self.kwargs)
    editor = delegate.createEditor(None, self.option, None)
    self.assertTrue(isinstance(editor, self.editors.CodeEditor))
    self.grab_delegate(delegate, ['76','AB'])
    delegate = self.delegates.CodeDelegate(parent=None, parts=['99','AA', '99', 'AA'], editable=False)
    editor = delegate.createEditor(None, self.option, None)
    self.assertTrue(isinstance(editor, self.editors.CodeEditor))
    self.grab_delegate(delegate, ['76','AB', '12', '34'], 'disabled')
    
  def testCurrencyDelegate(self):
    delegate = self.delegates.CurrencyDelegate(parent=None, suffix='euro', **self.kwargs)
    editor = delegate.createEditor(None, self.option, None)
    self.assertTrue(isinstance(editor, self.editors.FloatEditor))
    self.grab_delegate(delegate, 1000000.12)
    delegate = self.delegates.CurrencyDelegate(parent=None, prefix='prefix', editable=False)
    self.grab_delegate(delegate, 1000000.12, 'disabled')    
  
  def testComboBoxDelegate(self):
    CHOICES = (('1','A'), ('2','B'), ('3','C'))
    delegate = self.delegates.ComboBoxDelegate(parent=None,
                                               choices=CHOICES,
                                               **self.kwargs)
    editor = delegate.createEditor(None, self.option, None)
    self.assertTrue(isinstance(editor, self.editors.ChoicesEditor))
    self.grab_delegate(delegate, 1)
    delegate = self.delegates.ComboBoxDelegate(parent=None,
                                               choices=CHOICES,
                                               editable=False)
    self.grab_delegate(delegate, 1, 'disabled')

  def testImageDelegate(self):
    delegate = self.delegates.ImageDelegate(parent=None, **self.kwargs)
    editor = delegate.createEditor(None, self.option, None)
    self.assertTrue(isinstance(editor, self.editors.ImageEditor))

  def testVirtualAddressDelegate(self):
    delegate = self.delegates.VirtualAddressDelegate(parent=None,
                                                     **self.kwargs)
    editor = delegate.createEditor(None, self.option, None)
    self.assertTrue(isinstance(editor, self.editors.VirtualAddressEditor))
    self.grab_delegate(delegate, ('email', 'project-camelot@conceptive.be'))
    delegate = self.delegates.VirtualAddressDelegate(parent=None, editable=False)
    self.grab_delegate(delegate, ('email', 'project-camelot@conceptive.be'), 'disabled')

class FilterTest(ModelThreadTestCase):
  """Test the filters in the table view"""
  
  images_path = static_images_path
  
  def test_group_box_filter(self):
    from camelot.view import filters
    filter = filters.GroupBoxFilter('state')
    self.grab_widget(filter.render(None, 'Organization', [('Nokia',None), ('Apple',None)]))

  def test_combo_box_filter(self):
    from camelot.view import filters
    filter = filters.ComboBoxFilter('state')
    self.grab_widget(filter.render(None, 'Organization', [('Nokia',None), ('Apple',None)]))
    
class ControlsTest(ModelThreadTestCase):
    """Test some basic controls"""
    
    images_path = static_images_path
    
    def setUp(self):
        super(ControlsTest, self).setUp()
        from camelot.admin.application_admin import ApplicationAdmin
        self.app_admin = ApplicationAdmin()
          
    def test_table_view(self):
        from camelot.view.controls.tableview import TableView
        from camelot.model.authentication import Person
        widget = TableView(self.app_admin.get_entity_admin(Person))
        self.grab_widget(widget)
    
    def test_navigation_pane(self):
        from camelot.view.controls import navpane
        widget = navpane.NavigationPane(self.app_admin)
        self.grab_widget(widget)
      
    def test_main_window(self):
        from camelot.view.mainwindow import MainWindow
        widget = MainWindow(self.app_admin)
        self.grab_widget(widget)
        
    def test_status_bar(self):
        from camelot.view.controls.statusbar import StatusBar
        status_bar = StatusBar(None)
        status_bar.busy_widget.set_busy(True)
        self.grab_widget(status_bar)
    
class CamelotEntityViewsTest(EntityViewsTest):
  """Test the views of all the Entity subclasses"""
  
  images_path = static_images_path
  
class SnippetsTest(ModelThreadTestCase):
    
    images_path = static_images_path
    
    def test_fields_with_actions(self):
        from snippet.fields_with_actions import Coordinate
        from camelot.view.proxy.collection_proxy import CollectionProxy
        coordinate = Coordinate()
        admin = Coordinate.Admin(None, Coordinate)
        proxy = CollectionProxy(admin, lambda:[coordinate], admin.get_fields )
        form = admin.create_form_view('Coordinate', proxy, 0, None)
        self.grab_widget(form)
      
    def test_fields_with_tooltips(self):
        from snippet.fields_with_tooltips import Coordinate
        from camelot.view.proxy.collection_proxy import CollectionProxy
        coordinate = Coordinate()
        admin = Coordinate.Admin(None, Coordinate)
        proxy = CollectionProxy(admin, lambda:[coordinate], admin.get_fields )
        form = admin.create_form_view('Coordinate', proxy, 0, None)
        self.grab_widget(form)
        
    def test_entity_validator(self):
        from camelot.view.proxy.collection_proxy import CollectionProxy
        from camelot.model.authentication import Person
        from camelot.admin.application_admin import ApplicationAdmin
        from snippet.entity_validator import PersonValidator, Admin
        app_admin = ApplicationAdmin()
        person_admin = Admin(app_admin, Person)
        proxy = CollectionProxy(person_admin, lambda:[Person()], person_admin.get_columns)
        validator = PersonValidator(person_admin, proxy)
        self.mt.post(lambda:validator.isValid(0))
        self.process()
        self.assertEqual(len(validator.validityMessages(0)), 3)
        self.grab_widget(validator.validityDialog(0, parent=None))
        
    def test_background_color(self):
        from camelot.view.proxy.collection_proxy import CollectionProxy
        from camelot.model.authentication import Person
        from camelot.admin.application_admin import ApplicationAdmin
        from snippet.background_color import Admin
        app_admin = ApplicationAdmin()
        person_admin = Admin(app_admin, Person)
        proxy = CollectionProxy(person_admin, lambda:[Person(first_name='John', last_name='Cleese'),
                                                      Person(first_name='eric', last_name='Idle')],
                                                       person_admin.get_columns)
        from camelot.view.controls.editors.one2manyeditor import One2ManyEditor
        editor = One2ManyEditor(admin=person_admin)
        editor.set_value(proxy)
        self.process()
        self.grab_widget(editor)
  
class CamelotSchemaTest(SchemaTest):
  
    images_path = static_images_path
  

if __name__ == '__main__':
    logger.info('running unit tests')
    app = get_application()
    runner=unittest.TextTestRunner(verbosity=2)
    snippets_test =  unittest.makeSuite(SnippetsTest, 'test')
    runner.run(snippets_test)
#  proxy_test =  unittest.makeSuite(ProxyEntityTest, 'test')
#  runner.run(proxy_test)
#  proxy_one_to_many_test =  unittest.makeSuite(ProxyOneToManyTest, 'test')
#  runner.run(proxy_one_to_many_test)
    schema_test =  unittest.makeSuite(CamelotSchemaTest, 'test')
    runner.run(schema_test)
    
    form_action_test =  unittest.makeSuite(FormActionTest, 'test')
    runner.run(form_action_test)
    editors_test =  unittest.makeSuite(EditorsTest, 'test')
    runner.run(editors_test)
    editor_test =  unittest.makeSuite(DelegateTest, 'test')
    runner=unittest.TextTestRunner(verbosity=2)
    runner.run(editor_test)
    controls_test = unittest.makeSuite(ControlsTest, 'test')
    runner.run(controls_test)
    form_test = unittest.makeSuite(FormTest, 'test')
    runner.run(form_test)
    filter_test = unittest.makeSuite(FilterTest, 'test')
    runner.run(filter_test)    
    entity_views_test = unittest.makeSuite(CamelotEntityViewsTest, 'test')
    runner.run(entity_views_test)

