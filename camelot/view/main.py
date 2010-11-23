#  ============================================================================
#
#  Copyright (C) 2007-2010 Conceptive Engineering bvba. All rights reserved.
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

class Application(QtCore.QObject):
    """The camelot application.  This class will take care of the order of
    initialization of various stuff needed to get the application up and
    running, each of its methods will be called in subsequent order,
    overwrite any of them to customize its behaviour.

    This class will create the QApplication and call its processEvents
    method regulary will starting up the application
    """

    def __init__(self, application_admin):
        """:param application_admin: a subclass of camelot.admin.application_admin.ApplicationAdmin
        customized to your app"""
        super(Application, self).__init__()
        self.application_admin = application_admin

    @QtCore.pyqtSlot(str, str)
    def setup_exception(self, exc_name, exc_trace):
        """This slot will be called when the setup of the model thread fails, eg
        in case of database connection failure"""
        from camelot.view.controls.exception import model_thread_exception_message_box
        model_thread_exception_message_box( (exc_name, exc_trace) )
    
    def show_splashscreen(self):
        """:return: the splash window"""
        from PyQt4 import QtGui
        pixmap = self.application_admin.get_splashscreen()
        # don't let splash screen stay on top, this might hinder
        # registration wizards or others that wait for user input
        # while camelot is starting up
        # flag = QtCore.Qt.WindowStaysOnTopHint
        splash_window = QtGui.QSplashScreen(pixmap) #, flag)
        splash_window.show()
        return splash_window

    def show_splash_message(self, splash_window, message):
        """:param message: displays a message on the splash screen, informing
        the user of the status of the application"""
        from PyQt4 import QtCore
        msgalign = QtCore.Qt.AlignBottom #| QtCore.Qt.AlignRight
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
        
        The default implementation does nothing and returns None. Overwrite
        this method for custom behaviour.
        
        An example use of this function would be to 
        present the user with a dialog to select the database to use, and to store the
        result in some global variable that is later used in the settings.ENGINE function.
        """
        pass

    def start_model_thread(self):
        """Launch the second thread where the model lives"""
        from camelot.view.model_thread import get_model_thread, construct_model_thread
        from camelot.view.remote_signals import construct_signal_handler
        construct_model_thread()
        construct_signal_handler()
        mt = get_model_thread()
        mt.setup_exception_signal.connect( self.setup_exception )
        mt.start()

    def load_translations(self, application):
        """Fill the QApplication with the needed translations
        :param application: the QApplication on which to install the translator
        """
        from camelot.core.utils import load_translations
        from camelot.view.model_thread import get_model_thread
        get_model_thread().post(load_translations)
        translator = self.application_admin.get_translator()
        application.installTranslator(translator)

    def initialization(self):
        """Method that is called afther the model has been set up, before the main
        window is constructed"""
        pass

    def create_main_window(self):
        """:return: a QWidget representing the main window, upon its appearance, the splash
        screen will be closed"""
        return self.application_admin.create_main_window()

    def close_splashscreen(self, splash_window, main_window):
        """closes the splashcreen on appearance of the main window
        :param splash_window: the splash screen window, as generated by the
        show splashcreen function
        """
        main_window.show()
        splash_window.finish(main_window)

    def start_event_loop(self, application):
        """Starts the application's main event loop, wait until it is finished, then
        exit
        :param application: the QApplication to run"""
        import sys
        sys.exit(application.exec_())

    def initialization_exception(self, exception_info):
        """This method is called whenever an exception occurs before the event
        loop has been started, by default, this method pops up a message box to
        inform the user
        :param exception_info: a tuple (exception, traceback_print) where traceback_print
        is a string representation of the traceback
        """
        from camelot.view.controls import exception
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

            QT_MAJOR_VERSION = float('.'.join(str(QtCore.QT_VERSION_STR).split('.')[0:2]))
            logger.debug('qt version %s, pyqt version %s' %
                         (QtCore.QT_VERSION_STR, QtCore.PYQT_VERSION_STR))
            logger.debug('qt major version %f' % QT_MAJOR_VERSION)
            app.processEvents()
            import sqlalchemy, elixir
            logger.debug('sqlalchemy version %s'%sqlalchemy.__version__)
            logger.debug('elixir version %s'%elixir.__version__)
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
            from camelot.view.model_thread import get_model_thread
            self.show_splash_message(splash_window, _('Load translations'))
            app.processEvents()
            get_model_thread().post(load_translations)
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

            #self.load_translations(app)
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
            self.close_splashscreen(splash_window, main_window)
            return self.start_event_loop(app)
        except Exception, e:
            logger.error( 'exception in initialization', exc_info = e )
            import traceback, cStringIO
            sio = cStringIO.StringIO()
            traceback.print_exc(file=sio)
            traceback_print = sio.getvalue()
            sio.close()
            exception_info = (e, traceback_print)
            self.initialization_exception(exception_info)

def main(application_admin,
         initialization=lambda:None,
         pre_initialization=lambda:None):
    """shortcut main function, call this function to start the GUI interface with minimal hassle
    and without the need to construct an Application object.  If you need to customize the initialization
    process, construct an Application subclass and use it's main method.

    @param application_admin: object of type ApplicationAdmin (as defined in application_admin.py)
    that specifies the look of the GUI interface
    @param initialization: function that will be called during the appearance of the splash
    screen, put all time consuming initialization here.  this function will be called after the
    model thread has been started.
    @param pre-initialization: function that will be called before the model thread has been started,
    but after the QApplication has been created.  This function can be used to run a configuration
    wizard before a connection to the database was made or any gui element has been constructed.
    """

    class ShortcutApplication(Application):

        def initialization(self):
            initialization()

        def pre_initialization(self):
            pre_initialization()

    app = ShortcutApplication(application_admin)
    app.main()

if __name__ == '__main__':
    from application_admin import ApplicationAdmin
    main(ApplicationAdmin())

