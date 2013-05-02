from ...admin.action.base import ActionStep

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
