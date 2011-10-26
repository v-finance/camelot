#  ============================================================================
#
#  Copyright (C) 2007-2011 Conceptive Engineering bvba. All rights reserved.
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

import functools
import logging
logger = logging.getLogger('camelot.view.mainwindow')

#
# Dummy imports to fool the windows installer and force
# it to include the right packages
#
# from sqlalchemy.databases import sqlite
# import sqlite3

from PyQt4.QtCore import Qt
from PyQt4 import QtGui, QtCore

from camelot.view.action import ActionFactory
from camelot.view.controls.navpane2 import NavigationPane
from camelot.view.controls.progress_dialog import ProgressDialog
from camelot.view.model_thread import post

from camelot.core.utils import ugettext as _

def addActions(target, actions):
    """add action objects to menus, menubars, and toolbars
    if action is None, add a separator.
    """
    for action in actions:
        if action is None:
            target.addSeparator()
        else:
            target.addAction(action)

class MainWindow(QtGui.QMainWindow):
    """Main window GUI"""

    def __init__(self, app_admin, parent=None):
        from workspace import DesktopWorkspace
        logger.debug('initializing main window')
        QtGui.QMainWindow.__init__(self, parent)

        self.app_admin = app_admin
        logger.debug('setting up workspace')
        self.workspace = DesktopWorkspace(app_admin, self)

        logger.debug('setting child windows dictionary')

        logger.debug('setting central widget to our workspace')
        self.setCentralWidget(self.workspace)

        self.workspace.view_activated_signal.connect(self.updateMenus)
        self.workspace.change_view_mode_signal.connect( self.change_view_mode )
        self.workspace.last_view_closed_signal.connect( self.unmaximize_view )

        logger.debug('creating navigation pane')
        self.createNavigationPane()

        logger.debug('creating all the required actions')
        self.createActions()

        logger.debug('creating the menus')
        self.createMenus()

        logger.debug('creating the toolbars')
        self.createToolBars()

        logger.debug('creating status bar')
        self.createStatusBar()

        logger.debug('updating menus')
        self.updateMenus()

        logger.debug('reading saved settings')
        self.readSettings()
        
        windowtitle = self.app_admin.get_name()
        logger.debug('setting up window title: %s' % windowtitle)
        self.setWindowTitle(windowtitle)
        self.app_admin.title_changed_signal.connect( self.setWindowTitle )

        #QtCore.QTimer.singleShot(0, self.doInitialization)
        logger.debug('initialization complete')
        
    def about(self):
        logger.debug('showing about message box')
        abtmsg = self.app_admin.get_about()
        QtGui.QMessageBox.about(self, _('About'), _(abtmsg))
        logger.debug('about message closed')

    def whats_new(self):
        widget = self.app_admin.get_whats_new()
        if widget:
            widget.exec_()

    def affiliated_website(self):
        from PyQt4.QtGui import QDesktopServices
        url = self.app_admin.get_affiliated_url()
        if url:
            QDesktopServices.openUrl(url)

    def remote_support(self):
        from PyQt4.QtGui import QDesktopServices
        url = self.app_admin.get_remote_support_url()
        if url:
            QDesktopServices.openUrl(url)

    @QtCore.pyqtSlot()
    def unmaximize_view(self):
        self.navpane.show()
        self.menuBar().show()

    @QtCore.pyqtSlot()
    def change_view_mode(self):
        if self.menuBar().isHidden():
            self.navpane.show()
            self.menuBar().show()
        else:
            self.navpane.hide()
            self.menuBar().hide()

    def readSettings(self):
        settings = QtCore.QSettings()
        self.restoreGeometry(settings.value('geometry').toByteArray())
        # Don't restore state, since it messes up the toolbar if stuff was
        # added
        # self.restoreState(settings.value('state').toByteArray())

    def writeSettings(self):
        logger.debug('writing application settings')
        settings = QtCore.QSettings()
        settings.setValue('geometry', QtCore.QVariant(self.saveGeometry()))
        #settings.setValue('state', QtCore.QVariant(self.saveState()))
        logger.debug('settings written')

    def display_exception_message_box(self, exc_info):
        from controls.exception import model_thread_exception_message_box
        model_thread_exception_message_box(exc_info)

    def runAction(self, name, callable):
        progress = QtGui.QProgressDialog(_('Please wait'), QtCore.QString(), 0, 0)
        progress.setWindowTitle(name)
        progress.show()
        post(
            callable,
            progress.close,
            exception=self.display_exception_message_box
        )

    def createActions(self):
        self.backupAct = ActionFactory.backup(self, self.backup)
        self.restoreAct = ActionFactory.restore(self, self.restore)
        self.pageSetupAct = ActionFactory.page_setup(self, self.pageSetup)
        self.previewAct = ActionFactory.print_preview(self, self.previewDoc)
        self.exitAct= ActionFactory.exit(self, slot=self.close)
        self.copyAct = ActionFactory.copy(self, slot=self.copy)
        self.selectAllAct = ActionFactory.select_all(self, slot=self.select_all)
        self.separatorAct = QtGui.QAction(self)
        self.separatorAct.setSeparator(True)
        self.aboutAct = ActionFactory.about(self, slot=self.about)
        self.whats_new_action = ActionFactory.whats_new(self, slot=self.whats_new)
        self.affiliated_website_action = ActionFactory.affiliated_website(self, slot=self.affiliated_website)
        self.remote_support_action =ActionFactory.remote_support(self, slot=self.remote_support)
        self.helpAct = ActionFactory.help(self, slot=self.help)
        self.newAct = ActionFactory.new(self, slot=self.new)
        self.deleteAct = ActionFactory.delete(self, slot=self.delete)
        self.viewFirstAct = ActionFactory.view_first(self, self.viewFirst)
        self.viewLastAct = ActionFactory.view_last(self, self.viewLast)
        self.viewNextAct = ActionFactory.view_next(self, self.viewNext)
        self.viewPreviousAct = ActionFactory.view_previous(self, self.viewPrevious)
        self.viewFirstAct.setIconVisibleInMenu(False)
        self.viewLastAct.setIconVisibleInMenu(False)
        self.viewNextAct.setIconVisibleInMenu(False)
        self.viewPreviousAct.setIconVisibleInMenu(False)
        self.updateValueAct = ActionFactory.update_values(self, slot = self.updateValue)
        self.mergeDocumentAct = ActionFactory.merge_document(self, slot = self.merge_document)
        self.exportToExcelAct = ActionFactory.export_excel(self, slot=self.exportToExcel)
        self.exportToWordAct = ActionFactory.export_word(self, slot=self.exportToWord)
        self.exportToMailAct = ActionFactory.export_mail(self, slot=self.exportToMail)
        self.importFromFileAct = ActionFactory.import_file(self, slot=self.importFromFile)
        self.sessionRefreshAct = ActionFactory.refresh(self, slot=self.refresh_session)

    # QAction slots and methods implementations

    def refresh_session(self):
        from elixir import session
        from camelot.core.orm import refresh_session
        post( functools.update_wrapper( functools.partial( refresh_session, session ), refresh_session ) )
        self.workspace.refresh()

    def help(self):
        #
        # Import WebKit as late as possible, since it's the largest
        # part of the QT Library (15 meg on Ubuntu linux)
        #
        from PyQt4 import QtWebKit
        TOP_LEVEL = None
        self.view = QtWebKit.QWebView(TOP_LEVEL)
        #print self.app_admin.get_help_url()
        #print self.app_admin.get_help_base()
        #index_file = open(self.app_admin.get_help_url(),'r')
        #self.view.setHtml (index_file.read(), self.app_admin.get_help_base())
        self.view.load(self.app_admin.get_help_url())
        self.view.setWindowTitle(_('Help Browser'))
        self.view.setWindowIcon(self.helpAct.icon())
        self.view.show()

    def backup(self):
        self.app_admin.backup(self)

    def restore(self):
        self.app_admin.restore(self)

    def saveAs(self):
        pass

    def copy(self):
        self.activeMdiChild().copy_selected_rows()

    def select_all(self):
        self.activeMdiChild().select_all_rows()

    def previewDoc(self):
        active = self.activeMdiChild()
        from camelot.admin.action import Action, GuiContext
        from camelot.view.action_steps import PrintHtml

        class PrintPreviewAction( Action ):
            
            def model_run( self, model_context ):
                yield PrintHtml( active.to_html() )

        action = PrintPreviewAction()
        action.gui_run( GuiContext() )

    def new(self):
        self.activeMdiChild().newRow()

    def delete(self):
        self.activeMdiChild().deleteSelectedRows()

    def pageSetup(self):
        pass

    def viewFirst(self):
        """selects view's first row"""
        active = self.activeMdiChild()
        active.viewFirst()

    def viewLast(self):
        """selects view's last row"""
        active = self.activeMdiChild()
        active.viewLast()

    def viewNext(self):
        """selects view's next row"""
        active = self.activeMdiChild()
        active.viewNext()

    def viewPrevious(self):
        """selects view's previous row"""
        active = self.activeMdiChild()
        active.viewPrevious()

    def updateValue(self):
        from camelot.view.wizard.update_value import UpdateValueWizard

        admin = self.activeMdiChild().get_admin()
        selection_getter = self.activeMdiChild().get_selection_getter()
        wizard = UpdateValueWizard(admin=admin, selection_getter=selection_getter)
        wizard.exec_()

    def merge_document(self):
        """Run the merge document wizard on the selection in the current
        table view"""
        from camelot.view.wizard.merge_document import MergeDocumentWizard

        selection_getter = self.activeMdiChild().get_selection_getter()
        wizard = MergeDocumentWizard(selection_getter=selection_getter)
        wizard.exec_()

    def exportToExcel(self):
        """creates an excel file from the view"""
        widget = self.activeMdiChild()
        d = ProgressDialog(_('Please wait'))
        post(widget.export_to_excel, d.finished, d.exception)
        d.exec_()

    def exportToWord(self):
        """Use windows COM to export the active child window to MS word,
        by using its to_html function"""
        widget = self.activeMdiChild()
        d = ProgressDialog(_('Please wait'))
        post(widget.export_to_word, d.finished, d.exception)
        d.exec_()

    def exportToMail(self):
        widget = self.activeMdiChild()
        d = ProgressDialog(_('Please wait'))
        post(widget.export_to_mail, d.finished, d.exception)
        d.exec_()

    def importFromFile(self):
        self.activeMdiChild().importFromFile()

    def createMenus(self):

        self.file_menu = self.menuBar().addMenu(_('&File'))
        addActions(self.file_menu, (
            #self.closeAct,
            None,
            self.backupAct,
            self.restoreAct,
            None,
            self.pageSetupAct,
            self.previewAct,
            None
        ))

        self.exportMenu = QtGui.QMenu(_('Export To'))
        addActions(self.exportMenu, (
            self.exportToExcelAct,
            self.exportToWordAct,
            self.exportToMailAct,
        ))
        self.file_menu.addMenu(self.exportMenu)

        self.importMenu = QtGui.QMenu(_('Import From'))
        addActions(self.importMenu, (self.importFromFileAct,))
        self.file_menu.addMenu(self.importMenu)

        addActions(self.file_menu, (None, self.exitAct))

        self.editMenu = self.menuBar().addMenu(_('&Edit'))

        addActions(self.editMenu, (self.copyAct,
                                   self.selectAllAct,
                                   self.updateValueAct,
                                   self.mergeDocumentAct))

        self.viewMenu = self.menuBar().addMenu(_('View'))
        addActions(self.viewMenu, (self.sessionRefreshAct,))
        gotoMenu = self.viewMenu.addMenu(_('Go To'))
        addActions(gotoMenu, (
            self.viewFirstAct,
            self.viewPreviousAct,
            self.viewNextAct,
            self.viewLastAct
        ))

        self.menuBar().addSeparator()

        self.helpMenu = self.menuBar().addMenu(_('&Help'))

        help_menu_actions = [self.helpAct, self.aboutAct]
        if self.app_admin.get_whats_new():
            help_menu_actions.append(self.whats_new_action)
        if self.app_admin.get_affiliated_url():
            help_menu_actions.append(self.affiliated_website_action)
        if self.app_admin.get_remote_support_url():
            help_menu_actions.append(self.remote_support_action)
        addActions(self.helpMenu, help_menu_actions )

    def updateMenus(self):
        """Toggle the status of the menus, depending on the active view"""
        active_view = (self.workspace.active_view() is not None)
        self.backupAct.setEnabled(True)
        self.restoreAct.setEnabled(True)

        self.pageSetupAct.setEnabled(active_view)
        self.previewAct.setEnabled(active_view)

        self.newAct.setEnabled(active_view)
        self.deleteAct.setEnabled(active_view)
        self.copyAct.setEnabled(active_view)
        self.viewFirstAct.setEnabled(active_view)
        self.viewPreviousAct.setEnabled(active_view)
        self.viewNextAct.setEnabled(active_view)
        self.viewLastAct.setEnabled(active_view)

        self.exportToWordAct.setEnabled(active_view)
        self.exportToExcelAct.setEnabled(active_view)
        self.exportToMailAct.setEnabled(active_view)

        self.importFromFileAct.setEnabled(active_view)

        self.separatorAct.setVisible(active_view)

    def get_tool_bar(self):
        return self.tool_bar

    def createToolBars(self):
        #
        # All actions are put in one toolbar, to ease unit testing and
        # generation of screenshots
        #
        self.tool_bar = self.addToolBar(_('Toolbar'))
        self.tool_bar.setObjectName('ToolBar')
        self.tool_bar.setMovable(False)
        self.tool_bar.setFloatable(False)
        addActions(self.tool_bar, (
            self.newAct,
            self.copyAct,
            self.deleteAct,
            self.viewFirstAct,
            self.viewPreviousAct,
            self.viewNextAct,
            self.viewLastAct
        ))

        addActions(self.tool_bar, (
            self.exportToExcelAct,
            self.exportToWordAct,
            self.exportToMailAct,
        ))

        addActions(self.tool_bar, (self.previewAct,))

        addActions(self.tool_bar, (self.helpAct,))

    # Navigation Pane
    def createNavigationPane(self):
        self.navpane = NavigationPane(
            self.app_admin,
            workspace=self.workspace,
            parent=self
        )
        self.addDockWidget(Qt.LeftDockWidgetArea, self.navpane)

    def activeMdiChild(self):
        return self.workspace.active_view()

    # Statusbar
    def createStatusBar(self):
        from controls.statusbar import StatusBar
        statusbar = StatusBar(self)
        self.setStatusBar(statusbar)
        statusbar.showMessage(_('Ready'), 5000)

    def closeEvent(self, event):
        from camelot.view.model_thread import get_model_thread
        model_thread = get_model_thread()
        self.workspace.close_all_views()
        self.writeSettings()
        logger.info( 'closing mainwindow' )
        model_thread.stop()
        super( MainWindow, self ).closeEvent( event )
        QtCore.QCoreApplication.exit(0)
