"""Main function, to be called to start the GUI interface"""
import logging
logger = logging.getLogger('camelot.view.main')
import settings

from PyQt4 import QtCore
from PyQt4 import QtGui
QT_MAJOR_VERSION = float('.'.join(str(QtCore.QT_VERSION_STR).split('.')[0:2]))
from camelot.view.art import Icon

import sys
import os

def main(application_admin):
  """Main function, call this function to start the GUI interface
  @param application_admin: object of type ApplicationAdmin (as defined in application_admin.py)
  that specifies the look of the GUI interface 
  """
  
  logger.debug('qt version %s, pyqt version %s' % 
               (QtCore.QT_VERSION_STR, QtCore.PYQT_VERSION_STR))
  logger.debug('qt major version %f' % QT_MAJOR_VERSION)

  app = QtGui.QApplication(sys.argv)
  app.setOrganizationName(application_admin.getOrganizationName())
  app.setOrganizationDomain(application_admin.getOrganizationDomain())
  app.setApplicationName(application_admin.getName())
  app.setWindowIcon(application_admin.getIcon())

  logger.debug('loading splashscreen')
  splash = QtGui.QSplashScreen(application_admin.getSplashscreen())
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

  from camelot.view.mainwindow import MainWindow
  mainwindow = MainWindow(application_admin)
  mainwindow.show()
  splash.finish(mainwindow)
  sys.exit(app.exec_())