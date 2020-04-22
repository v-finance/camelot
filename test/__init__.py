import logging
import faulthandler
import sys

#warnings.filterwarnings( 'error' )

from camelot.core.conf import settings

logging.basicConfig(level=logging.INFO, format='[%(levelname)-7s] [%(name)-35s] - %(message)s')
#logging.getLogger('sqlalchemy.engine').setLevel(logging.DEBUG)

faulthandler.enable()
# import here because mac osx causes crashes with imports later on
from camelot.core.qt import QtCore
from camelot.core.qt import QtGui
from camelot.core.qt import QtWidgets
from camelot.core.qt import QtNetwork

# a QApplication is needed to be able to construct other
# objects.
_application_ = []
if QtWidgets.QApplication.instance() is None:
    # set up a test application
    _application_.append(QtWidgets.QApplication([a for a in sys.argv if a]))
    # set up a specific locale to test import of files
    QtCore.QLocale.setDefault(QtCore.QLocale('nl_BE'))
    # to generate consistent screenshots
    _application_[0].setStyle('fusion')

getattr(QtCore, 'QObject')
getattr(QtGui, 'QColor')
getattr(QtWidgets, 'QWidget')
getattr(QtNetwork, 'QNetworkAccessManager')

from camelot.admin.application_admin import ApplicationAdmin

app_admin = ApplicationAdmin()

class TestSettings( object ):

    CAMELOT_MEDIA_ROOT = 'media'

    def __init__( self ): 
        from sqlalchemy.pool import StaticPool
        from sqlalchemy import create_engine
        # static pool to preserve tables and data accross threads
        self.engine = create_engine('sqlite:///', poolclass = StaticPool)

    def setup_model(self):
        pass

    def ENGINE( self ):
        return self.engine
   
settings.append( TestSettings() )
