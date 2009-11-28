#  ============================================================================
#
#  Copyright (C) 2007-2008 Conceptive Engineering bvba. All rights reserved.
#  www.conceptive.be / project-camelot@conceptive.be
#
#  This file is part of the Camelot Library.
#
#  This file may be used under the terms of the GNU General Public
#  License version 2.0 as published by the Free Software Foundation
#  and appearing in the file LICENSE.GPL included in the packaging of
#  this file.  Please review the following information to ensure GNU
#  General Public Licensing requirements will be met:
#  http://www.trolltech.com/products/qt/opensource.html
#
#  If you are unsure which license is appropriate for your use, please
#  review the following information:
#  http://www.trolltech.com/products/qt/licensing.html or contact
#  project-camelot@conceptive.be.
#
#  This file is provided AS IS with NO WARRANTY OF ANY KIND, INCLUDING THE
#  WARRANTY OF DESIGN, MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE.
#
#  For use of this library in commercial applications, please contact
#  project-camelot@conceptive.be
#
#  ============================================================================

import logging

logger = logging.getLogger( 'mainwindow' )
logger.setLevel( logging.INFO )

#
# Dummy imports to fool the windows installer and force
# it to include the right packages
#
from sqlalchemy.databases import sqlite
import sqlite3

from PyQt4.QtCore import Qt
from PyQt4 import QtGui, QtCore
from PyQt4 import QtWebKit

from camelot.view.art import Icon
from camelot.action import createAction, addActions
from camelot.view.controls.navpane import NavigationPane
from camelot.view.controls.printer import Printer
from camelot.view.model_thread import post

QT_MAJOR_VERSION = float( '.'.join( str( QtCore.QT_VERSION_STR ).split( '.' )[0:2] ) )

from camelot.core.utils import ugettext as _

