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

"""left navigation pane"""

import os
import sys
import logging

logger = logging.getLogger('camelot.view.controls.navpane')

from PyQt4.QtCore import Qt
from PyQt4 import QtGui, QtCore

import settings
from camelot.view.model_thread import get_model_thread
from camelot.action import addActions, createAction
from camelot.view.controls.modeltree import ModelItem, ModelTree
from appscheme import scheme, defaultUI

QT_MAJOR_VERSION = float('.'.join(str(QtCore.QT_VERSION_STR).split('.')[0:2]))

_ = lambda x:x


class PaneCaption(QtGui.QLabel):
  """Navigation pane Caption"""
  def __init__(self, 
               text,
               textbold=True,
               textindent=3,
               width=160,
               height=32,
               objectname='PaneCaption',
               parent=None):

    super(PaneCaption, self).__init__(parent)

    self.setText(text)

    if textbold:
      self.textbold()

    font = self.font()
    font.setPointSize(font.pointSize() + 2)
    self.setFont(font)
    
    self.setIndent(textindent)

    self.setObjectName(objectname)

    style = """
    QLabel#PaneCaption {
      margin: 3px 0 0 3px;
      border: 1px solid %s;
      color: %s;
      background-color: %s;
    }
    """ % (scheme.bordercolor(),
           scheme.captiontextcolor(),
           scheme.captionbackground())

    self.setStyleSheet(style);
    self.setFixedHeight(height)
    self.resize(width, height)

  def textbold(self):
    font = self.font()
    font.setBold(True)
    font.setPointSize(font.pointSize() + 1)
    self.setFont(font)


class PaneButton(QtGui.QWidget):
  """Custom made navigation pane pushbutton"""
  INDEX = 0  # Keep track of the buttons

  def __init__(self,
               text,
               buttonicon='',
               textbold=True,
               textleft=True,
               width=160,
               height=32,
               objectname='PaneButton',
               parent=None):

    super(PaneButton, self).__init__(parent)

    if textleft:
      option = QtGui.QBoxLayout.LeftToRight 
    else:
      option = QtGui.QBoxLayout.RightToLeft
    self.layout = QtGui.QBoxLayout(option)
    self.layout.setSpacing(0)
    self.layout.setContentsMargins(3,0,0,0)

    if buttonicon:
      self.icon = QtGui.QLabel()
      self.icon.setPixmap(QtGui.QPixmap(buttonicon))
      self.layout.addWidget(self.icon)
    
    self.label = QtGui.QLabel(text)
    
    self.layout.addWidget(self.label, 2)
    
    self.setLayout(self.layout)

    if textbold:
      self.textbold()

    self.setObjectName(objectname)

    self.stylenormal = """
    QWidget#PaneButton * {
      margin: 0;
      padding-left: 3px;
      color : %s;
      border-color : %s;
      background-color : %s;
    }
    """ % (scheme.textcolor(),
           scheme.bordercolor(),
           scheme.normalbackground())
    
    self.stylehovered = """
    QWidget#PaneButton * {
      margin: 0;
      padding-left: 3px;
      color : %s;
      background-color : %s;
    }
    """ % (scheme.textcolor(),
           scheme.hoveredbackground())

    self.styleselected = """
    QWidget#PaneButton * {
      margin: 0;
      padding-left: 3px;
      color : %s;
      background-color : %s;
    }
    """ % (scheme.selectedcolor(),
           scheme.selectedbackground())

    self.styleselectedover = """
    QWidget#PaneButton * {
      margin: 0;
      padding-left: 3px;
      color : %s;
      background-color : %s;
    }
    """ % (scheme.selectedcolor(),
           scheme.selectedbackground(inverted=True))

    self.setStyleSheet(self.stylenormal)
    self.setFixedHeight(height)
    self.resize(width, height)
    self.selected = False
    self.index = PaneButton.INDEX
    PaneButton.INDEX += 1

  def textbold(self):
    font = self.label.font()
    font.setBold(True)
    self.label.setFont(font)

  def enterEvent(self, event):
    if self.selected:
      self.setStyleSheet(self.styleselectedover)
    else:
      self.setStyleSheet(self.stylehovered)

  def leaveEvent(self, event):
    if self.selected:
      self.setStyleSheet(self.styleselected)
    else:
      self.setStyleSheet(self.stylenormal)

  def mousePressEvent(self, event):
    if self.selected:
      return
    else:
      self.selected = True
      self.setStyleSheet(self.styleselectedover)
      # Python shortcut SIGNAL, any object can be passed
      self.emit(QtCore.SIGNAL('indexselected'),
                (self.index, self.label.text()))


