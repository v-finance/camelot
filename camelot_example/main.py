import logging

FORMAT = '[%(levelname)-7s] [%(name)-35s] - %(message)s'
logging.basicConfig(level=logging.INFO, format=FORMAT)

logger = logging.getLogger('videostore.main')
logging.getLogger('sqlalchemy.engine').setLevel(logging.DEBUG)
try:
    import matplotlib
    logger.info('matplotlib %s is used'%(matplotlib.__version__))
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
        #
        # import all the needed model files to make sure the mappers and tables
        # are defined before creating them in the database
        #
        from camelot.model import (party, authentication, i18n, fixture,
                                   memento, batch_job)
        from . import model
        logger.debug('loaded datamodel for %s'%party.__name__)
        logger.debug('loaded datamodel for %s'%authentication.__name__)
        logger.debug('loaded datamodel for %s'%i18n.__name__)
        logger.debug('loaded datamodel for %s'%fixture.__name__)
        logger.debug('loaded datamodel for %s'%memento.__name__)
        logger.debug('loaded datamodel for %s'%batch_job.__name__)
        logger.debug('loaded datamodel for %s'%model.__name__)
        #
        # create the tables for all models, configure mappers first, to make
        # sure all deferred properties have been handled, as those could
        # create tables or columns
        #
        configure_mappers()
        metadata.create_all()
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

example_settings = ExampleSettings('camelot', 
                                   'videostore',
                                   data = 'videostore_3.sqlite')

def main():
    from camelot.admin.action.application import Application
    from camelot.view.main import main_action
    from camelot_example.application_admin import MyApplicationAdmin
    settings.append(example_settings)
    videostore = Application(MyApplicationAdmin())
    main_action(videostore)

if __name__ == '__main__':
    main()
