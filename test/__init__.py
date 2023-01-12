import faulthandler
import logging
import sys
import traceback

from camelot.core.conf import settings

logging.basicConfig(level=logging.INFO, format='[%(levelname)-7s] [%(name)-35s] - %(message)s')
#logging.getLogger('sqlalchemy.engine').setLevel(logging.DEBUG)

faulthandler.enable()
from camelot.core.naming import initial_naming_context
from camelot.core.qt import QtCore
from camelot.core.qt import QtGui
from camelot.core.qt import QtWidgets
from camelot.core.qt import QtNetwork
from camelot.admin.application_admin import ApplicationAdmin

from sqlalchemy.pool import StaticPool
from sqlalchemy import create_engine

# set up a specific locale to test import of files
QtCore.QLocale.setDefault(QtCore.QLocale('nl_BE'))

getattr(QtCore, 'QObject')
getattr(QtGui, 'QColor')
getattr(QtWidgets, 'QWidget')
getattr(QtNetwork, 'QNetworkAccessManager')

app_admin = ApplicationAdmin()

unit_test_context = initial_naming_context.bind_new_context(
    'unit_test', immutable=True
)

class TestSettings( object ):

    CAMELOT_MEDIA_ROOT = 'media'

    def __init__( self ):
        # static pool to preserve tables and data accross threads
        self.engine = create_engine('sqlite:///', poolclass = StaticPool)

    def setup_model(self):
        pass

    def ENGINE( self ):
        return self.engine
   
settings.append( TestSettings() )

def excepthook(type, value, tb):
    print('Camelot Unit Test Excepthook')
    for line in traceback.format_exception(type, value, tb):
        print(line)

sys.excepthook = excepthook