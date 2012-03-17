from PyQt4.QtCore import Qt
from PyQt4 import QtCore

from camelot.core.utils import variant_to_pyobject
from camelot.test import ModelThreadTestCase

class QueryProxyCase( ModelThreadTestCase ):
    """Test the functionality of the QueryProxy to perform CRUD operations on 
    stand alone data"""
  
    def setUp(self):
        super( QueryProxyCase, self ).setUp()
        from camelot_example.fixtures import load_movie_fixtures
        from camelot.model.party import Person
        from camelot.view.proxy.queryproxy import QueryTableProxy
        from camelot.admin.application_admin import ApplicationAdmin
        load_movie_fixtures()
        self.app_admin = ApplicationAdmin()
        self.person_admin = self.app_admin.get_related_admin( Person )
        Person.query.count
        self.person_proxy = QueryTableProxy( self.person_admin, 
                                             query_getter = lambda:Person.query, 
                                             columns_getter = self.person_admin.get_columns )
  
    def _load_data( self, proxy = None ):
        """Trigger the loading of data by the proxy"""
        if proxy == None:
            proxy = self.person_proxy
        for row in range( proxy.rowCount() ):
            self._data( row, 0, proxy )
        self.process()
        
    def _data( self, row, column, proxy = None ):
        """Get data from the proxy"""
        if proxy == None:
            proxy = self.person_proxy
        index = proxy.index( row, column )
        return variant_to_pyobject( proxy.data( index ) )
    
    def _set_data( self, row, column, value ):
        """Set data to the proxy"""
        index = self.person_proxy.index( row, column )
        return self.person_proxy.setData( index, lambda:value )
      
    def test_insert_after_sort( self ):
        from camelot.view.proxy.queryproxy import QueryTableProxy
        from camelot.model.party import Person
        self.person_proxy.sort( 1, Qt.AscendingOrder )
        # check the query
        self.assertTrue( self.person_proxy.columnCount() > 0 )
        rowcount = self.person_proxy.rowCount()
        self.assertTrue( rowcount > 0 )
        # check the sorting
        self._load_data()
        data0 = self._data( 0, 1 )
        data1 = self._data( 1, 1 )
        self.assertTrue( data1 > data0 )
        self.person_proxy.sort( 1, Qt.DescendingOrder )
        self._load_data()
        data0 = self._data( 0, 1 )
        data1 = self._data( 1, 1 )
        self.assertTrue( data0 > data1 )
        # insert a new object
        person = Person()
        self.person_proxy.append_object( person )
        new_rowcount = self.person_proxy.rowCount()
        self.assertTrue( new_rowcount > rowcount )
        new_row = new_rowcount - 1
        self.assertEqual( person, self.person_proxy._get_object( new_row ) )
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
            self.person_proxy.get_query_getter(),
            self.person_admin.get_columns,
            max_number_of_rows = 1,
            cache_collection_proxy = self.person_proxy
        )
        self.assertEqual( new_rowcount, related_proxy.rowCount() )
        self._load_data( related_proxy )
        self.assertEqual( self._data( new_row, 0, related_proxy ), 'Foo' )
