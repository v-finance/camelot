import logging
import inspect
import camelot
import os

logging.basicConfig(level=logging.ERROR)

def setup_model():
  from model import *
  from camelot.model.memento import *
  from camelot.model.synchronization import *
  from camelot.model.authentication import *
  from camelot.model.i18n import *
  setup_all(create_tables=True)
  updateLastLogin()
      
CAMELOT_MAIN_DIRECTORY = os.path.dirname(inspect.getabsfile(camelot))
CAMELOT_ART_DIRECTORY = os.path.join(CAMELOT_MAIN_DIRECTORY, 'art')
PARTNERPLAN_MAIN_DIRECTORY = os.path.join(CAMELOT_MAIN_DIRECTORY, '..', 'partnerplan')
PARTNERPLAN_ART_DIRECTORY = os.path.join(PARTNERPLAN_MAIN_DIRECTORY, 'art')
CAMELOT_TEMPLATES_DIRECTORY = os.path.join(CAMELOT_MAIN_DIRECTORY,
                                           'view', 'templates')
CAMELOT_ATTACHMENTS = ''
CAMELOT_MEDIA_ROOT = ''

ENGINE = lambda:'sqlite:///model-data.sqlite'
