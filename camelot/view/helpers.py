#  ==================================================================================
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
#  ==================================================================================

"""
collection of helper functions 
"""

from PyQt4 import QtGui
from PyQt4 import QtCore
from PyQt4.QtCore import Qt

def createAction(parent,
                 text,
                 slot=None,
                 shortcut='', 
                 actionicon='',
                 tip='', 
                 checkable=False, 
                 signal='triggered()',
                 widgetaction=False):

  """ creates and returns a QAction object """

  action = QtGui.QWidgetAction(parent) if widgetaction \
                                       else QtGui.QAction(parent)
  action.setText(text)

  if actionicon:
    action.setIcon(QtGui.QIcon(actionicon))
  if shortcut: 
    action.setShortcut(shortcut)
  if tip:
    action.setToolTip(tip)
    action.setStatusTip(tip)
  if slot:
    parent.connect(action, QtCore.SIGNAL(signal), slot)
  if checkable:
    action.setCheckable(True)
  return action

def addActions(target, actions):
  """ 
    add action objects to menus, menubars, and toolbars
    if action is None, add a toolbar, however we must
    explicitly add separator actions in the case of 
    context menus.
  """
  for action in actions:
    if action is None:
      target.addSeparator()
    else:
      target.addAction(action)

def okToContinue(widget, func):
  """
    save unsaved changes before exiting the application
    function func is called
  """
  if widget.changed:
    reply = QtGui.QMessageBox.question(widget,
                  widget.tr('Unsaved Changes'),
                  widget.tr('Save unsaved changes?'),
                  QtGui.QMessageBox.Yes|
                  QtGui.QMessageBox.No|
                  QtGui.QMessageBox.Cancel)
    if reply == QtGui.QMessageBox.Cancel:
      return False
    elif reply == QtGui.QMessageBox.Yes:
      getattr(widget, func)()
    return True

