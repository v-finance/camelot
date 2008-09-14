"""This module provides a singleton workspace that can be used by views
and widget to create new windows or raise existing ones"""

from PyQt4 import QtGui
import logging

logger = logging.getLogger('camelot.view.workspace')
logger.setLevel(logging.DEBUG)

def key_from_entity(entity, primary_key):
  return ('entity', entity, primary_key)

def key_from_query(entity, query):
  return ('query', entity, unicode(query()))

class DesktopWorkspace(QtGui.QWorkspace):
  def __init__(self, *args):
    QtGui.QWorkspace.__init__(self, *args)
    self._keys = dict()
    
  def addWindow(self, key, widget, *args):
    """Add a widget as a window to the workspace, each window
    should have a key that can be used to search for a window
    in the workspace.
    
    this method is a modification of QWorkspace.addWindow
    """
    parent = self.parent()
    width = int(parent.width() / 2)
    height = int(parent.height() / 2)
    widget.resize(width, height)    
    window = QtGui.QWorkspace.addWindow(self, widget, *args)
    self._keys[key] = window
    logger.debug(u'added window with key : %s'%unicode(key))
    return window

_workspace_ = []
        
def construct_workspace(*args, **kwargs):
  _workspace_.append(DesktopWorkspace(*args))
  return _workspace_[0]
  
def get_workspace():
  return _workspace_[0]