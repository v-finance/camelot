import logging

FORMAT = '[%(levelname)-7s] [%(name)-35s] - %(message)s'
logging.basicConfig(level=logging.INFO, format=FORMAT)

logger = logging.getLogger('videostore.main')

try:
    import matplotlib
except:
    logger.error('Charts will not work because of missing matplotlib')

from camelot.core.conf import settings, SimpleSettings

class ExampleSettings( SimpleSettings ):
    """Special settings class for the example application, this is done to
    'survive' various packaging regimes, such as windows, debian, ...
    """
    
    @staticmethod
    def setup_model():
        from sqlalchemy.orm import configure_mappers
        from camelot.core.sql import metadata
        metadata.bind = settings.ENGINE()
        import camelot.model.party
        import camelot.model.authentication
        import camelot.model.i18n
        import camelot.model.fixture
        import camelot.model.memento
        import camelot_example.model
        #
        # setup_all is only needed for those models that rely on elixir
        #
        from elixir import setup_all
        setup_all()
        #
        # create the tables for all models, configure mappers first, to make
        # sure all deferred properties have been handled, as those could
        # create tables or columns
        #
        configure_mappers()
        metadata.create_all()
        from camelot.model.authentication import update_last_login
        update_last_login()
        # 
        # Load sample data with the fixure mechanism
        #
        from camelot_example.fixtures import load_movie_fixtures
        load_movie_fixtures()
        #
        # setup the views
        #
        from camelot_example.view import setup_views
        setup_views()

settings.append( ExampleSettings( 'camelot', 
                                  'videostore',
                                  data = 'videostore_2.sqlite') )

def main():
    from camelot.view.main import main
    from camelot_example.application_admin import MyApplicationAdmin
    main( MyApplicationAdmin() )
    
if __name__ == '__main__':
    main()
