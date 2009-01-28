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

import settings
import os
import sys
import logging

logger = logging.getLogger('mainwindow')
logger.setLevel(logging.INFO)

#
# Dummy imports to fool the windows installer and force
# it to include the right packages
#
from sqlalchemy.databases import sqlite
import sqlite3

from PyQt4.QtCore import Qt
from PyQt4.QtTest import QTest
from PyQt4 import QtGui, QtCore

from camelot.view.art import TangoIcon
from camelot.view.helpers import createAction, addActions
from camelot.view.controls.navpane import PaneButton, NavigationPane
from camelot.view.controls.printer import Printer
from camelot.view.model_thread import get_model_thread, construct_model_thread
from camelot.view.response_handler import ResponseHandler
from camelot.view.remote_signals import construct_signal_handler

QT_MAJOR_VERSION = float('.'.join(str(QtCore.QT_VERSION_STR).split('.')[0:2]))

_ = lambda x: x


class MainWindow(QtGui.QMainWindow):
  """Main window GUI"""

  def __init__(self, app_admin, parent=None):
    from workspace import construct_workspace
    logger.debug('initializing main window')
    super(MainWindow, self).__init__(parent)

    self.app_admin = app_admin

    logger.debug('setting up workspace')
    self.workspace = construct_workspace(self)

    logger.debug('setting child windows dictionary')

    logger.debug('setting central widget to our workspace')
    self.setCentralWidget(self.workspace)

    self.connect(self.workspace, QtCore.SIGNAL('subWindowActivated(QMdiSubWindow *)'),
                 self.updateMenus)

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

    logger.debug('setting up printer object')
    self.printer = Printer()

    logger.debug('setting up window title')
    self.setWindowTitle(self.app_admin.getName())

    #QtCore.QTimer.singleShot(0, self.doInitialization)
    logger.debug('initialization complete')

  # Application settings

  def about(self):
    logger.debug('showing about message box')
    abtmsg = self.app_admin.getAbout()
    QtGui.QMessageBox.about(self, _('About'), _(abtmsg))
    logger.debug('about message closed')

  def readSettings(self):
    # TODO: improve settings reading
    settings = QtCore.QSettings()
    self.restoreGeometry(settings.value('geometry').toByteArray())
    # Don't restore state, since it messes up the toolbar if stuff was
    # added
    # self.restoreState(settings.value('state').toByteArray())

  def writeSettings(self):
    # TODO: improve settings saving
    logger.debug('writing application settings')
    settings = QtCore.QSettings()
    settings.setValue('geometry', QtCore.QVariant(self.saveGeometry()))
    settings.setValue('state', QtCore.QVariant(self.saveState()))
    logger.debug('settings written')

  def runAction(self, name, callable):
    progress = QtGui.QProgressDialog('Please wait', 'Run in background', 0, 0)
    progress.setWindowTitle(name)
    progress.show()
    mt = get_model_thread()
    
    def exception_in_action(e):
      progress.close()
      QtGui.QMessageBox.warning(self, 'Error while %s'%name, str(e))
      
    mt.post(callable, lambda *args:progress.close(), exception_in_action)
    
  # QAction objects creation methods
  def createActions(self):
    # TODO: change status tip
    self.saveAct = createAction(self,
                                _('&Save'),
                                self.save,
                                QtGui.QKeySequence.Save,
                                TangoIcon('document-save', 
                                          folder='actions').fullpath(),
                                _('Save'))

    temp = TangoIcon('document-properties', folder='actions').fullpath()
    self.pageSetupAct = createAction(self,
                                     _('Page Setup...'),
                                     self.pageSetup,
                                     actionicon=temp,
                                     tip=_('Page Setup...'))

    self.printAct = createAction(self,
                                 _('Print...'),
                                 self.printDoc,
                                 QtGui.QKeySequence.Print,
                                 TangoIcon('document-print',
                                           folder='actions').fullpath(),
                                 _('Print...'))

    temp = TangoIcon('document-print-preview', folder='actions').fullpath()
    self.previewAct = createAction(self,
                                   _('Print Preview'),
                                   self.previewDoc,
                                   actionicon=temp,
                                   tip=_('Print Preview'))

    self.exitAct = createAction(self,
                                _('E&xit'),
                                self.close,
                                tip=_('Exit the application'))

    tip = _("Cut the current selection's contents to the clipboard")
    self.cutAct = createAction(self,
                               _('Cu&t'),
                               self.cut,
                               QtGui.QKeySequence.Cut,
                               TangoIcon('edit-cut',
                                         folder='actions').fullpath(),
                               tip)

    tip = _("Copy the current selection's contents to the clipboard")
    self.copyAct = createAction(self,
                                _('&Copy'),
                                self.copy,
                                QtGui.QKeySequence.Copy,
                                TangoIcon('edit-copy',
                                          folder='actions').fullpath(),
                                tip)

    tip = _("Paste the clipboard's contents into the current selection")
    self.pasteAct = createAction(self,
                                 _('&Paste'),
                                 self.paste,
                                 QtGui.QKeySequence.Paste,
                                 TangoIcon('edit-paste',
                                           folder='actions').fullpath(),
                                 tip)

    self.closeAct = createAction(self,
                                 _('Cl&ose'),
                                 self.workspace.closeActiveSubWindow,
                                 shortcut = QtGui.QKeySequence.Close,
                                 tip=_('Close the active window'))

    self.closeAllAct = createAction(self,
                                    _('Close &All'),
                                    self.workspace.closeAllSubWindows,
                                    tip=_('Close all the windows'))

    self.cascadeAct = createAction(self,
                                   _('&Cascade windows'),
                                   self.workspace.cascadeSubWindows,
                                   tip=_('Arranges all the child windows '
                                         'in a cascade pattern.'))

    self.separatorAct = QtGui.QAction(self)
    self.separatorAct.setSeparator(True)

    self.aboutAct = createAction(self,
                                 _('&About'),
                                 self.about,
                                 tip=_("Show the application's About box"))

    self.newAct = createAction(self,
                               _('New'),
                               self.new,
                               QtGui.QKeySequence.New,
                               TangoIcon('document-new',
                                         folder='actions').fullpath(),
                               _('New'))

    self.deleteAct = createAction(self,
                                  _('Delete'),
                                  self.delete,
                                  QtGui.QKeySequence.Delete,
                                  TangoIcon('user-trash',
                                            folder='places').fullpath(),
                                  _('Delete'))

    self.viewFirstAct = createAction(self,
                                     _('First'),
                                     self.viewFirst,
                                     QtGui.QKeySequence.MoveToStartOfDocument,
                                     TangoIcon('go-first',
                                               folder='actions').fullpath(),
                                     _('First'))

    self.viewLastAct = createAction(self,
                                    _('Last'),
                                    self.viewLast,
                                    QtGui.QKeySequence.MoveToEndOfDocument,
                                    TangoIcon('go-last',
                                              folder='actions').fullpath(),
                                    _('Last'))

    self.viewNextAct = createAction(self,
                                    _('Next'),
                                    self.viewNext,
                                    QtGui.QKeySequence.MoveToNextPage,
                                    TangoIcon('go-next',
                                              folder='actions').fullpath(),
                                    _('Next'))

    self.viewPreviousAct = createAction(self,
                                        _('Previous'),
                                        self.viewPrevious,
                                        QtGui.QKeySequence.MoveToPreviousPage,
                                        TangoIcon('go-previous',
                                                  folder='actions').fullpath(),
                                        _('Previous'))

    if QT_MAJOR_VERSION > 4.3:
      self.viewFirstAct.setIconVisibleInMenu(False)
      self.viewLastAct.setIconVisibleInMenu(False)
      self.viewNextAct.setIconVisibleInMenu(False)
      self.viewPreviousAct.setIconVisibleInMenu(False)

    temp = TangoIcon('x-office-spreadsheet', folder='mimetypes').fullpath()
    self.exportToExcelAct = createAction(self,
                                         _('Export to MS Excel'),
                                         self.exportToExcel,
                                         actionicon=temp,
                                         tip=_('Export to MS Excel'))

    temp = TangoIcon('x-office-document', folder='mimetypes').fullpath()
    self.exportToWordAct = createAction(self,
                                        _('Export to MS Word'),
                                        self.exportToWord,
                                        actionicon=temp,
                                        tip=_('Export to MS Word'))

    temp = TangoIcon('mail-message-new', folder='actions').fullpath()
    self.exportToMailAct = createAction(self,
                                        _('Send by e-mail'),
                                        self.exportToMail,
                                        actionicon=temp,
                                        tip=_('Send by e-mail'))    
    
    self.app_actions = []
    for name, icon, callable in self.app_admin.getActions():
      
      def bind_callable(name, callable):
        return lambda:self.runAction(name, callable)
      
      self.app_actions.append(createAction(self,
                                           name,
                                           slot=bind_callable(name, callable), 
                                           actionicon=icon,
                                           tip=name))

  # QAction slots and methods implementations

  def save(self):
    pass

  def saveAs(self):
    pass

  def cut(self):
    pass

  def copy(self):
    pass

  def paste(self):
    pass

  def printDoc(self):
    active = self.activeMdiChild()
    self.printer.printView(active.widget(), self)

  def previewDoc(self):
    self.printer.preview(self.activeMdiChild().widget(), self)

  def new(self):
    self.activeMdiChild().widget().newRow()

  def delete(self):
    self.activeMdiChild().widget().deleteSelectedRows()

  def pageSetup(self):
    pass

  def viewFirst(self):
    """selects view's first row"""
    active = self.activeMdiChild()
    active.widget().viewFirst()

  def viewLast(self):
    """selects view's last row"""
    active = self.activeMdiChild()
    active.widget().viewLast()

  def viewNext(self):
    """selects view's next row"""
    active = self.activeMdiChild()
    active.widget().viewNext()

  def viewPrevious(self):
    """selects view's previous row"""
    active = self.activeMdiChild()
    active.widget().viewPrevious()

  def exportToExcel(self):
    """creates an excel file from the view"""

    mt = get_model_thread()

    def export():
      import os
      import tempfile
      from export.excel import ExcelExport
      title = self.activeMdiChild().widget().getTitle()
      columns = self.activeMdiChild().widget().getColumns()
      data = [d for d in self.activeMdiChild().widget().getData()]
      objExcel = ExcelExport()
      xls_fd, xls_fn = tempfile.mkstemp(suffix='.xls')
      objExcel.exportToFile(xls_fn, title, columns, data)

      try:
        import pythoncom
        import win32com.client
        pythoncom.CoInitialize()
        excel_app = win32com.client.Dispatch("Excel.Application")
      except Exception, e:
        """We're probably not running windows, so try gnumeric"""
        logger.warning('Unable to launch excel', exc_info=e)
        os.system('gnumeric "%s"'%xls_fn)
        return

      excel_app.Visible = True
      excel_app.Workbooks.Open(xls_fn)

    mt.post(export)

  def exportToWord(self):
    """Use windows COM to export the active child window to MS word,
    by using its toHtml function"""

    mt = get_model_thread()

    def export():
      from export.word import open_html_in_word
      html = self.activeMdiChild().widget().toHtml()
      open_html_in_word(html)

    mt.post(export)

  def exportToMail(self):
    
    mt = get_model_thread()
    
    def export():
      from export.outlook import open_html_in_outlook
      html = self.activeMdiChild().widget().toHtml()
      open_html_in_outlook(html)

    mt.post(export)      
  # Menus

  def createMenus(self):
    self.fileMenu = self.menuBar().addMenu(_('&File'))
    addActions(self.fileMenu, (self.closeAct,
                               None, self.saveAct,
                               None, self.pageSetupAct,
                               self.previewAct,
                               self.printAct, None))

    self.exportMenu = QtGui.QMenu(_('Export To'))
    addActions(self.exportMenu, (self.exportToExcelAct,
                                 self.exportToWordAct,
                                 self.exportToMailAct,
                                 ))
    self.fileMenu.addMenu(self.exportMenu)

    addActions(self.fileMenu, (None, self.exitAct))

    self.editMenu = self.menuBar().addMenu(_('&Edit'))

    addActions(self.editMenu, (self.cutAct,
                               self.copyAct,
                               self.pasteAct))
    # TODO: add refresh action
    self.viewMenu = self.menuBar().addMenu(_('View'))
    gotoMenu = self.viewMenu.addMenu(_('Go To'))
    addActions(gotoMenu, (self.viewFirstAct,
                          self.viewPreviousAct,
                          self.viewNextAct,
                          self.viewLastAct))

    self.windowMenu = self.menuBar().addMenu(_('&Window'))
    self.connect(self.windowMenu, QtCore.SIGNAL('aboutToShow()'),
                 self.updateWindowMenu)

    self.menuBar().addSeparator()

    self.helpMenu = self.menuBar().addMenu(_('&Help'))
    addActions(self.helpMenu, (self.aboutAct, ))

  def updateMenus(self):
    hasMdiChild = (self.activeMdiChild() is not None)
    self.saveAct.setEnabled(hasMdiChild)
    self.pasteAct.setEnabled(hasMdiChild)
    self.closeAct.setEnabled(hasMdiChild)

    self.closeAllAct.setEnabled(hasMdiChild)
    self.cascadeAct.setEnabled(hasMdiChild)

    self.pageSetupAct.setEnabled(hasMdiChild)
    self.previewAct.setEnabled(hasMdiChild)
    self.printAct.setEnabled(hasMdiChild)

    self.newAct.setEnabled(hasMdiChild)
    self.deleteAct.setEnabled(hasMdiChild)
    self.viewFirstAct.setEnabled(hasMdiChild)
    self.viewPreviousAct.setEnabled(hasMdiChild)
    self.viewNextAct.setEnabled(hasMdiChild)
    self.viewLastAct.setEnabled(hasMdiChild)

    self.exportToWordAct.setEnabled(hasMdiChild)
    self.exportToExcelAct.setEnabled(hasMdiChild)
    self.exportToMailAct.setEnabled(hasMdiChild)

    self.separatorAct.setVisible(hasMdiChild)

    # TODO: selecting text in views for copy/cut/paste
    #hasSelection = (self.activeMdiChild() is not None and
    #                self.activeMdiChild().textCursor().hasSelection())
    hasSelection = False
    self.cutAct.setEnabled(hasSelection)
    self.copyAct.setEnabled(hasSelection)

  def updateWindowMenu(self):
    self.windowMenu.clear()
    self.windowMenu.addAction(self.closeAllAct)
    self.windowMenu.addAction(self.cascadeAct)
    self.windowMenu.addAction(self.separatorAct)

    windows = self.workspace.subWindowList()

    self.separatorAct.setVisible(len(windows) != 0)

    i = 0

    for child in windows:
      if i < 9:
        text = self.tr('&%1 %2').arg(i + 1).arg(child.windowTitle())
      else:
        text = self.tr('%1 %2').arg(i + 1).arg(child.windowTitle())

      i += 1

      action = self.windowMenu.addAction(text)
      action.setCheckable(True)
      action.setChecked(child == self.activeMdiChild())
      
      def create_window_activator(window):
        
        def activate_window():
          self.workspace.setActiveSubWindow(window)
          
        return activate_window
      
      self.connect(action, QtCore.SIGNAL('triggered()'), create_window_activator(child))

  # Toolbars

  def createToolBars(self):
    self.printToolBar = self.addToolBar(_('Print'))
    self.printToolBar.setObjectName('PrintToolBar')
    self.printToolBar.setMovable(False)
    self.printToolBar.setFloatable(False)
    addActions(self.printToolBar, (self.printAct, self.previewAct))

    self.editToolBar = self.addToolBar(_('Edit'))
    self.editToolBar.setObjectName('EditToolBar')
    self.editToolBar.setMovable(False)
    self.editToolBar.setFloatable(False)
    addActions(self.editToolBar, (self.cutAct,
                                  self.copyAct,
                                  self.pasteAct))

    self.viewToolBar = self.addToolBar(_('View'))
    self.viewToolBar.setObjectName('ViewToolBar')
    self.viewToolBar.setMovable(False)
    self.viewToolBar.setFloatable(False)
    addActions(self.viewToolBar, (self.newAct,
                                  self.deleteAct,
                                  self.viewFirstAct,
                                  self.viewPreviousAct,
                                  self.viewNextAct,
                                  self.viewLastAct))

    self.exportToolBar = self.addToolBar(_('Export'))
    self.exportToolBar.setObjectName('ExportToolBar')
    self.exportToolBar.setMovable(False)
    self.exportToolBar.setFloatable(False)
    addActions(self.exportToolBar, (self.exportToExcelAct,
                                    self.exportToWordAct,
                                    self.exportToMailAct,))
    
    
    if self.app_actions:
      self.applicationToolBar = self.addToolBar(_('Application'))
      self.applicationToolBar.setObjectName('ApplicationToolBar')
      self.applicationToolBar.setMovable(False)
      self.applicationToolBar.setFloatable(False)
      addActions(self.exportToolBar, self.app_actions)
      
  # Navigation Pane

  def createNavigationPane(self):
    self.navpane = NavigationPane(self.app_admin, parent=self)
    self.addDockWidget(Qt.LeftDockWidgetArea, self.navpane)

    self.connect(self.navpane.treewidget,
                 QtCore.SIGNAL('itemClicked(QTreeWidgetItem *, int)'),
                 self.createMdiChild)

    # use QTest to auto select first button :)
    firstbutton = self.navpane.buttons[0]
    QTest.mousePress(firstbutton, Qt.LeftButton)

  # Interface for child windows

  def createMdiChild(self, item):
    index = self.navpane.treewidget.indexFromItem(item)
    model = self.navpane.models[index.row()]
    logger.debug('creating model %s' % str(model[0]))

    child = model[0].createTableView(model[1], parent=self)
    self.workspace.addSubWindow(child)

    self.connect(child, QtCore.SIGNAL("copyAvailable(bool)"),
           self.cutAct.setEnabled)
    self.connect(child, QtCore.SIGNAL("copyAvailable(bool)"),
           self.copyAct.setEnabled)
    child.showMaximized()

  def activeMdiChild(self):
    return self.workspace.activeSubWindow()

  # Statusbar

  def createStatusBar(self):
    self.status = self.statusBar()
    self.status.showMessage(_('Ready'), 5000)

  # Events (re)implementations

  def closeEvent(self, event):
    self.workspace.closeAllSubWindows()
    if self.activeMdiChild():
      event.ignore()
    else:
      self.writeSettings()
      event.accept()
