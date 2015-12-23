import logging
import sys

from ...core.qt import QtCore
from ...core.utils import ugettext as _
from ..application_admin import ApplicationAdmin
from .base import Action

logger = logging.getLogger('camelot.admin.action.application')

class Application( Action ):
    """An action to be used as the entry point of the application.  This
    action will pop up a splash window, set the application attributes, 
    initialize the database, install translators and construct a main window.
    
    Subclass this class and overwrite the :meth:`model_run` method to customize
    the application initialization process
    
    :param application_admin: a subclass of camelot.admin.application_admin.ApplicationAdmin
        customized to your app.  If no application_admin is passed, a default one is
        created (this is not recommended)
    """

    def __init__(self, application_admin=None):
        super(Application, self).__init__()
        if application_admin is None:
            application_admin = ApplicationAdmin()
        self.application_admin = application_admin
        self.gui_context = None
        
    def gui_run(self, gui_context ):
        """The main entry point of the application, method will show the splash,
        start the event loop, start the model thread and pass control asap to 
        the model thread"""
        from ...view.controls.progress_dialog import SplashProgress
        try:
            self.gui_context = gui_context
            #
            # before anything else happens or is imported, the splash screen should be there
            #
            pixmap = self.application_admin.get_splashscreen()
            if pixmap is not None:
                self.gui_context.progress_dialog = SplashProgress( pixmap )
                gui_context.progress_dialog.show()
                if sys.platform == 'darwin':
                    # Running on Mac OS X, focus application on launch
                    gui_context.progress_dialog.raise_()
                gui_context.progress_dialog.setLabelText( _('Initialize application') )
            self.set_application_attributes()
            self.gui_context.admin = self.application_admin
            super( Application, self ).gui_run( gui_context )
            if pixmap is not None:
                gui_context.progress_dialog.close()
        except Exception as e:
            from ...view.controls import exception
            exc_info = exception.register_exception( logger, 'exception in initialization', e )
            dialog = exception.ExceptionDialog(exc_info)
            dialog.exec_()
            QtCore.QCoreApplication.exit(-1)

    def set_application_attributes(self):
        """Sets the attributes of the QApplication object
        :param application: the QApplication object"""
        application = QtCore.QCoreApplication.instance()
        application.setOrganizationName(self.application_admin.get_organization_name())
        application.setOrganizationDomain(self.application_admin.get_organization_domain())
        application.setApplicationName(self.application_admin.get_name())
        application.setWindowIcon(self.application_admin.get_icon())
        stylesheet = self.application_admin.get_stylesheet()
        if stylesheet:
            application.setStyleSheet(stylesheet)

    #def pre_initialization(self):
        #"""Method that is called before the model thread is started, while the app is still
        #running single threaded.

        #The default implementation verifies if the database_selection attribute is set to
        #True on the ApplicationAdmin, and if this is the case, present the user with a
        #database selection wizard.
        #"""
        #if self.application_admin.database_selection:
            ##
            ## in case of profile selection, load the system locale translations for
            ## the profile dialog.  These might be different from the final translations
            ## that are specified in the profile
            ##
            #locale_name = QtCore.QLocale().name()
            #language_name = locale_name.split('_')[0]
            #camelot_translator = self.application_admin._load_translator_from_file( 'camelot', 
                                                                                    #'camelot',
                                                                                    #'art/translations/%s/LC_MESSAGES/'%language_name )
            #if camelot_translator:
                #QtCore.QCoreApplication.instance().installTranslator( camelot_translator )
            #from camelot.view.database_selection import select_database
            #select_database(self.application_admin)

    def model_run( self, model_context ):
        """
        Overwrite this generator method to customize the startup process of
        your application.
        
        :param model_context: a :class:`camelot.admin.action.base.ModelContext` object
        """
        from ...core.conf import settings
        from ...core.utils import load_translations
        from ...view import action_steps
        yield action_steps.UpdateProgress( 1, 5, _('Setup database') )
        settings.setup_model()
        yield action_steps.UpdateProgress( 2, 5, _('Load translations') )
        load_translations()
        yield action_steps.UpdateProgress( 3, 5, _('Install translator') )
        yield action_steps.InstallTranslator( model_context.admin ) 
        yield action_steps.UpdateProgress( 4, 5, _('Create main window') )
        yield action_steps.MainWindow( self.application_admin )
        home_actions = self.application_admin.get_actions()
        yield action_steps.ActionView( _('Home'), home_actions )
