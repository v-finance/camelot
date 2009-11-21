import logging
import os

FORMAT = '[%(levelname)-7s] [%(name)-35s] - %(message)s' 
logging.basicConfig(level=logging.INFO, format=FORMAT)

CAMELOT_MEDIA_ROOT = os.path.join(os.path.dirname(__file__), 'media')
ENGINE = lambda:'sqlite:///videostore.sqlite'

#logging.getLogger('sqlalchemy.engine').setLevel(logging.DEBUG)
#logging.getLogger('camelot.view.proxy.collection_proxy').setLevel(logging.DEBUG)

def setup_model():
    import camelot.model
    import example.model
    from elixir import setup_all
    setup_all(create_tables=True)
    from camelot.model.authentication import updateLastLogin
    updateLastLogin()
