from sqlalchemy.engine import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.schema import Table

from camelot.admin.application_admin import ApplicationAdmin
from camelot.admin.entity_admin import EntityAdmin
from camelot.core.conf import settings
from camelot.core.sql import metadata

engine = create_engine( 'sqlite:///test.sqlite' )
#
# Create a table in the database using plain old sql
#
connection = engine.connect()
try:
    connection.execute("""drop table person""")
except:
    pass
connection.execute( """create table person ( pk INTEGER PRIMARY KEY,
                                             first_name TEXT NOT NULL,
                                             last_name TEXT NOT NULL )""" )
connection.execute( """insert into person (first_name, last_name)
                       values ("Peter", "Principle")""" )        

#
# Use declarative to reflect the table and create classes
#

Base = declarative_base( metadata = metadata )

class Person( Base ):
    __table__ = Table( 'person', Base.metadata,  
                       autoload=True, autoload_with=engine )
    
    class Admin( EntityAdmin ):
        list_display = ['first_name', 'last_name']
        
#
# Setup a camelot application
#

class AppAdmin( ApplicationAdmin ):
    pass

class Settings(object):
    
    def ENGINE( self ):
        return engine
    
    def setup_model( self ):
        metadata.bind = engine
    
settings.append( Settings() )
app_admin = AppAdmin()
all_tables = app_admin.add_navigation_menu('All tables')
app_admin.add_navigation_entity_table(Person, all_tables)

#
# Start the application 
#
if __name__ == '__main__':
    from camelot.view.main import main
    main( app_admin )
        
