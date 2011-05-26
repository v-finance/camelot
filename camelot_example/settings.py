import logging
import os

FORMAT = '[%(levelname)-7s] [%(name)-35s] - %(message)s'
logging.basicConfig(level=logging.INFO, format=FORMAT)

CAMELOT_MEDIA_ROOT = os.path.join(os.path.dirname(__file__), 'media')

def ENGINE():
    from sqlalchemy import create_engine
    return create_engine('sqlite:///videostore.sqlite')

#logging.getLogger('sqlalchemy.engine').setLevel(logging.DEBUG)
#logging.getLogger('camelot.view.proxy.collection_proxy').setLevel(logging.DEBUG)

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
    #
    # setup the views
    #
    from camelot_example.view import setup_views
    setup_views()
