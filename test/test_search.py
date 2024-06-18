import collections
import datetime
import inspect
import itertools

import camelot.types
import sqlalchemy.types
from sqlalchemy import orm, schema, sql

from . import test_orm
from camelot.admin.action.list_filter import SearchFilter
from camelot.admin.application_admin import ApplicationAdmin
from camelot.admin.entity_admin import EntityAdmin
from camelot.test.action import MockModelContext
#
# build a list of the various column types for which the search functions
# should be tested
#
possible_types = itertools.chain(sqlalchemy.types.__dict__.items(),
                                 camelot.types.__dict__.items() )
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
                                         sqlalchemy.types.ARRAY,
                                         sqlalchemy.types.JSON,
                                         sqlalchemy.types.PickleType,
                                         camelot.types.File,
                                         camelot.types.Enumeration) ):
            types_to_test[(i, '%s_%i'%(name, i))] = definition

class SearchCase( test_orm.TestMetaData ):
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
        elif issubclass( definition, camelot.types.VirtualAddress ):
            value =('email', str(i))
        elif issubclass( definition, camelot.types.Color ):
            value = "#{:06d}".format(i)
        return value

    def setUp(self):
        super(SearchCase, self).setUp()
        self.app_admin = ApplicationAdmin()

        class T( self.Entity ):
            """An entity with for each column type a column"""
            pass
        
        for (i,name), definition in types_to_test.items():
            setattr(T, name, schema.Column(definition))

        class TAdmin(EntityAdmin):
            search_all_fields = True
            list_search = []
            entity = T
        
        self.create_all()
        self.T = T
        self.TAdmin = TAdmin

    def test_get_search_fields(self):
        #
        # check if all columns are searched for
        #
        admin = self.TAdmin(self.app_admin, self.T)
        search_fields = admin._get_search_fields(u'foo')
        for (_i,name) in types_to_test.keys():
            search_strategy = admin.get_field_attributes(name).get('search_strategy')
            self.assertTrue(search_strategy in search_fields)
        #
        # test if selects are skipped
        #
        self.T.id_max = orm.column_property(sql.select([sql.func.max(self.T.id)]))
        admin = self.TAdmin(self.app_admin, self.T)
        search_fields = admin._get_search_fields(u'foo')
        self.assertTrue('id_max' not in search_fields)

    def test_search_filter( self ):
        """Verify it search works for most common types"""
        admin = self.TAdmin(self.app_admin, self.T)
        search_filter = SearchFilter()
        model_context = MockModelContext()
        model_context.admin = admin
        model_context.proxy = admin.get_proxy(admin.get_query())
        list(search_filter.model_run(model_context, None))
        #
        # insert the value of i in each column of T, that can be searched for
        #
        insert = self.T.__table__.insert()
        for (i,name), definition in types_to_test.items():
            self.session.execute(insert,
                                 {name:self.value_for_type( definition, i )})

        initial_count = model_context.proxy.get_query().count()
        for (i,name), definition in types_to_test.items():
            value = self.value_for_type( definition, i )
            #
            # @todo : search for types that need special conversion to string
            #         is skipped for now because the test would become too
            #         convoluted, this should work through a to_string field
            #         attribute.
            #
            if isinstance( value, ( datetime.date, datetime.time, bool, tuple) ) or definition == camelot.types.Color:
                continue
            string_value = str( i )

            list(search_filter.model_run(model_context, string_value))
            query = model_context.proxy.get_query()
            self.assertTrue(initial_count > query.count() > 0, 'Count return 0 for {} {}'.format(
                name, definition
            ))

