import datetime
import inspect
import types
import unittest

import sqlalchemy.types

from camelot.core.conf import settings
from camelot.core.orm import Entity, Session, has_field
from camelot.core.sql import metadata

#
# build a list of the various column types for which the search functions
# should be tested
#
types_to_test = dict()
for i, (name, definition) in enumerate( sqlalchemy.types.__dict__.items() ):
    if not inspect.isclass( definition ):
        continue
    if definition == sqlalchemy.types.TypeEngine:
        continue
    if issubclass( definition, sqlalchemy.types.TypeEngine ):
        if not issubclass( definition, ( sqlalchemy.types.TypeDecorator,
                                         sqlalchemy.types.UserDefinedType,
                                         sqlalchemy.types.NullType,
                                         sqlalchemy.types._Binary,
                                         sqlalchemy.types.Enum ) ):
            types_to_test[(i, '%s_%i'%(name, i))] = definition

class T( Entity ):
    """An entity with for each column type a column"""
    for (i,name), definition in types_to_test.items():
        has_field( name, definition )
        
class TAdmin( object ):
    search_all_fields = True
    list_search = []
    entity = T
    
class SearchCase( unittest.TestCase ):
    """Test the creation of search queries"""
    
    def setUp( self ):
        metadata.bind = settings.ENGINE()
        metadata.create_all()
        self.session = Session()
        #
        # insert the value of i in each column of T, that can be searched for
        #
        for (i,name), definition in types_to_test.items():
            value = self.value_for_type( definition, i )
            t = T()
            setattr( t, name, value )
        self.session.flush()
        self.admin = TAdmin()
        
    def value_for_type( self, definition, i ):
        value = i        
        if issubclass( definition, sqlalchemy.types.DateTime ):
            value = datetime.datetime( year = 2000, month = 1, day = 1, hour = 1, minute = i )       
        elif issubclass( definition, sqlalchemy.types.Date ):
            value = datetime.date( year = 2000, month = 1, day = i%31 )                  
        elif issubclass( definition, sqlalchemy.types.Time ):
            value = datetime.time( hour = 1, minute = i )
        elif issubclass( definition, sqlalchemy.types.String ):
            value = str( i )
        elif issubclass( definition, sqlalchemy.types.Boolean ):
            value = True
        return value
            
    def test_search_decorator( self ):
        """Verify it search works for most common types"""
        from camelot.view.search import create_entity_search_query_decorator
        for (i,name), definition in types_to_test.items():
            value = self.value_for_type( definition, i )
            #
            # @todo : search for types that need special conversion to string
            #         is skipped for now because the test would become too
            #         convoluted, this should work through a to_string field
            #         attribute.
            #
            if isinstance( value, ( datetime.date, datetime.time, bool) ):
                continue
            string_value = str( value )
            
            search_decorator = create_entity_search_query_decorator( self.admin,
                                                                     string_value )
            query = self.session.query( T )
            query = search_decorator( query )
            
            #print query
            
            self.assertTrue( query.count() > 0 )
            
    