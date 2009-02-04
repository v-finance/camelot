import logging
import settings

logger = logging.getLogger('camelot.main')
from PyQt4 import QtGui, QtCore
QT_MAJOR_VERSION = float('.'.join(str(QtCore.QT_VERSION_STR).split('.')[0:2]))

from camelot.view import art
from camelot.view.art import Icon

def main():
  logger.debug('qt version %s, pyqt version %s' % (QtCore.QT_VERSION_STR, 
                                                   QtCore.PYQT_VERSION_STR))

  logger.debug('qt major version %f' % QT_MAJOR_VERSION)
  import sys
  app = QtGui.QApplication(sys.argv)
  app.setOrganizationName('My organization')
  app.setOrganizationDomain('example.com')
  app.setApplicationName('Camelot')
  app.setWindowIcon(Icon('tango/32x32/apps/system-users.png').getQIcon())

  from camelot.view.controls.appscheme import scheme
  style = """
  QMainWindow::separator {
    border-right: 1px solid rgb%(BorderColor)s;
  }
  """ % scheme.styledict
  app.setStyleSheet(style)

  logger.debug('loading splashscreen')
  pixmap = QtGui.QPixmap(art.file_('camelot-proposal.png'))
  splash = QtGui.QSplashScreen(pixmap)
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
  
  from application_admin import MyApplicationAdmin
  from camelot.view.mainwindow import MainWindow
  admin = MyApplicationAdmin()
  mainwindow = MainWindow(admin)
  mainwindow.show()
  splash.finish(mainwindow)
  sys.exit(app.exec_())

if __name__ == '__main__':
  main()
