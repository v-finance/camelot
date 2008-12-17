"""This module provides a singleton workspace that can be used by views
and widget to create new windows or raise existing ones"""

from PyQt4 import QtGui
import logging

logger = logging.getLogger('camelot.view.workspace')

class DesktopWorkspace(QtGui.QWorkspace):
  def __init__(self, *args):
    QtGui.QWorkspace.__init__(self, *args)

_workspace_ = []
        
def construct_workspace(*args, **kwargs):
  _workspace_.append(DesktopWorkspace(*args))
  return _workspace_[0]
  
def get_workspace():
  return _workspace_[0]
