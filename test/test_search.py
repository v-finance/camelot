import collections
import datetime
import inspect
import itertools
import types
import unittest

import sqlalchemy.types

from . import test_orm

from camelot.admin.entity_admin import EntityAdmin
from camelot.core.conf import settings
from camelot.core.orm import has_field
import camelot.types

#
# build a list of the various column types for which the search functions
# should be tested
#
possible_types = itertools.chain( sqlalchemy.types.__dict__.iteritems(),
                                  camelot.types.__dict__.iteritems() )
types_to_test = collections.OrderedDict()
for i, (name, definition) in enumerate(possible_types):
    if not inspect.isclass( definition ):
        continue
    if definition in (sqlalchemy.types.TypeEngine,
                      sqlalchemy.types.TypeDecorator,
                      sqlalchemy.types.Variant):
        continue
    if issubclass( definition, (sqlalchemy.types.TypeEngine,
                                sqlalchemy.types.TypeDecorator) ):
        if not issubclass( definition, ( sqlalchemy.types.UserDefinedType,
                                         sqlalchemy.types.NullType,
                                         sqlalchemy.types._Binary,
                                         sqlalchemy.types.Enum,
                                         sqlalchemy.types.PickleType,
                                         camelot.types.File,
                                         camelot.types.Enumeration) ):
            types_to_test[(i, '%s_%i'%(name, i))] = definition

class SearchCase( test_orm.TestMetaData ):
    pass

    """Test the creation of search queries"""
     
    def value_for_type( self, definition, i ):
        value = i        
        if issubclass( definition, sqlalchemy.types.DateTime ):
            value = datetime.datetime( year = 2000, month = 1, day = 1, hour = 1, minute = 1+i%59 )       
        elif issubclass( definition, sqlalchemy.types.Date ):
            value = datetime.date( year = 2000, month = 1, day = 1 + i%30 )                  
        elif issubclass( definition, sqlalchemy.types.Time ):
            value = datetime.time( hour = 1, minute = 1+i%59 )
        elif issubclass( definition, sqlalchemy.types.String ):
            value = str( i )
        elif issubclass( definition, sqlalchemy.types.Boolean ):
            value = True
        elif issubclass( definition, sqlalchemy.types.Interval ):
            value = datetime.timedelta(days=i)
        elif issubclass( definition, camelot.types.Code ):
            value =(str(i),)
        elif issubclass( definition, camelot.types.VirtualAddress ):
            value =('email', str(i))
        elif issubclass( definition, camelot.types.Color ):
            value =(i, i, i, i)            
        return value
            
    def test_search_decorator( self ):
        """Verify it search works for most common types"""
        from camelot.view.search import create_entity_search_query_decorator
        
        class T( self.Entity ):
            """An entity with for each column type a column"""
            for (i,name), definition in types_to_test.items():
                has_field( name, definition )
                
        class TAdmin( object ):
            search_all_fields = True
            list_search = []
            entity = T

        self.create_all()
        #
        # insert the value of i in each column of T, that can be searched for
        #
        insert = T.__table__.insert()
        for (i,name), definition in types_to_test.items():
            self.session.execute(insert,
                                 {name:self.value_for_type( definition, i )})
        admin = TAdmin()
        
        for (i,name), definition in types_to_test.items():
            value = self.value_for_type( definition, i )
            #
            # @todo : search for types that need special conversion to string
            #         is skipped for now because the test would become too
            #         convoluted, this should work through a to_string field
            #         attribute.
            #
            if isinstance( value, ( datetime.date, datetime.time, bool, tuple) ):
                continue
            string_value = str( i )
            
            search_decorator = create_entity_search_query_decorator( admin,
                                                                     string_value )
            query = self.session.query( T )
            query = search_decorator( query )
            
            self.assertTrue( query.count() > 0 )
            
    