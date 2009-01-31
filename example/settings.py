import logging
import inspect
import camelot
import os

FORMAT = '[%(levelname)-7s] [%(name)-35s] - %(message)s' 
logging.basicConfig(level=logging.INFO, format=FORMAT)

CAMELOT_MAIN_DIRECTORY = os.path.dirname(inspect.getabsfile(camelot))
CAMELOT_LIB_DIRECTORY = os.path.join(CAMELOT_MAIN_DIRECTORY, 'librairies')
CAMELOT_ART_DIRECTORY = os.path.join(CAMELOT_MAIN_DIRECTORY, 'art')

CAMELOT_TEMPLATES_DIRECTORY = os.path.join(CAMELOT_MAIN_DIRECTORY,
                                           'view', 'templates')
CAMELOT_ATTACHMENTS = 'G:\Data\Attachments'
CAMELOT_MEDIA_ROOT = 'media'

ENGINE = lambda:'sqlite:///videostore.sqlite'

def setup_model():
  from example.model import Movie, Cast
  from camelot.model.memento import *
  from camelot.model.synchronization import *
  from camelot.model.authentication import *
  from camelot.model.i18n import *
  setup_all(create_tables=True)
  updateLastLogin()
      