class MainWindow( QtGui.QMainWindow ):
    """Main window GUI"""

    def __init__( self, app_admin, parent = None ):
        from workspace import construct_workspace
        logger.debug( 'initializing main window' )
        QtGui.QMainWindow.__init__( self, parent )

        self.app_admin = app_admin

        logger.debug( 'setting up workspace' )
        self.workspace = construct_workspace( self )

        logger.debug( 'setting child windows dictionary' )

        logger.debug( 'setting central widget to our workspace' )
        self.setCentralWidget( self.workspace )

        self.connect( self.workspace,
                     QtCore.SIGNAL( 'subWindowActivated(QMdiSubWindow *)' ),
                     self.updateMenus )

        logger.debug( 'creating navigation pane' )
        self.createNavigationPane()

        logger.debug( 'creating all the required actions' )
        self.createActions()

        logger.debug( 'creating the menus' )
        self.createMenus()

        logger.debug( 'creating the toolbars' )
        self.createToolBars()

        logger.debug( 'creating status bar' )
        self.createStatusBar()

        logger.debug( 'updating menus' )
        self.updateMenus()

        logger.debug( 'reading saved settings' )
        self.readSettings()

        logger.debug( 'setting up printer object' )
        self.printer = Printer()

        logger.debug( 'setting up window title' )
        self.setWindowTitle( self.app_admin.get_name() )
        
        #QtCore.QTimer.singleShot(0, self.doInitialization)
        logger.debug( 'initialization complete' )
        
    # Application settings

    def about( self ):
        logger.debug( 'showing about message box' )
        abtmsg = self.app_admin.get_about()
        QtGui.QMessageBox.about( self, _( 'About' ), _( abtmsg ) )
        logger.debug( 'about message closed' )

    def readSettings( self ):
        # TODO: improve settings reading
        settings = QtCore.QSettings()
        self.restoreGeometry( settings.value( 'geometry' ).toByteArray() )
        # Don't restore state, since it messes up the toolbar if stuff was
        # added
        # self.restoreState(settings.value('state').toByteArray())

    def writeSettings( self ):
        # TODO: improve settings saving
        logger.debug( 'writing application settings' )
        settings = QtCore.QSettings()
        settings.setValue( 'geometry', QtCore.QVariant( self.saveGeometry() ) )
        settings.setValue( 'state', QtCore.QVariant( self.saveState() ) )
        logger.debug( 'settings written' )

    def runAction( self, name, callable ):
        progress = QtGui.QProgressDialog( 'Please wait', 'Run in background', 0, 0 )
        progress.setWindowTitle( name )
        progress.show()

        from controls.exception import model_thread_exception_message_box
        post( callable, progress.close, model_thread_exception_message_box )

    # QAction objects creation methods
    def createActions( self ):
        icon_save = Icon( 'tango/16x16/actions/document-save.png' ).fullpath()
        icon_pgsetup = Icon( 'tango/16x16/actions/document-properties.png' ).fullpath()
        icon_print = Icon( 'tango/16x16/actions/document-print.png' ).fullpath()
        icon_preview = Icon( 'tango/16x16/actions/document-print-preview.png' ).fullpath()

        icon_cut = Icon( 'tango/16x16/actions/edit-cut.png' ).fullpath()
        icon_copy = Icon( 'tango/16x16/actions/edit-copy.png' ).fullpath()
        icon_paste = Icon( 'tango/16x16/actions/edit-paste.png' ).fullpath()

        icon_new = Icon( 'tango/16x16/actions/document-new.png' ).fullpath()
        icon_delete = Icon( 'tango/16x16/places/user-trash.png' ).fullpath()

        icon_gofirst = Icon( 'tango/16x16/actions/go-first.png' ).fullpath()
        icon_golast = Icon( 'tango/16x16/actions/go-last.png' ).fullpath()
        icon_gonext = Icon( 'tango/16x16/actions/go-next.png' ).fullpath()
        icon_goprevious = Icon( 'tango/16x16/actions/go-previous.png' ).fullpath()

        icon_excel = Icon( 'tango/16x16/mimetypes/x-office-spreadsheet.png' ).fullpath()
        icon_word = Icon( 'tango/16x16/mimetypes/x-office-document.png' ).fullpath()
        icon_mail = Icon( 'tango/16x16/actions/mail-message-new.png' ).fullpath()

        icon_import = Icon( 'tango/16x16/mimetypes/text-x-generic.png' ).fullpath()

        icon_help = Icon( 'tango/16x16/apps/help-browser.png' ).fullpath()

        # TODO: change some of the status tips
        self.saveAct = createAction( parent = self,
                                    text = _( '&Save' ),
                                    slot = self.save,
                                    shortcut = QtGui.QKeySequence.Save,
                                    actionicon = icon_save,
                                    tip = _( 'Save' ) )

        self.pageSetupAct = createAction( parent = self,
                                         text = _( 'Page Setup...' ),
                                         slot = self.pageSetup,
                                         actionicon = icon_pgsetup,
                                         tip = _( 'Page Setup...' ) )

        self.printAct = createAction( parent = self,
                                     text = _( 'Print...' ),
                                     slot = self.printDoc,
                                     shortcut = QtGui.QKeySequence.Print,
                                     actionicon = icon_print,
                                     tip = _( 'Print...' ) )

        self.previewAct = createAction( parent = self,
                                       text = _( 'Print Preview' ),
                                       slot = self.previewDoc,
                                       actionicon = icon_preview,
                                       tip = _( 'Print Preview' ) )

        self.exitAct = createAction( parent = self,
                                    text = _( 'E&xit' ),
                                    slot = self.close,
                                    tip = _( 'Exit the application' ) )

        tip = _( "Cut the current selection's contents to the clipboard" )
        self.cutAct = createAction( parent = self,
                                   text = _( 'Cu&t' ),
                                   slot = self.cut,
                                   shortcut = QtGui.QKeySequence.Cut,
                                   actionicon = icon_cut,
                                   tip = tip )

        tip = _( "Copy the current selection's contents to the clipboard" )
        self.copyAct = createAction( parent = self,
                                    text = _( '&Copy' ),
                                    slot = self.copy,
                                    shortcut = QtGui.QKeySequence.Copy,
                                    actionicon = icon_copy,
                                    tip = tip )

        tip = _( "Paste the clipboard's contents into the current selection" )
        self.pasteAct = createAction( parent = self,
                                     text = _( '&Paste' ),
                                     slot = self.paste,
                                     shortcut = QtGui.QKeySequence.Paste,
                                     actionicon = icon_paste,
                                     tip = tip )

        # BUG: there is a problem with setting a key sequence for closing
        #      a subwindow.  PyQt adopts defaults from specific platforms
        #      but we want the sequence Ctrl+W on every platform.  there-
        #      fore we set the string 'Ctrl+W', but PyQt defaults will
        #      still work.
        self.closeAct = createAction( parent = self,
                                     text = _( 'Cl&ose' ),
                                     slot = self.workspace.closeActiveSubWindow,
                                     shortcut = 'Ctrl+W',
                                     tip = _( 'Close the active window' ) )

        self.closeAllAct = createAction( parent = self,
                                        text = _( 'Close &All' ),
                                        slot = self.workspace.closeAllSubWindows,
                                        tip = _( 'Close all the windows' ) )

        self.cascadeAct = createAction( parent = self,
                                       text = _( '&Cascade windows' ),
                                       slot = self.workspace.cascadeSubWindows,
                                       tip = _( 'Arranges all the child windows '
                                             'in a cascade pattern.' ) )

        self.separatorAct = QtGui.QAction( self )
        self.separatorAct.setSeparator( True )

        self.aboutAct = createAction( parent = self,
                                     text = _( '&About' ),
                                     slot = self.about,
                                     tip = _( "Show the application's About box" ) )

        self.helpAct = createAction( parent = self,
                                     text = _( 'Help' ),
                                     slot = self.help,
                                     shortcut = QtGui.QKeySequence.HelpContents,
                                     actionicon = icon_help,
                                     tip = _( 'Help content' ) )

        self.newAct = createAction( parent = self,
                                   text = _( 'New' ),
                                   slot = self.new,
                                   shortcut = QtGui.QKeySequence.New,
                                   actionicon = icon_new,
                                   tip = _( 'New' ) )

        self.deleteAct = createAction( parent = self,
                                      text = _( 'Delete' ),
                                      slot = self.delete,
                                      shortcut = QtGui.QKeySequence.Delete,
                                      actionicon = icon_delete,
                                      tip = _( 'Delete' ) )

        self.viewFirstAct = createAction( parent = self,
                                         text = _( 'First' ),
                                         slot = self.viewFirst,
                                         shortcut = QtGui.QKeySequence.MoveToStartOfDocument,
                                         actionicon = icon_gofirst,
                                         tip = _( 'First' ) )

        self.viewLastAct = createAction( parent = self,
                                        text = _( 'Last' ),
                                        slot = self.viewLast,
                                        shortcut = QtGui.QKeySequence.MoveToEndOfDocument,
                                        actionicon = icon_golast,
                                        tip = _( 'Last' ) )

        self.viewNextAct = createAction( parent = self,
                                        text = _( 'Next' ),
                                        slot = self.viewNext,
                                        shortcut = QtGui.QKeySequence.MoveToNextPage,
                                        actionicon = icon_gonext,
                                        tip = _( 'Next' ) )

        self.viewPreviousAct = createAction( parent = self,
                                            text = _( 'Previous' ),
                                            slot = self.viewPrevious,
                                            shortcut = QtGui.QKeySequence.MoveToPreviousPage,
                                            actionicon = icon_goprevious,
                                            tip = _( 'Previous' ) )

        if QT_MAJOR_VERSION > 4.3:
            self.viewFirstAct.setIconVisibleInMenu( False )
            self.viewLastAct.setIconVisibleInMenu( False )
            self.viewNextAct.setIconVisibleInMenu( False )
            self.viewPreviousAct.setIconVisibleInMenu( False )

        self.exportToExcelAct = createAction( parent = self,
                                             text = _( 'Export to MS Excel' ),
                                             slot = self.exportToExcel,
                                             actionicon = icon_excel,
                                             tip = _( 'Export to MS Excel' ) )

        self.exportToWordAct = createAction( parent = self,
                                            text = _( 'Export to MS Word' ),
                                            slot = self.exportToWord,
                                            actionicon = icon_word,
                                            tip = _( 'Export to MS Word' ) )

        self.exportToMailAct = createAction( parent = self,
                                            text = _( 'Send by e-mail' ),
                                            slot = self.exportToMail,
                                            actionicon = icon_mail,
                                            tip = _( 'Send by e-mail' ) )

        self.importFromFileAct = createAction( parent = self,
                                              text = _( 'Import from file' ),
                                              slot = self.importFromFile,
                                              actionicon = icon_import,
                                              tip = _( 'Import from file' ) )

        from camelot.action.refresh import SessionRefresh

        self.sessionRefreshAct = SessionRefresh( self )

        self.app_actions = []
        for name, icon, callable in self.app_admin.get_actions():

            def bind_callable( name, callable ):
                return lambda:self.runAction( name, callable )

            self.app_actions.append( createAction( parent = self,
                                                 text = name,
                                                 slot = bind_callable( name, callable ),
                                                 actionicon = icon,
                                                 tip = name ) )

    # QAction slots and methods implementations

    def help( self ):
        TOP_LEVEL = None
        self.view = QtWebKit.QWebView( TOP_LEVEL )
        #print self.app_admin.get_help_url()
        #print self.app_admin.get_help_base()
        #index_file = open(self.app_admin.get_help_url(),'r')
        #self.view.setHtml ( index_file.read(), self.app_admin.get_help_base() )
        self.view.load( self.app_admin.get_help_url() )
        self.view.setWindowTitle( _('Help Browser') )
        self.view.setWindowIcon( self.helpAct.icon() )
        self.view.show()

    def save( self ):
        pass

    def saveAs( self ):
        pass

    def cut( self ):
        pass

    def copy( self ):
        pass

    def paste( self ):
        pass

    def printDoc( self ):
        self.previewDoc()

    def previewDoc( self ):
        active = self.activeMdiChild()
        from camelot.admin.form_action import PrintHtmlFormAction

        class PrintPreview(PrintHtmlFormAction):

            def html( self, entity_getter ):
                return active.widget().toHtml()

        action = PrintPreview('Print Preview')
        action.run(lambda:None)

    def new( self ):
        self.activeMdiChild().widget().newRow()

    def delete( self ):
        self.activeMdiChild().widget().deleteSelectedRows()

    def pageSetup( self ):
        pass

    def viewFirst( self ):
        """selects view's first row"""
        active = self.activeMdiChild()
        active.widget().viewFirst()

    def viewLast( self ):
        """selects view's last row"""
        active = self.activeMdiChild()
        active.widget().viewLast()

    def viewNext( self ):
        """selects view's next row"""
        active = self.activeMdiChild()
        active.widget().viewNext()

    def viewPrevious( self ):
        """selects view's previous row"""
        active = self.activeMdiChild()
        active.widget().viewPrevious()

    def exportToExcel( self ):
        """creates an excel file from the view"""

        def export():
            from export.excel import open_data_with_excel
            title = self.activeMdiChild().widget().getTitle()
            columns = self.activeMdiChild().widget().getColumns()
            data = [d for d in self.activeMdiChild().widget().getData()]
            open_data_with_excel( title, columns, data )

        post( export )

    def exportToWord( self ):
        """Use windows COM to export the active child window to MS word,
        by using its toHtml function"""

        def export():
            from export.word import open_html_in_word
            html = self.activeMdiChild().widget().toHtml()
            open_html_in_word( html )

        post( export )

    def exportToMail( self ):

        def export():
            from export.outlook import open_html_in_outlook
            html = self.activeMdiChild().widget().toHtml()
            open_html_in_outlook( html )

        post( export )

    def importFromFile( self ):
        self.activeMdiChild().widget().importFromFile()

    def createMenus( self ):
        
        self.fileMenu = self.menuBar().addMenu( _( '&File' ) )
        addActions( self.fileMenu, ( self.closeAct,
                                   None, self.saveAct,
                                   None, self.pageSetupAct,
                                   self.previewAct,
                                   self.printAct, None ) )

        self.exportMenu = QtGui.QMenu( _( 'Export To' ) )
        addActions( self.exportMenu, ( self.exportToExcelAct,
                                     self.exportToWordAct,
                                     self.exportToMailAct,
                                     ) )
        self.fileMenu.addMenu( self.exportMenu )

        self.importMenu = QtGui.QMenu( _( 'Import From' ) )
        addActions( self.importMenu, ( self.importFromFileAct, ) )
        self.fileMenu.addMenu( self.importMenu )

        addActions( self.fileMenu, ( None, self.exitAct ) )

        self.editMenu = self.menuBar().addMenu( _( '&Edit' ) )

        addActions( self.editMenu, ( self.cutAct,
                                   self.copyAct,
                                   self.pasteAct,
                                   self.sessionRefreshAct ) )
        # TODO: add refresh action
        self.viewMenu = self.menuBar().addMenu( _( 'View' ) )
        gotoMenu = self.viewMenu.addMenu( _( 'Go To' ) )
        addActions( gotoMenu, ( self.viewFirstAct,
                              self.viewPreviousAct,
                              self.viewNextAct,
                              self.viewLastAct ) )

        self.windowMenu = self.menuBar().addMenu( _( '&Window' ) )
        self.connect( self.windowMenu, QtCore.SIGNAL( 'aboutToShow()' ),
                     self.updateWindowMenu )

        self.menuBar().addSeparator()

        self.helpMenu = self.menuBar().addMenu( _( '&Help' ) )
        addActions( self.helpMenu, ( self.helpAct, self.aboutAct) )

    def updateMenus( self ):
        hasMdiChild = ( self.activeMdiChild() is not None )
        self.saveAct.setEnabled( hasMdiChild )
        self.pasteAct.setEnabled( hasMdiChild )
        self.closeAct.setEnabled( hasMdiChild )

        self.closeAllAct.setEnabled( hasMdiChild )
        self.cascadeAct.setEnabled( hasMdiChild )

        self.pageSetupAct.setEnabled( hasMdiChild )
        self.previewAct.setEnabled( hasMdiChild )
        self.printAct.setEnabled( hasMdiChild )

        self.newAct.setEnabled( hasMdiChild )
        self.deleteAct.setEnabled( hasMdiChild )
        self.viewFirstAct.setEnabled( hasMdiChild )
        self.viewPreviousAct.setEnabled( hasMdiChild )
        self.viewNextAct.setEnabled( hasMdiChild )
        self.viewLastAct.setEnabled( hasMdiChild )

        self.exportToWordAct.setEnabled( hasMdiChild )
        self.exportToExcelAct.setEnabled( hasMdiChild )
        self.exportToMailAct.setEnabled( hasMdiChild )

        self.importFromFileAct.setEnabled( hasMdiChild )

        self.separatorAct.setVisible( hasMdiChild )

        # TODO: selecting text in views for copy/cut/paste
        #hasSelection = (self.activeMdiChild() is not None and
        #                self.activeMdiChild().textCursor().hasSelection())
        hasSelection = False
        self.cutAct.setEnabled( hasSelection )
        self.copyAct.setEnabled( hasSelection )

    def updateWindowMenu( self ):
        self.windowMenu.clear()
        self.windowMenu.addAction( self.closeAllAct )
        self.windowMenu.addAction( self.cascadeAct )
        self.windowMenu.addAction( self.separatorAct )

        windows = self.workspace.subWindowList()

        self.separatorAct.setVisible( len( windows ) != 0 )

        i = 0

        for child in windows:
            if i < 9:
                text = self.tr( '&%1 %2' ).arg( i + 1 ).arg( child.windowTitle() )
            else:
                text = self.tr( '%1 %2' ).arg( i + 1 ).arg( child.windowTitle() )

            i += 1

            action = self.windowMenu.addAction( text )
            action.setCheckable( True )
            action.setChecked( child == self.activeMdiChild() )

            def create_window_activator( window ):

                def activate_window():
                    self.workspace.setActiveSubWindow( window )

                return activate_window

            self.connect( action, QtCore.SIGNAL( 'triggered()' ), create_window_activator( child ) )

    # Toolbars

    def createToolBars( self ):
        self.viewToolBar = self.addToolBar( _( 'View' ) )
        self.viewToolBar.setObjectName( 'ViewToolBar' )
        self.viewToolBar.setMovable( False )
        self.viewToolBar.setFloatable( False )
        addActions( self.viewToolBar, ( self.newAct,
                                      self.deleteAct,
                                      self.viewFirstAct,
                                      self.viewPreviousAct,
                                      self.viewNextAct,
                                      self.viewLastAct ) )

        self.editToolBar = self.addToolBar( _( 'Edit' ) )
        self.editToolBar.setObjectName( 'EditToolBar' )
        self.editToolBar.setMovable( False )
        self.editToolBar.setFloatable( False )
        addActions( self.editToolBar, ( self.cutAct,
                                      self.copyAct,
                                      self.pasteAct ) )

        self.exportToolBar = self.addToolBar( _( 'Export' ) )
        self.exportToolBar.setObjectName( 'ExportToolBar' )
        self.exportToolBar.setMovable( False )
        self.exportToolBar.setFloatable( False )
        addActions( self.exportToolBar, ( self.exportToExcelAct,
                                        self.exportToWordAct,
                                        self.exportToMailAct, ) )

        self.printToolBar = self.addToolBar( _( 'Print' ) )
        self.printToolBar.setObjectName( 'PrintToolBar' )
        self.printToolBar.setMovable( False )
        self.printToolBar.setFloatable( False )
        addActions( self.printToolBar, ( self.printAct, self.previewAct ) )

        self.helpToolBar = self.addToolBar( _( 'Help' ) )
        self.helpToolBar.setObjectName( 'HelpToolBar' )
        self.helpToolBar.setMovable( False )
        self.helpToolBar.setFloatable( False )
        addActions( self.helpToolBar, (self.helpAct, ) )

        if self.app_actions:
            self.applicationToolBar = self.addToolBar( _( 'Application' ) )
            self.applicationToolBar.setObjectName( 'ApplicationToolBar' )
            self.applicationToolBar.setMovable( False )
            self.applicationToolBar.setFloatable( False )
            addActions( self.applicationToolBar, self.app_actions )

    # Navigation Pane

    def createNavigationPane( self ):
        self.navpane = NavigationPane( self.app_admin, parent = self )
        self.addDockWidget( Qt.LeftDockWidgetArea, self.navpane )

        self.connect( self.navpane.treewidget,
                     QtCore.SIGNAL( 'itemClicked(QTreeWidgetItem *, int)' ),
                     self.createMdiChild )

    # Interface for child windows

    def createMdiChild( self, item ):
        index = self.navpane.treewidget.indexFromItem( item )
        section_item = self.navpane.items[index.row()]
        child = section_item.get_action().run( self.workspace )
        assert child != None
        self.connect( child, QtCore.SIGNAL( "copyAvailable(bool)" ),
                      self.cutAct.setEnabled )
        self.connect( child, QtCore.SIGNAL( "copyAvailable(bool)" ),
                      self.copyAct.setEnabled )
        subwindow = self.workspace.addSubWindow( child )
        subwindow.showMaximized()

    def activeMdiChild( self ):
        return self.workspace.activeSubWindow()

    # Statusbar

    def createStatusBar( self ):
        from controls.statusbar import StatusBar
        statusbar = StatusBar( self )
        self.setStatusBar( statusbar )
        statusbar.showMessage( _( 'Ready' ), 5000 )

    # Events (re)implementations

    def closeEvent( self, event ):
        self.workspace.closeAllSubWindows()
        if self.activeMdiChild():
            event.ignore()
        else:
            self.writeSettings()
            event.accept()
