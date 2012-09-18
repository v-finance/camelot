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

import logging
logger = logging.getLogger('camelot.view.mainwindow')

from PyQt4.QtCore import Qt
from PyQt4 import QtGui, QtCore

from camelot.view.controls.busy_widget import BusyWidget
from camelot.view.controls.navpane2 import NavigationPane
from camelot.view.model_thread import post

from camelot.core.utils import ugettext as _

class MainWindow(QtGui.QMainWindow):
    """Main window of a Desktop Camelot application
    
    :param gui_context: an :class:`camelot.admin.action.application_action.ApplicationActionGuiContext`
        object
    :param parent: a :class:`QtGui.QWidget` object or :class:`None` 
    
    .. attribute:: splash_screen 
        a :class:`QtGui.QWidget` that needs to be closed when
        the main window is shown.
    """

    def __init__(self, gui_context, parent=None):
        from workspace import DesktopWorkspace
        logger.debug('initializing main window')
        QtGui.QMainWindow.__init__(self, parent)

        self.splash_screen = None
        self.toolbars = []
        self.nav_pane = None
        self.app_admin = gui_context.admin.get_application_admin()
        
        logger.debug('setting up workspace')
        self.workspace = DesktopWorkspace( self.app_admin, self )
        self.gui_context = gui_context
        self.gui_context.workspace = self.workspace

        logger.debug('setting child windows dictionary')

        logger.debug('setting central widget to our workspace')
        self.setCentralWidget( self.workspace )

        self.workspace.change_view_mode_signal.connect( self.change_view_mode )
        self.workspace.last_view_closed_signal.connect( self.unmaximize_view )
        self.workspace.view_activated_signal.connect( self.view_activated )

        logger.debug('creating navigation pane')
        post( self.app_admin.get_sections, self.set_sections )
        
        logger.debug('creating the menus')
        post( self.app_admin.get_main_menu, self.set_main_menu )

        logger.debug('creating the toolbars')
        post( self.app_admin.get_toolbar_actions, 
              self.set_left_toolbar_actions,
              args = (Qt.LeftToolBarArea,) )
        post( self.app_admin.get_toolbar_actions, 
              self.set_right_toolbar_actions,
              args = (Qt.RightToolBarArea,) )
        post( self.app_admin.get_toolbar_actions, 
              self.set_top_toolbar_actions,
              args = (Qt.TopToolBarArea,) )
        post( self.app_admin.get_toolbar_actions, 
              self.set_bottom_toolbar_actions,
              args = (Qt.BottomToolBarArea,) )

        logger.debug('reading saved settings')
        self.read_settings()
        
        windowtitle = self.app_admin.get_name()
        logger.debug( u'setting up window title: %s'%windowtitle )
        self.setWindowTitle( windowtitle )
        self.app_admin.title_changed_signal.connect( self.setWindowTitle )

        logger.debug('initialization complete')

    @QtCore.pyqtSlot()
    def show( self ):
        """This method wait until the main window is completely set up, and
        only then shows it.  This is a workaround for a bug in Qt on OS X
        
        https://bugreports.qt.nokia.com/browse/QTBUG-18567
        
        """
        post( lambda:None, self._delayed_show )
        
    @QtCore.pyqtSlot(object)
    def _delayed_show( self, _o ):
        """Call to the underlying :meth:`QMainWindow.show`, to be used in
        :meth:`MainWindow.show`
        """
        super( MainWindow, self ).show()
        if self.splash_screen:
            self.splash_screen.close()
        
    @QtCore.pyqtSlot()
    def unmaximize_view( self ):
        """Show the navigation pane and the menu bar if they exist """
        if self.navpane:
            self.navpane.show()
        if self.menuBar():
            self.menuBar().show()

    @QtCore.pyqtSlot()
    def change_view_mode( self ):
        """Switch between hidden or shown menubar and navigation pane"""
        if self.menuBar().isHidden():
            if self.navpane:
                self.navpane.show()
            self.menuBar().show()
        else:
            if self.navpane:
                self.navpane.hide()
            self.menuBar().hide()

    def read_settings( self ):
        """Restore the geometry of the main window to its last saved state"""
        settings = QtCore.QSettings()
        self.restoreGeometry(settings.value('geometry').toByteArray())

    def write_settings(self):
        """Store the current geometry of the main window"""
        logger.debug('writing application settings')
        settings = QtCore.QSettings()
        settings.setValue('geometry', QtCore.QVariant(self.saveGeometry()))
        logger.debug('settings written')

    @QtCore.pyqtSlot( object )
    def set_main_menu( self, main_menu ):
        """Set the main menu
        :param main_menu: a list of :class:`camelot.admin.menu.Menu` objects,
            as returned by the :meth:`camelot.admin.application_admin.ApplicationAdmin.get_main_menu`
            method.
        """
        from camelot.view.controls.action_widget import ActionAction
        if main_menu == None:
            return
        menu_bar = self.menuBar()
        for menu in main_menu:
            menu_bar.addMenu( menu.render( self.gui_context, menu_bar ) )
        for qaction in menu_bar.findChildren( ActionAction ):
            qaction.triggered.connect( self.action_triggered )

    def get_gui_context( self ):
        """Get the :class:`GuiContext` of the active view in the mainwindow,
        or the :class:`GuiContext` of the application.

        :return: a :class:`camelot.admin.action.base.GuiContext`
        """
        active_view = self.gui_context.workspace.active_view()
        if active_view:
            return active_view.gui_context
        return self.gui_context
        
    @QtCore.pyqtSlot( object, object )
    def set_toolbar_actions( self, toolbar_area, toolbar_actions ):
        """Set the toolbar for a specific area
        :param toolbar_area: the area on which to put the toolbar, from
            :class:`Qt.LeftToolBarArea` through :class:`Qt.BottomToolBarArea`
        :param toolbar_actions: a list of :class:`camelot.admin.action..base.Action` objects,
            as returned by the :meth:`camelot.admin.application_admin.ApplicationAdmin.get_toolbar_actions`
            method.
        """
        from camelot.view.controls.action_widget import ActionAction
        if toolbar_actions != None:
            #
            # gather menu bar actions to prevent duplication of QActions
            #
            qactions = dict()
            menu_bar = self.menuBar()
            if menu_bar:
                for qaction in menu_bar.findChildren( ActionAction ):
                    qactions[qaction.action] = qaction
            toolbar = QtGui.QToolBar( _('Toolbar') )
            self.addToolBar( toolbar_area, toolbar )
            toolbar.setObjectName( 'MainWindowToolBar_%i'%toolbar_area )
            toolbar.setMovable( False )
            toolbar.setFloatable( False )
            for action in toolbar_actions:
                qaction = qactions.get( action, None )
                if qaction == None:
                    qaction = action.render( self.gui_context, toolbar )
                    qaction.triggered.connect( self.action_triggered )
                toolbar.addAction( qaction )
            self.toolbars.append( toolbar )
            toolbar.addWidget( BusyWidget() )
                
    @QtCore.pyqtSlot( object )
    def set_left_toolbar_actions( self, toolbar_actions ):
        self.set_toolbar_actions( Qt.LeftToolBarArea, toolbar_actions )
    
    @QtCore.pyqtSlot( object )
    def set_right_toolbar_actions( self, toolbar_actions ):
        self.set_toolbar_actions( Qt.RightToolBarArea, toolbar_actions )
        
    @QtCore.pyqtSlot( object )
    def set_top_toolbar_actions( self, toolbar_actions ):
        self.set_toolbar_actions( Qt.TopToolBarArea, toolbar_actions )
        
    @QtCore.pyqtSlot( object )
    def set_bottom_toolbar_actions( self, toolbar_actions ):
        self.set_toolbar_actions( Qt.BottomToolBarArea, toolbar_actions )

    @QtCore.pyqtSlot()
    def view_activated( self ):
        """Update the state of the actions when the active tab in the
        desktop widget has changed"""
        from camelot.view.controls.action_widget import ActionAction
        gui_context = self.get_gui_context()
        model_context = gui_context.create_model_context()
        for toolbar in self.toolbars:
            for qaction in toolbar.actions():
                if isinstance( qaction, ActionAction ):
                    post( qaction.action.get_state,
                          qaction.set_state,
                          args = ( model_context, ) )
        menu_bar = self.menuBar()
        if menu_bar:
            for qaction in menu_bar.findChildren( ActionAction ):
                post( qaction.action.get_state,
                      qaction.set_state,
                      args = ( model_context, ) )
        
    @QtCore.pyqtSlot( bool )
    def action_triggered( self, _checked = False ):
        """Execute an action that was triggered somewhere in the main window,
        such as the toolbar or the main menu"""
        action_action = self.sender()
        gui_context = self.get_gui_context()
        action_action.action.gui_run( gui_context )
        
    @QtCore.pyqtSlot( object )
    def set_sections( self, sections ):
        """Set the sections of the navigation pane
        :param main_menu: a list of :class:`camelot.admin.section.Section` objects,
            as returned by the :meth:`camelot.admin.application_admin.ApplicationAdmin.get_sections`
            method.
        """
        if sections != None:
            self.navpane = NavigationPane(
                self.app_admin,
                workspace=self.workspace,
                parent=self
            )
            self.addDockWidget( Qt.LeftDockWidgetArea, self.navpane )
        else:
            self.navpane = None

    def closeEvent( self, event ):
        from camelot.view.model_thread import get_model_thread
        model_thread = get_model_thread()
        self.workspace.close_all_views()
        self.write_settings()
        logger.info( 'closing mainwindow' )
        model_thread.stop()
        super( MainWindow, self ).closeEvent( event )
        QtCore.QCoreApplication.exit(0)