class NavigationPane(QtGui.QDockWidget):
  """ms office-like navigation pane in Qt"""
  
  def __init__(self, app_admin, objectname='NavigationPane', parent=None):
    super(NavigationPane, self).__init__(parent)
    self.app_admin = app_admin
    self.sections = app_admin.getSections() 
    buttons = [PaneButton(label, icon) 
               for (section, (label, icon)) in self.sections]
    self.setFeatures(QtGui.QDockWidget.NoDockWidgetFeatures)

    self.setcontent(buttons)
    self.parent = parent

    self.currentbutton = -1

    self.caption = PaneCaption('')
    self.setTitleBarWidget(self.caption)

    self.setObjectName(objectname)

    # Tried selecting QDockWidget but it's not working
    # so we must undo this margin in children stylesheets :)
    #style = 'margin: 0 0 0 3px;'
    #self.setStyleSheet(style)
    
  def setcontent(self, buttons):
    logger.debug('setting up pane content')
    self.content = QtGui.QWidget()
    self.content.setObjectName('NavPaneContent')

    style = """
    QWidget#NavPaneContent { 
      margin-left: 3px;
      background-color: %s;
    }
    """ % scheme.bordercolor()

    self.content.setStyleSheet(style) 

    self.mt = get_model_thread()
    # TODO: Should a separator be added between the tree
    #       and the buttons?
    #self.treewidget = PaneTree(self)
    header_labels = ['']
    self.treewidget = ModelTree(header_labels, self)
    self.treewidget.setObjectName('NavPaneTree')

    style = """
    QWidget#NavPaneTree { 
      margin-left: 3px;
      border: 1px solid %s;
    }
    """ % scheme.bordercolor()
  
    self.treewidget.setStyleSheet(style)

    # context menu
    self.treewidget.contextmenu = QtGui.QMenu(self)
    newWindowAct = createAction(parent=self,
                                text=_('Open in New Window'),
                                slot=self.popWindow,
                                shortcut='Ctrl+Enter')
    
    addActions(self.treewidget.contextmenu, (newWindowAct,))
    self.treewidget.setContextMenuPolicy(Qt.CustomContextMenu)
    self.connect(self.treewidget,
                 QtCore.SIGNAL('customContextMenuRequested(const QPoint &)'),
                 self.createContextMenu)

    layout = QtGui.QVBoxLayout()
    layout.setSpacing(1)
    layout.setContentsMargins(1,1,1,1)
    layout.addWidget(self.treewidget)

    if buttons:
      for b in buttons:
        layout.addWidget(b)
        self.connect(b, QtCore.SIGNAL('indexselected'), self.change_current)
      self.buttons = buttons

    self.content.setLayout(layout)
    self.setWidget(self.content)

  def set_models_in_tree(self, models):
    self.treewidget.clear()
    self.treewidget.clear_model_items()
    self.models = models

    if not models:
      return


    for model in models:
      logger.debug('loading model %s' % str(model[0]))
      item = ModelItem(self.treewidget, [model[0].getVerboseNamePlural()])
      self.treewidget.modelitems.append(item)

    self.treewidget.update()

  def change_current(self, (index, text)):
    logger.debug('set current to %s' % text)
    
    if self.currentbutton != -1:
      button = self.buttons[self.currentbutton]
      button.setStyleSheet(button.stylenormal)
      button.selected = False
    self.caption.setText(text)
    self.currentbutton = index
    
    def get_models_for_tree():
      """Return pairs of (Admin, query) classes for items in the tree"""
      section = self.sections[index][0] 
      return self.app_admin.getEntitiesAndQueriesInSection(section)
    
    self.mt.post(get_models_for_tree, 
                 lambda models:self.set_models_in_tree(models))

  def createContextMenu(self, point):
    logger.debug('creating context menu')
    item = self.treewidget.itemAt(point) 
    if item:
      #column = 0
      #flag = QtGui.QItemSelectionModel.SelectCurrent
      #self.treewidget.setCurrentItem(item, column, flag)
      self.treewidget.setCurrentItem(item)
      self.treewidget.contextmenu.popup(self.cursor().pos())
    
  def popWindow(self):
    """pops a model window in parent's workspace"""
    logger.debug('poping a window in parent')
    item = self.treewidget.currentItem()
    #column = 0
    #self.parent.createMdiChild(item, column)
    self.parent.createMdiChild(item)
