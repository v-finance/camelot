'''
Created on May 22, 2010

@author: tw55413
'''
from PyQt4 import QtGui, QtCore

from camelot.view.model_thread import post

class ActionWidget(QtGui.QPushButton):
    """A button that can be pushed to trigger an action"""
    
    def __init__(self, action, entity_getter, parent):
        super(QtGui.QPushButton, self).__init__( unicode(action.get_name() ) )
        if action.get_icon():
            self.setIcon( action.get_icon().getQIcon() )
        self._action = action
        self._entity_getter = entity_getter
        self.connect( self, QtCore.SIGNAL( 'clicked()' ), self.triggered )
        
    def triggered(self):
        """This slot is triggered when the user triggers the action."""
        self._action.run( self._entity_getter )
        
    def changed(self):
        """This slot is triggered when the entity displayed has changed, which means
        the state of the widget needs to be updated"""
        post( self._is_enabled, self._set_enabled )
        
    def _set_enabled(self, enabled):
        self.setEnabled( enabled )

    def _is_enabled(self):
        obj = self._entity_getter()
        return self._action.enabled(obj)