from ..workspace import DesktopBackground
from ...admin.action.base import ActionStep
from ...core.qt import QtCore, Qt

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

    .. attribute:: window_title

        The title of the main window, defaults to the application name if `None`
        is given

    """
    
    def __init__( self,
                  admin ):
        self.admin = admin
        self.window_title = admin.get_name()
        self.sections = admin.get_sections()
        self.main_menu = admin.get_main_menu()
        self.left_toolbar_actions = admin.get_toolbar_actions(Qt.LeftToolBarArea)
        self.right_toolbar_actions = admin.get_toolbar_actions(Qt.RightToolBarArea)
        self.top_toolbar_actions = admin.get_toolbar_actions(Qt.TopToolBarArea)
        self.bottom_toolbar_actions = admin.get_toolbar_actions(Qt.BottomToolBarArea)
        self.hidden_actions = admin.get_hidden_actions()

    def render( self, gui_context ):
        """create the main window. this method is used to unit test
        the action step."""
        from ..mainwindow import MainWindow
        main_window_context = gui_context.copy()
        main_window_context.progress_dialog = None
        main_window_context.admin = self.admin
        main_window = MainWindow( gui_context=main_window_context )
        gui_context.workspace = main_window_context.workspace
        main_window.setWindowTitle( self.window_title )
        main_window.set_sections(self.sections)
        main_window.set_main_menu(self.main_menu)
        main_window.set_toolbar_actions(Qt.LeftToolBarArea,
                                        self.left_toolbar_actions)
        main_window.set_toolbar_actions(Qt.RightToolBarArea,
                                        self.right_toolbar_actions)
        main_window.set_toolbar_actions(Qt.TopToolBarArea,
                                        self.top_toolbar_actions)
        main_window.set_toolbar_actions(Qt.BottomToolBarArea,
                                        self.bottom_toolbar_actions)
        return main_window
        
    def gui_run( self, gui_context ):
        from camelot.view.register import register
        main_window = self.render( gui_context )
        register( main_window, main_window )
        main_window.show()

class ActionView( ActionStep ):
    """
    Open a new view which presents the user with a number of actions
    to trigger.
    
    :param title: the tile of the view
    :param actions: a list of actions
    """

    def __init__(self, title, actions):
        self.title = title
        self.actions = actions

    def render(self, gui_context):
        view = DesktopBackground(gui_context)
        view.set_actions(self.actions)
        return view

    def gui_run(self, gui_context):
        workspace = gui_context.workspace
        view = self.render(gui_context)
        workspace.set_view(view, title=self.title)

class InstallTranslator( ActionStep ):
    """
    Install a translator in the application.  Ownership of the translator will
    be moved to the application.
    
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
                t.setParent(app)
                app.installTranslator( t )
        else:
            app.installTranslator( translator )
