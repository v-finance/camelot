from PyQt4 import QtCore

from ...admin.action.base import ActionStep

class Exit( ActionStep ):
    """
    Stop the event loop, and exit the application
    """
    
    def __init__( self, return_code=0 ):
        self.return_code = return_code
        
    def gui_run( self, gui_context ):
        QtCore.QCoreApplication.exit(self.return_code)
        
class MainWindow( ActionStep ):
    """
    Open a top level application window
    
    :param admin: a :class:`camelot.admin.application_admin.ApplicationAdmin'
        object

    """
    
    def __init__( self,
                  admin ):
        self.admin = admin
        
    def render( self, gui_context ):
        """create the main window. this method is used to unit test
        the action step."""
        from ..mainwindow import MainWindow
        return MainWindow( gui_context=gui_context )
        
    def gui_run( self, gui_context ):
        from camelot.view.register import register
        main_window = self.render( gui_context )
        register( main_window, main_window )
        main_window.show()
        
class InstallTranslator( ActionStep ):
    """
    Install a translator in the application
    
    :param admin: a :class:`camelot.admin.application_admin.ApplicationAdmin'
        object

    """
    
    def __init__( self,
                  admin ):
        self.admin = admin
        
    def gui_run( self, gui_context ):
        app = QtCore.QCoreApplication.instance()
        translator = self.admin.get_translator()
        if isinstance(translator, list):
            for t in translator:
                app.installTranslator( t )
        else:
            app.installTranslator( translator )        
