from PyQt4.QtCore import Qt
from PyQt4 import QtCore

from camelot_example.fixtures import load_movie_fixtures
from camelot.model.party import Person
from camelot.view.proxy.collection_proxy import CollectionProxy
from camelot.view.proxy.queryproxy import QueryTableProxy
from camelot.admin.application_admin import ApplicationAdmin
from camelot.core.orm import Session
from camelot.core.utils import variant_to_pyobject
from camelot.test import ModelThreadTestCase

class ProxyCase( ModelThreadTestCase ):

    def setUp( self ):
        super( ProxyCase, self ).setUp()
        load_movie_fixtures()
        self.app_admin = ApplicationAdmin()
        self.person_admin = self.app_admin.get_related_admin( Person )
        
    def _load_data( self, proxy = None ):
        """Trigger the loading of data by the proxy"""
        if proxy == None:
            proxy = self.proxy
        for row in range( proxy.rowCount() ):
            self._data( row, 0, proxy )
        self.process()
        
    def _data( self, row, column, proxy = None ):
        """Get data from the proxy"""
        if proxy == None:
            proxy = self.proxy
        index = proxy.index( row, column )
        return variant_to_pyobject( proxy.data( index ) )
    
    def _set_data( self, row, column, value ):
        """Set data to the proxy"""
        index = self.proxy.index( row, column )
        return self.proxy.setData( index, lambda:value )
    
class CollectionProxyCase( ProxyCase ):

    def setUp( self ):
        super( CollectionProxyCase, self ).setUp()
        session = Session()
        self.collection = list( session.query( Person ).all() )
        self.proxy = CollectionProxy( self.person_admin,
                                      collection_getter=lambda:self.collection,
                                      columns_getter=self.person_admin.get_columns )
        
    def test_modify_list_while_editing( self ):
        person1 = self.collection[0]
        person2 = self.collection[1]
        self._load_data()
        self.assertEqual( person1.first_name, self._data( 0, 0 ) )
        # switch first and second person in collection without informing
        # the proxy
        self.collection[0:2] = [person2, person1]
        self._set_data( 0, 0, 'Foo' )
        self.assertEqual( person1.first_name, 'Foo' )
        
class QueryProxyCase( ProxyCase ):
    """Test the functionality of the QueryProxy to perform CRUD operations on 
    stand alone data"""
  
    def setUp(self):
        super( QueryProxyCase, self ).setUp()
        self.proxy = QueryTableProxy( self.person_admin, 
                                             query_getter = lambda:Person.query, 
                                             columns_getter = self.person_admin.get_columns )

    def test_insert_after_sort( self ):
        from camelot.view.proxy.queryproxy import QueryTableProxy
        from camelot.model.party import Person
        self.proxy.sort( 1, Qt.AscendingOrder )
        # check the query
        self.assertTrue( self.proxy.columnCount() > 0 )
        rowcount = self.proxy.rowCount()
        self.assertTrue( rowcount > 0 )
        # check the sorting
        self._load_data()
        data0 = self._data( 0, 1 )
        data1 = self._data( 1, 1 )
        self.assertTrue( data1 > data0 )
        self.proxy.sort( 1, Qt.DescendingOrder )
        self._load_data()
        data0 = self._data( 0, 1 )
        data1 = self._data( 1, 1 )
        self.assertTrue( data0 > data1 )
        # insert a new object
        person = Person()
        self.proxy.append_object( person )
        new_rowcount = self.proxy.rowCount()
        self.assertTrue( new_rowcount > rowcount )
        new_row = new_rowcount - 1
        self.assertEqual( person, self.proxy._get_object( new_row ) )
        # fill in the required fields
        self.assertFalse( self.person_admin.is_persistent( person ) )
        self._set_data( new_row, 0, 'Foo' )
        self._set_data( new_row, 1, 'Bar' )
        self.assertEqual( person.first_name, 'Foo' )
        self.assertEqual( person.last_name, 'Bar' )
        self._load_data()
        self.assertEqual( self._data( new_row, 0 ), 'Foo' )
        self.assertEqual( self._data( new_row, 1 ), 'Bar' )
        self.assertTrue( self.person_admin.is_persistent( person ) )
        # create a related proxy (eg, to display a form view)
        related_proxy = QueryTableProxy(
            self.person_admin,
            self.proxy.get_query_getter(),
            self.person_admin.get_columns,
            max_number_of_rows = 1,
            cache_collection_proxy = self.proxy
        )
        self.assertEqual( new_rowcount, related_proxy.rowCount() )
        self._load_data( related_proxy )
        self.assertEqual( self._data( new_row, 0, related_proxy ), 'Foo' )
        
    def test_get_object( self ):
        #
        # verify that get_object retruns None when the requested row
        # is out of range
        #
        self.assertFalse( self.proxy._get_object( -1 ) )
        rows = self.proxy.rowCount()
        self.assertTrue( rows > 1 )
        self.assertTrue( self.proxy._get_object( 0 ) )
        self.assertTrue( self.proxy._get_object( rows - 1 ) )        
        self.assertFalse( self.proxy._get_object( rows ) )
        self.assertFalse( self.proxy._get_object( rows + 1 ) )
