"""Main function, to be called to start the GUI interface"""

def main(application_admin, 
         initialization=lambda:None,
         pre_initialization=lambda:None):
  """Main function, call this function to start the GUI interface

  @param application_admin: object of type ApplicationAdmin (as defined in application_admin.py)
  that specifies the look of the GUI interface
  @param initialization: function that will be called during the appearance of the splash
  screen, put all time consuming initialization here.  this function will be called after the
  model thread has been started.
  @param pre-initialization: function that will be called before the model thread has been started,
  but after the QApplication has been created.  This function can be used to run a configuration
  wizard before a connection to the database was mode or any gui element has been constructed.
  """
  #
  # before anything else happens or is imported, the splash screen should be there
  #
  import sys
  from PyQt4 import QtGui
  app = QtGui.QApplication(sys.argv)
  splash = QtGui.QSplashScreen(application_admin.getSplashscreen())
  splash.show()
  
  # regulary call processEvents to keep the splash alive
  splash.showMessage('Initialize application')
  app.processEvents()
    
  import logging
  logger = logging.getLogger('camelot.view.main')
  import settings
  from PyQt4 import QtCore

  QT_MAJOR_VERSION = float('.'.join(str(QtCore.QT_VERSION_STR).split('.')[0:2]))
  logger.debug('qt version %s, pyqt version %s' % 
               (QtCore.QT_VERSION_STR, QtCore.PYQT_VERSION_STR))
  logger.debug('qt major version %f' % QT_MAJOR_VERSION)

  # regulary call processEvents to keep the splash alive
  app.processEvents()
  
  import sqlalchemy, elixir
  logger.debug('sqlalchemy version %s'%sqlalchemy.__version__)
  logger.debug('elixir version %s'%elixir.__version__)

  # regulary call processEvents to keep the splash alive
  app.processEvents()
    
  app.setOrganizationName(application_admin.getOrganizationName())
  app.setOrganizationDomain(application_admin.getOrganizationDomain())
  app.setApplicationName(application_admin.getName())
  app.setWindowIcon(application_admin.getIcon())
  pre_initialization()
  app.processEvents()

  # regulary call processEvents to keep the splash alive
  splash.showMessage('Setup database')
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
  
  # Set the stylesheet
  splash.showMessage('Create main window')
  stylesheet = application_admin.getStylesheet()
  if stylesheet:
    app.setStyleSheet(stylesheet)
  
  # regulary call processEvents to keep the splash alive
  app.processEvents()
  
  # Application specific intialization instructions
  initialization()

  # regulary call processEvents to keep the splash alive
  app.processEvents()
    
  from camelot.view.mainwindow import MainWindow
  mainwindow = MainWindow(application_admin)
  mainwindow.show()
  splash.finish(mainwindow)
  sys.exit(app.exec_())
