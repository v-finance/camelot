import logging
import inspect
import camelot
import os

logging.basicConfig(level=logging.ERROR)

CAMELOT_MAIN_DIRECTORY = os.path.dirname(inspect.getabsfile(camelot))
CAMELOT_ART_DIRECTORY = os.path.join(CAMELOT_MAIN_DIRECTORY, 'art')
CAMELOT_TEMPLATES_DIRECTORY = os.path.join(CAMELOT_MAIN_DIRECTORY,
                                           'view', 'templates')
CAMELOT_ATTACHMENTS = ''
CAMELOT_MEDIA_ROOT = ''

V_INSURANCE_MAIN_DIRECTORY = os.path.dirname(__file__) 

REPOSITORY = 'repository'
ENGINE = lambda:'sqlite:///model-data.sqlite'

def setup_model():
    
  from migrate.versioning.schema import ControlledSchema
  from migrate.versioning.exceptions import DatabaseAlreadyControlledError
  try:
    schema = ControlledSchema.create(ENGINE(), REPOSITORY, 0)
  except DatabaseAlreadyControlledError, e:
    schema = ControlledSchema(ENGINE(), REPOSITORY)
    logger.info('current database version : %s'%schema.version)
  from migrate.versioning.repository import Repository
  repository = Repository(os.path.join(V_INSURANCE_MAIN_DIRECTORY, REPOSITORY))
  logger.info('latest available version : %s'%str(repository.latest))
  schema.upgrade(repository.latest)
    
  from model import *
  from camelot.model.memento import *
  from camelot.model.synchronization import *
  from camelot.model.authentication import *
  from camelot.model.i18n import *
  setup_all(create_tables=True)
  updateLastLogin()
      