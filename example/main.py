import settings
import logging
import os

logger = logging.getLogger('videostore')

from PyQt4 import QtGui, QtCore
QT_MAJOR_VERSION = float('.'.join(str(QtCore.QT_VERSION_STR).split('.')[0:2]))

from camelot.view.art import TangoIcon, QTangoIcon

def main():
  logger.debug('qt version %s, pyqt version %s' % (QtCore.QT_VERSION_STR, 
                                                   QtCore.PYQT_VERSION_STR))

  logger.debug('qt major version %f' % QT_MAJOR_VERSION)
  import sys
  app = QtGui.QApplication(sys.argv)
  app.setOrganizationName('Conceptive Engineering')
  app.setOrganizationDomain('conceptive.be')
  app.setApplicationName('Videostore')
  app.setWindowIcon(QTangoIcon('system-users', 
                    folder='apps',
                    size='32x32').getQIcon())

  from camelot.view.controls.appscheme import scheme
  style = """
  QMainWindow::separator {
    border-right: 1px solid rgb%(BorderColor)s;
  }
  """ % scheme.styledict
  app.setStyleSheet(style)

  logger.debug('loading splashscreen')
  splash = QtGui.QSplashScreen(QtGui.QPixmap(os.path.join(settings.CAMELOT_MEDIA_ROOT, 'camelot-proposal.png')))
  splash.show()
  app.processEvents()

  #
  # Start the model thread
  #
  from camelot.view.model_thread import get_model_thread, \
                                        construct_model_thread
  from camelot.view.response_handler import ResponseHandler
  from camelot.view.remote_signals import construct_signal_handler

  rh = ResponseHandler()
  construct_model_thread(rh)
  construct_signal_handler()
  get_model_thread().start()
  
  from camelot.view.application_admin import ApplicationAdmin
  
  # icons displayed in the navigation pane with buttons

  icon_movies = TangoIcon('x-office-presentation',
                          folder='mimetypes',
                          size='24x24').fullpath()
  icon_relations = TangoIcon('system-users',
                             folder='apps',
                             size='24x24').fullpath()
  icon_configuration = TangoIcon('preferences-system',
                                 folder='categories',
                                 size='24x24').fullpath()

  admin = ApplicationAdmin([
    ('movies', ('Movies', icon_movies)),
    ('relations', ('Relations', icon_relations)),
    ('configuration', ('Configuration', icon_configuration)),
  ])
  
  from camelot.model.memento import Memento
  from camelot.model.authentication import *
  from example.model import Movie, Cast
  admin.register(Memento, Memento.Admin)
  admin.register(Person, Person.Admin)
  admin.register(Movie, Movie.Admin)
  admin.register(Organization, Organization.Admin)
  admin.register(Party, Party.Admin)
  from camelot.view.mainwindow import MainWindow
  mainwindow = MainWindow(admin)
  mainwindow.show()
  splash.finish(mainwindow)
  sys.exit(app.exec_())

if __name__ == '__main__':
  main()
