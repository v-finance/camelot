import logging
import sys

from PyQt4 import QtGui, QtCore

from ...core.utils import ugettext as _
from .application_action import ApplicationActionGuiContext
from .base import Action

logger = logging.getLogger('camelot.admin.action.application')

class Application( Action ):
    """The camelot application.  This class will take care of the order of
    initialization of various stuff needed to get the application up and
    running, each of its methods will be called in subsequent order,
    overwrite any of them to customize its behaviour.

    This class will create the QApplication and call its processEvents
    method regulary while starting up the application.
    """

    def __init__(self, application_admin):
        """:param application_admin: a subclass of camelot.admin.application_admin.ApplicationAdmin
        customized to your app"""
        super(Application, self).__init__()
        self.application_admin = application_admin
        self._splashscreen = None
        self.return_code = None

    def exit( self, return_code ):
        """Set the return_code of the application.  If this is set before the
        main event loop has started, the main event loop will not start, and
        the application will exit with this code"""
        self.return_code = return_code
        
    def gui_run(self, gui_context = ApplicationActionGuiContext() ):
        """The main entry point of the application, method will show the splash,
        start the event loop, start the model thread and pass control asap to 
        the model thread"""
        try:
            #
            # before anything else happens or is imported, the splash screen should be there
            #
            app = QtGui.QApplication([a for a in sys.argv if a])
            splash_window = self.show_splashscreen()
            self.show_splash_message(splash_window, _('Initialize application'))
            # regularly call processEvents to keep the splash alive
            app.processEvents()
            self.set_application_attributes(app)            
            app.processEvents()
            self.start_model_thread()
            app.processEvents()
            gui_context.admin = self.application_admin
            app.processEvents()
            stylesheet = self.application_admin.get_stylesheet()
            if stylesheet:
                app.setStyleSheet(stylesheet)
            super( Application, self ).gui_run( gui_context )
            splash_window.close()
            # to be able to exit the application before the event loop
            # has started
            if self.return_code == None:
                sys.exit( app.exec_() )
            else:
                sys.exit( self.return_code )
        except Exception, e:
            from ...view.controls import exception, ExceptionDialog
            exc_info = exception.register_exception( logger, 'exception in initialization', e )
            dialog = ExceptionDialog(exc_info)
            dialog._exec()
            
    def show_splashscreen(self):
        """:return: the splash window"""
        from PyQt4 import QtGui
        pixmap = self.application_admin.get_splashscreen()
        # don't let splash screen stay on top, this might hinder
        # registration wizards or others that wait for user input
        # while camelot is starting up
        # flag = QtCore.Qt.WindowStaysOnTopHint
        splashscreen = QtGui.QSplashScreen(pixmap) #, flag)
        # transparency support
        if pixmap.mask(): splashscreen.setMask(pixmap.mask()) 
        self._splashscreen = splashscreen
        splashscreen.show()
        return splashscreen

    def show_splash_message(self, splash_window, message):
        """:param message: displays a message on the splash screen, informing
        the user of the status of the application"""
        msgalign = QtCore.Qt.AlignTop #| QtCore.Qt.AlignRight
        msgcolor = QtCore.Qt.white
        splash_window.showMessage(message, msgalign, msgcolor)

    def set_application_attributes(self, application):
        """Sets the attributes of the QApplication object
        :param application: the QApplication object"""
        application.setOrganizationName(self.application_admin.get_organization_name())
        application.setOrganizationDomain(self.application_admin.get_organization_domain())
        application.setApplicationName(self.application_admin.get_name())
        application.setWindowIcon(self.application_admin.get_icon())

    def pre_initialization(self):
        """Method that is called before the model thread is started, while the app is still
        running single threaded.

        The default implementation verifies if the database_selection attribute is set to
        True on the ApplicationAdmin, and if this is the case, present the user with a
        database selection wizard.
        """
        if self.application_admin.database_selection:
            #
            # in case of profile selection, load the system locale translations for
            # the profile dialog.  These might be different from the final translations
            # that are specified in the profile
            #
            locale_name = QtCore.QLocale().name()
            language_name = locale_name.split('_')[0]
            camelot_translator = self.application_admin._load_translator_from_file( 'camelot', 
                                                                                    'camelot',
                                                                                    'art/translations/%s/LC_MESSAGES/'%language_name )
            if camelot_translator:
                QtCore.QCoreApplication.instance().installTranslator( camelot_translator )
            from camelot.view.database_selection import select_database
            select_database(self.application_admin)

    def start_model_thread(self):
        """Launch the second thread where the model lives"""
        from camelot.view.model_thread import get_model_thread, construct_model_thread
        from camelot.view.remote_signals import construct_signal_handler
        construct_model_thread()
        construct_signal_handler()
        mt = get_model_thread()
        mt.start()

    def model_run( self, model_context ):
        from ...core.conf import settings
        from ...core.utils import load_translations
        from ...view import action_steps
        #
        # log the libraries in use
        #
        if hasattr( QtCore, 'QT_MAJOR_VERSION'):
            QT_MAJOR_VERSION = float('.'.join(str(QtCore.QT_VERSION_STR).split('.')[0:2]))
            logger.debug('qt version %s, pyqt version %s' %
                         (QtCore.QT_VERSION_STR, QtCore.PYQT_VERSION_STR))
            logger.debug('qt major version %f' % QT_MAJOR_VERSION)
        import sqlalchemy
        logger.debug('sqlalchemy version %s'%sqlalchemy.__version__)
        #
        # setup the database model
        #
        yield action_steps.UpdateProgress( 0, 0, _('Setup database') )
        settings.setup_model()
        yield action_steps.UpdateProgress( 0, 0, _('Load translations') )
        load_translations()
        yield action_steps.UpdateProgress( 0, 0, _('Install translator') )
        yield action_steps.InstallTranslator( model_context.admin ) 
        yield action_steps.UpdateProgress( 0, 0, _('Create main window') )
        yield action_steps.MainWindow( self.application_admin )
        
