"""This module provides a singleton workspace that can be used by views
and widget to create new windows or raise existing ones"""

from PyQt4 import QtGui, QtCore

import logging

from camelot.view.model_thread import gui_function

logger = logging.getLogger('camelot.view.workspace')

class DesktopWorkspace(QtGui.QMdiArea):
  
    @gui_function
    def __init__(self, *args):
        QtGui.QMdiArea.__init__(self, *args)
        self.setOption(QtGui.QMdiArea.DontMaximizeSubWindowOnActivation)
        self.setBackground(QtGui.QBrush(QtGui.QColor('white')))
        self.setActivationOrder(QtGui.QMdiArea.ActivationHistoryOrder)
    
    @gui_function
    def addSubWindow(self, widget, *args):
        from camelot.view.controls.view import AbstractView
        subwindow = QtGui.QMdiArea.addSubWindow(self, widget, *args)
        if hasattr(widget, 'closeAfterValidation'):
            subwindow.connect(widget, widget.closeAfterValidation, subwindow, QtCore.SLOT("close()"))
            
        def create_set_window_title(subwindow):
          
            def set_window_title(new_title):
                subwindow.setWindowTitle(new_title)
                
            return set_window_title
            
        self.connect(widget, AbstractView.title_changed_signal, create_set_window_title(subwindow))
        return subwindow
    
class NoDesktopWorkspace(QtCore.QObject):
    def __init__(self):
        QtCore.QObject.__init__(self)
        self._windowlist = []
    
    @gui_function
    def addSubWindow(self, widget, *args):
        self.widget = widget
        self.widget.setParent(None)
        self.widget.show()
        self._windowlist.append(self.widget)
        self.connect(widget, QtCore.SIGNAL('WidgetClosed()'), self.removeWidgetFromWorkspace)
        
    @gui_function
    def subWindowList(self):
        return self._windowlist
      
    @gui_function
    def removeWidgetFromWorkspace(self):
        self._windowlist.remove(self.widget)
        
_workspace_ = []
        
@gui_function
def construct_workspace(*args, **kwargs):
    _workspace_.append(DesktopWorkspace())
    return _workspace_[0]
    
@gui_function
def construct_no_desktop_workspace(*args, **kwargs):
    _workspace_.append(NoDesktopWorkspace())
    return _workspace_[0]
  
@gui_function
def get_workspace():
    return _workspace_[0]
