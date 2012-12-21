import logging

from camelot.core.conf import settings

logging.basicConfig(level=logging.INFO, format='[%(levelname)-7s] [%(name)-35s] - %(message)s')
#logging.getLogger('sqlalchemy.engine').setLevel(logging.DEBUG)

class TestSettings( object ):
    
    def setup_model( self ):
        from camelot.core.sql import metadata
        from elixir import setup_all
        metadata.bind = self.ENGINE()
        from camelot.model import authentication
        from camelot.model import party
        from camelot.model import i18n
        from camelot.model import memento
        from camelot.model import fixture
        from camelot.model import batch_job
        import camelot_example.model

        setup_all(create_tables=True)
        from camelot_example.view import setup_views
        from camelot_example.fixtures import load_movie_fixtures
        from camelot.model.authentication import update_last_login
        from camelot.core.orm import setup_all
        setup_all()
        print 'setting up metadata'
        print metadata.tables['batch_job_type'].c
        print metadata
        
        metadata.create_all()
        setup_views()
        load_movie_fixtures()
        update_last_login()
    
    CAMELOT_MEDIA_ROOT = 'media'
    
    def ENGINE( self ):
       from sqlalchemy import create_engine
       return create_engine( 'sqlite:///' )
   
settings.append( TestSettings() )