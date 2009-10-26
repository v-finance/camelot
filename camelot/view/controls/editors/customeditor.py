
from PyQt4.QtCore import Qt
from PyQt4 import QtGui, QtCore

import camelot.types
from camelot.core.constants import *
from camelot.view.proxy import ValueLoading
from camelot.core.utils import create_constant_function

editingFinished = QtCore.SIGNAL('editingFinished()')
 
class AbstractCustomEditor(object):
    """Helper class to be used to build custom editors.  This class provides
  functionallity to store and retrieve `ValueLoading` as an editor's value.
  """
    
    def __init__(self):
        self._value_loading = True
        
    def set_value(self, value):
        if value==ValueLoading:
            self._value_loading = True
            return None
        else:
            self._value_loading = False
            return value
            
    def get_value(self):
        if self._value_loading:
            return ValueLoading
        return None
      
      
    """
    Get the 'standard' height for a cell
    """
    def get_height(self):
      
        height = [QtGui.QLineEdit().sizeHint().height(),
               QtGui.QDateEdit().sizeHint().height(),
               QtGui.QDateTimeEdit().sizeHint().height(),
               QtGui.QSpinBox().sizeHint().height(),
               QtGui.QDateEdit().sizeHint().height(),
               QtGui.QComboBox().sizeHint().height()]
        
        finalHeight = max(height)
        
        return finalHeight
          
class CustomEditor(QtGui.QWidget, AbstractCustomEditor):
    """Base class for implementing custom editor widgets.  This class provides
  dual state functionality.  Each editor should have the posibility to have as
  its value `ValueLoading` specifying that no value has been set yet.
  """
    def __init__(self, parent):
        QtGui.QWidget.__init__(self, parent)
        AbstractCustomEditor.__init__(self)
