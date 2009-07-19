import logging
import os

logging.basicConfig(level=logging.INFO, format='[%(levelname)-7s] [%(name)-35s] - %(message)s')
db_name = 'test_data.db'
db_name = ''
#logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)

if os.path.exists(db_name):
  os.remove(db_name)

def setup_model():
  from camelot.model import *
  from camelot.model.memento import *
  from camelot.model.synchronization import *
  from camelot.model.authentication import *
  from camelot.model.i18n import *
  setup_all(create_tables=True)
  updateLastLogin()

CAMELOT_MEDIA_ROOT = 'media'

ENGINE = lambda:'sqlite:///%s'%db_name