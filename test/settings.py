import logging

logging.basicConfig(level=logging.INFO, format='[%(levelname)-7s] [%(name)-35s] - %(message)s')
#logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)

def setup_model():
    import camelot.model
    import example.model
    from example.view import setup_views
    from example.fixtures import load_movie_fixtures
    from elixir import setup_all
    from camelot.model.authentication import updateLastLogin
    setup_all(create_tables=True)
    setup_views()
    load_movie_fixtures()
    updateLastLogin()

CAMELOT_MEDIA_ROOT = 'media'

ENGINE = lambda:'sqlite:///'
