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
    
class SearchCase( unittest.TestCase ):
    """Test the creation of search queries"""
    
    def setUp( self ):
        metadata.bind = settings.ENGINE()
        metadata.create_all()
        self.session = Session()
        #
        # insert data in each column of T, that can be searched for
        #
        for (i,name), definition in types_to_test.items():
            if issubclass( definition, sqlalchemy.types.DateTime ):
                value = datetime.datetime( year = 2000, month = 1, day = 1, hour = 1, minute = i )       
            elif issubclass( definition, sqlalchemy.types.Date ):
                value = datetime.datetime( year = 2000, month = 1, day = i%31 )                  
            elif issubclass( definition, sqlalchemy.types.Time ):
                value = datetime.time( hour = 1, minute = i )
            elif issubclass( definition, sqlalchemy.types.String ):
                value = str( i )
            elif issubclass( definition, sqlalchemy.types.Boolean ):
                value = True
            else:
                value = i
            t = T()
            setattr( t, name, value )
        self.session.flush()
        
    def test_search_decorator( self ):
        pass
    