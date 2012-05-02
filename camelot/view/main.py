#  ============================================================================
#
#  Copyright (C) 2007-2012 Conceptive Engineering bvba. All rights reserved.
#  www.conceptive.be / project-camelot@conceptive.be
#
#  This file is part of the Camelot Library.
#
#  This file may be used under the terms of the GNU General Public
#  License version 2.0 as published by the Free Software Foundation
#  and appearing in the file license.txt included in the packaging of
#  this file.  Please review this information to ensure GNU
#  General Public Licensing requirements will be met.
#
#  If you are unsure which license is appropriate for your use, please
#  visit www.python-camelot.com or contact project-camelot@conceptive.be
#
#  This file is provided AS IS with NO WARRANTY OF ANY KIND, INCLUDING THE
#  WARRANTY OF DESIGN, MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE.
#
#  For use of this library in commercial applications, please contact
#  project-camelot@conceptive.be
#
#  ============================================================================

"""Main function, to be called to start the GUI interface"""
from PyQt4 import QtCore
from camelot.core.utils import ugettext as _

from camelot.art import resources # Required for tooltip visualization
resources.__name__ # Dodge PyFlakes' attack

class Application(QtCore.QObject):
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
        from PyQt4 import QtCore
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

        The default implementation verifies if the select_database attribute is set to
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
        from camelot.core.conf import settings
        from camelot.core.sql import metadata
        metadata.bind = settings.ENGINE()
        construct_model_thread()
        construct_signal_handler()
        mt = get_model_thread()
        mt.setup_exception_signal.connect( self.initialization_exception )
        mt.start()

    def load_translations(self, application):
        """Fill the QApplication with the needed translations
        :param application: the QApplication on which to install the translator
        """
        from camelot.core.utils import load_translations
        from camelot.view.model_thread import get_model_thread
        get_model_thread().post(load_translations)
        for translator in self.application_admin.get_translator():
            application.installTranslator(translator)

    def initialization(self):
        """Method that is called afther the model has been set up, before the main
        window is constructed"""
        pass

    def create_main_window(self):
        """:return: a QWidget representing the main window, upon its appearance, the splash
        screen will be closed"""
        return self.application_admin.create_main_window()

    def start_event_loop(self, application):
        """Starts the application's main event loop, wait until it is finished, then
        exit
        :param application: the QApplication to run"""
        import sys
        sys.exit( application.exec_() )

    @QtCore.pyqtSlot(object)
    def initialization_exception(self, exception_info):
        """This method is called whenever an exception occurs before the event
        loop has been started, or if the setup of the model thread failed.  By
        default this pops up a dialog.
        
        :param exception_info: a serialized form of the exception
        """
        from camelot.view.controls import exception
        if self._splashscreen:
            self._splashscreen.hide()
        exception.model_thread_exception_message_box(exception_info)
        
    def main(self):
        """the main function of the application, this will call all other
        functions before starting the event loop"""
        import logging
        logger = logging.getLogger('camelot.view.main')

        try:
            #
            # before anything else happens or is imported, the splash screen should be there
            #
            import sys
            from PyQt4 import QtGui, QtCore
            app = QtGui.QApplication([a for a in sys.argv if a])
            splash_window = self.show_splashscreen()

            self.show_splash_message(splash_window, _('Initialize application'))
            # regularly call processEvents to keep the splash alive
            app.processEvents()
            #  font = app.font()
            #  font.setStyleStrategy(QtGui.QFont.PreferAntialias)
            #  font.setPointSize(font.pointSize()+1)
            #  app.setFont(font)
            if hasattr( QtCore, 'QT_MAJOR_VERSION'):
                QT_MAJOR_VERSION = float('.'.join(str(QtCore.QT_VERSION_STR).split('.')[0:2]))
                logger.debug('qt version %s, pyqt version %s' %
                             (QtCore.QT_VERSION_STR, QtCore.PYQT_VERSION_STR))
                logger.debug('qt major version %f' % QT_MAJOR_VERSION)
            app.processEvents()
            import sqlalchemy
            logger.debug('sqlalchemy version %s'%sqlalchemy.__version__)
            app.processEvents()
            self.set_application_attributes(app)
            self.pre_initialization()
            app.processEvents()
            # regularly call processEvents to keep the splash alive
            self.show_splash_message(splash_window, _('Setup database'))
            app.processEvents()
            self.start_model_thread()
            app.processEvents()
            #
            # WEIRD, if we put this code in a method, the translations
            # don't work
            #
            from camelot.core.utils import load_translations
            from camelot.view.model_thread import post
            self.show_splash_message(splash_window, _('Load translations'))
            app.processEvents()
            post(load_translations)
            self.show_splash_message(splash_window, _('Create translator'))
            app.processEvents()
            translator = self.application_admin.get_translator()
            self.show_splash_message(splash_window, _('Install translator'))
            if isinstance(translator, list):
                for t in translator:
                    app.installTranslator( t )
            else:
                app.installTranslator( translator )
            app.processEvents()
            # Set the style sheet
            self.show_splash_message(splash_window, _('Create main window'))
            app.processEvents()
            stylesheet = self.application_admin.get_stylesheet()
            if stylesheet:
                app.setStyleSheet(stylesheet)
            app.processEvents()
            self.initialization()
            app.processEvents()
            main_window = self.create_main_window()
            main_window.splash_screen = splash_window
            main_window.show()
            return self.start_event_loop(app)
        except Exception, e:
            from camelot.view.controls import exception
            exc_info = exception.register_exception( logger, 'exception in initialization', e )
            self.initialization_exception( exc_info )

def main(application_admin):
    """shortcut main function, call this function to start the GUI interface with minimal hassle
    and without the need to construct an Application object.  If you need to customize the initialization
    process, construct an Application subclass and use it's main method.

    :param application_admin: object of type ApplicationAdmin (as defined in application_admin.py)
    that specifies the look of the GUI interface
    """
    app = Application(application_admin)
    app.main()

if __name__ == '__main__':
    from application_admin import ApplicationAdmin
    main(ApplicationAdmin())



