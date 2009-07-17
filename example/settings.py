import logging
import inspect
import camelot
import os

FORMAT = '[%(levelname)-7s] [%(name)-35s] - %(message)s' 
logging.basicConfig(level=logging.INFO, format=FORMAT)

CAMELOT_MEDIA_ROOT = os.path.join(os.path.dirname(__file__), 'media')
ENGINE = lambda:'sqlite:///videostore.sqlite'

#logging.getLogger('sqlalchemy.engine').setLevel(logging.DEBUG)
#logging.getLogger('camelot.view.proxy.collection_proxy').setLevel(logging.DEBUG)

def setup_model():
  from example.model import Movie, Cast
  from camelot.model.memento import *
  from camelot.model.synchronization import *
  from camelot.model.authentication import *
  from camelot.model.i18n import *
  setup_all(create_tables=True)
  updateLastLogin()
