#  ============================================================================
#
#  Copyright (C) 2007-2016 Conceptive Engineering bvba.
#  www.conceptive.be / info@conceptive.be
#
#  Redistribution and use in source and binary forms, with or without
#  modification, are permitted provided that the following conditions are met:
#      * Redistributions of source code must retain the above copyright
#        notice, this list of conditions and the following disclaimer.
#      * Redistributions in binary form must reproduce the above copyright
#        notice, this list of conditions and the following disclaimer in the
#        documentation and/or other materials provided with the distribution.
#      * Neither the name of Conceptive Engineering nor the
#        names of its contributors may be used to endorse or promote products
#        derived from this software without specific prior written permission.
#  
#  THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
#  ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
#  WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
#  DISCLAIMED. IN NO EVENT SHALL <COPYRIGHT HOLDER> BE LIABLE FOR ANY
#  DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
#  (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
#  LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
#  ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
#  (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
#  SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#
#  ============================================================================

from ..workspace import DesktopBackground
from ...admin.action.base import ActionStep
from ...core.qt import QtCore

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
        return view

    def gui_run(self, gui_context):
        workspace = gui_context.workspace
        view = self.render(workspace.gui_context)
        workspace.set_view(view, title=self.title)


class InstallTranslator(ActionStep):
    """
    Install a translator in the application.  Ownership of the translator will
    be moved to the application.

    :param admin: a :class:`camelot.admin.application_admin.ApplicationAdmin'
        object

    """

    def __init__(self, admin):
        self.admin = admin

    def gui_run(self, gui_context):
        app = QtCore.QCoreApplication.instance()
        translator = self.admin.get_translator()
        if isinstance(translator, list):
            for t in translator:
                t.setParent(app)
                app.installTranslator(t)
        else:
            app.installTranslator(translator)


class RemoveTranslators(ActionStep):
    """
    Unregister all previously installed translators from the application.

    :param admin: a :class:`camelot.admin.application_admin.ApplicationAdmin'
        object
    """

    def __init__(self, admin):
        self.admin = admin

    def gui_run(self, gui_context):
        app = QtCore.QCoreApplication.instance()
        for active_translator in app.findChildren(QtCore.QTranslator):
            app.removeTranslator(active_translator)

