import logging
import inspect
import camelot
import os

logging.basicConfig(level=logging.ERROR)

CAMELOT_ATTACHMENTS = ''
# media root needs to be an absolute path for the file open functions
# to function correctly
CAMELOT_MEDIA_ROOT = os.path.join(os.path.dirname(__file__), 'media')

REPOSITORY = 'repository'
ENGINE = lambda:'sqlite:///model-data.sqlite'

def setup_model():
    from model import *
    from camelot.model.memento import *
    from camelot.model.synchronization import *
    from camelot.model.authentication import *
    from camelot.model.i18n import *
    setup_all(create_tables=True)
    updateLastLogin()
