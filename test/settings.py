import logging
import os

logging.basicConfig(level=logging.INFO, format='[%(levelname)-7s] [%(name)-35s] - %(message)s')
db_name = 'test_data.db'
#logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)

if os.path.exists(db_name):
  os.remove(db_name)

def setup_model():
  from model import *
  from camelot.model.memento import *
  from camelot.model.synchronization import *
  from camelot.model.authentication import *
  setup_all(create_tables=True)
      
CAMELOT_MAIN_DIRECTORY = os.path.join(os.path.dirname(__file__), '..', 'camelot')
CAMELOT_LIB_DIRECTORY = os.path.join(CAMELOT_MAIN_DIRECTORY, 'librairies')
CAMELOT_ART_DIRECTORY = os.path.join(CAMELOT_MAIN_DIRECTORY, 'art')

CAMELOT_TEMPLATES_DIRECTORY = os.path.join(CAMELOT_MAIN_DIRECTORY,
                                           'view', 'templates')
CAMELOT_ATTACHMENTS = 'G:\Data\Attachments'
CAMELOT_MEDIA_ROOT = 'media'

ENGINE = lambda:'sqlite:///%s'%db_name