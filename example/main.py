import logging
FORMAT = '[%(levelname)-7s] [%(name)-35s] - %(message)s' 
logging.basicConfig(level=logging.DEBUG, format=FORMAT)
logger = logging.getLogger('videostore')

from PyQt4 import QtCore
from PyQt4 import QtGui
QT_MAJOR_VERSION = float('.'.join(str(QtCore.QT_VERSION_STR).split('.')[0:2]))

from camelot.view import art

def main():
  
  logger.debug('qt version %s, pyqt version %s' % (QtCore.QT_VERSION_STR, 
                                                   QtCore.PYQT_VERSION_STR))

  logger.debug('qt major version %f' % QT_MAJOR_VERSION)
  import sys
  app = QtGui.QApplication(sys.argv)
  app.setOrganizationName('Conceptive Engineering')
  app.setOrganizationDomain('conceptive.be')
  app.setApplicationName('Videostore')
  app.setWindowIcon(QtGui.QIcon(art.icon32('apps/system-users')))

  from camelot.view.controls.schemer import schemer
  style = """
  QMainWindow::separator {
    border-right: 1px solid rgb%(BorderColor)s;
  }
  """ % schemer.styledict
  app.setStyleSheet(style)

  logger.debug('loading splashscreen')
  splash = QtGui.QSplashScreen(QtGui.QPixmap(('camelot.png')))
  splash.show()
  app.processEvents()
  
  #
  # Start the model thread
  #
  from camelot.view.model_thread import get_model_thread, construct_model_thread
  from camelot.view.response_handler import ResponseHandler
  from camelot.view.remote_signals import construct_signal_handler
  rh = ResponseHandler()
  
  construct_model_thread(rh)
  construct_signal_handler()
  get_model_thread().start()
  
  from camelot.view.application_admin import ApplicationAdmin

  admin = ApplicationAdmin([('movies',('Movies', art.icon24('mimetypes/x-office-presentation'))),
                            ('configuration',('Configuration', art.icon24('categories/preferences-system'))),]
                           )
  from camelot.model.memento import Memento
  from camelot.model.authentication import Person
  from model import Director, Movie, Actor
  admin.register(Memento, Memento.Admin)
  admin.register(Person, Person.Admin)
  admin.register(Director, Director.Admin)
  admin.register(Movie, Movie.Admin)
  admin.register(Actor, Actor.Admin)
  from camelot.view.mainwindow import MainWindow
  mainwindow = MainWindow(admin)
#  mainwindow.connect(rh, rh.start_signal, mainwindow.throbber.process_working)
#  mainwindow.connect(rh, rh.stop_signal, mainwindow.throbber.process_idle)
  mainwindow.show()
  splash.finish(mainwindow)
  sys.exit(app.exec_())

if __name__ == '__main__':
  main()