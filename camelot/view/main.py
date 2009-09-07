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
  wizard before a connection to the database was made or any gui element has been constructed.
  """
  #
  # before anything else happens or is imported, the splash screen should be there
  #
  import sys
  from PyQt4 import QtGui, QtCore
  app = QtGui.QApplication([a for a in sys.argv if a])
  pixmap = application_admin.getSplashscreen()
  flag = QtCore.Qt.WindowStaysOnTopHint
  splash = QtGui.QSplashScreen(pixmap, flag)
  splash.show()
  
  msgalign = QtCore.Qt.AlignBottom | QtCore.Qt.AlignRight
  msgcolor = QtCore.Qt.white

  # regularly call processEvents to keep the splash alive
  splash.showMessage('Initialize application...', msgalign, msgcolor)
  app.processEvents()
  
#  font = app.font()
#  font.setStyleStrategy(QtGui.QFont.PreferAntialias)
#  font.setPointSize(font.pointSize()+1)
#  app.setFont(font)
    
  import logging
  logger = logging.getLogger('camelot.view.main')
  import settings
  #from PyQt4 import QtCore

  QT_MAJOR_VERSION = float('.'.join(str(QtCore.QT_VERSION_STR).split('.')[0:2]))
  logger.debug('qt version %s, pyqt version %s' % 
               (QtCore.QT_VERSION_STR, QtCore.PYQT_VERSION_STR))
  logger.debug('qt major version %f' % QT_MAJOR_VERSION)

  # regularly call processEvents to keep the splash alive
  app.processEvents()
  
  #
  # call set local if not done yet
  #
  import locale
  language, encoding = locale.getlocale(locale.LC_ALL)
  if not language:
    locale.setlocale(locale.LC_ALL, '')
  
  import sqlalchemy, elixir
  logger.debug('sqlalchemy version %s'%sqlalchemy.__version__)
  logger.debug('elixir version %s'%elixir.__version__)

  # regularly call processEvents to keep the splash alive
  app.processEvents()
    
  app.setOrganizationName(application_admin.getOrganizationName())
  app.setOrganizationDomain(application_admin.getOrganizationDomain())
  app.setApplicationName(application_admin.getName())
  app.setWindowIcon(application_admin.getIcon())
  pre_initialization()
  app.processEvents()

  # regularly call processEvents to keep the splash alive
  splash.showMessage('Setup database...', msgalign, msgcolor)
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
  
  # Set the style sheet
  splash.showMessage('Create main window...', msgalign, msgcolor)
  stylesheet = application_admin.getStylesheet()
  if stylesheet:
    app.setStyleSheet(stylesheet)
  
  # regularly call processEvents to keep the splash alive
  app.processEvents()
  
  # Application specific initialization instructions
  initialization()

  # regularly call processEvents to keep the splash alive
  app.processEvents()
  
  mainwindow = application_admin.createMainWindow()
    
  mainwindow.show()
  splash.finish(mainwindow)
  sys.exit(app.exec_())
