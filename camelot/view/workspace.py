"""This module provides a singleton workspace that can be used by views
and widget to create new windows or raise existing ones"""

from PyQt4 import QtGui
from PyQt4 import Qt

import logging

logger = logging.getLogger('camelot.view.workspace')

class DesktopWorkspace(QtGui.QMdiArea):
  def __init__(self, *args):
    QtGui.QMdiArea.__init__(self, *args)
    self.setOption(QtGui.QMdiArea.DontMaximizeSubWindowOnActivation)
    self.setBackground(QtGui.QBrush(QtGui.QColor('white')))
    self.setActivationOrder(QtGui.QMdiArea.ActivationHistoryOrder)

_workspace_ = []
        
def construct_workspace(*args, **kwargs):
  _workspace_.append(DesktopWorkspace(*args))
  return _workspace_[0]
  
def get_workspace():
  return _workspace_[0]
