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
        import camelot.model
        import camelot_example.model
        from elixir import setup_all
        setup_all(create_tables=True)
        from camelot.model.authentication import updateLastLogin
        updateLastLogin()
        # 
        # Load sample data with the fixure mechanism
        #
        from camelot_example.fixtures import load_movie_fixtures
        load_movie_fixtures()
        from camelot.core.sql import update_database_from_model
        #update_database_from_model()
        #
        # setup the views
        #
        from camelot_example.view import setup_views
        setup_views()

settings.append( ExampleSettings('camelot', 'videostore') )

def main():
    from camelot.view.main import main
    from camelot_example.application_admin import MyApplicationAdmin
    main(MyApplicationAdmin())
    
if __name__ == '__main__':
    main()
