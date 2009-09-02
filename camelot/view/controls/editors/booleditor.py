#
#from customeditor import *
#
#class BoolEditor(QtGui.QCheckBox, AbstractCustomEditor):
#  
#  def __init__(self, parent, editable=True, **kwargs):
#    QtGui.QCheckBox.__init__(self, parent)
#    AbstractCustomEditor.__init__(self)
#    self.setEnabled(editable)
#    
#  def set_value(self, value):
#    print 'VALUE : ', value
#    value = AbstractCustomEditor.set_value(self, value)
#    if value:
#      self.setCheckState(Qt.Checked)
#    else:
#      self.setCheckState(Qt.Unchecked)
#    
#    
#    print 'ISCHECKED? : ', self.isChecked()
#      
#  def get_value(self):
#    return AbstractCustomEditor.get_value(self) or self.isChecked()
#  
#  
  
  
  
from customeditor import *
from PyQt4 import QtGui

class BoolEditor(CustomEditor):
  """Widget for editing a boolean field"""

  def __init__(self,
               parent=None,
               minimum=camelot_minint,
               maximum=camelot_maxint,
               editable=True,
               **kwargs):
    CustomEditor.__init__(self, parent)
    self.checkBox = QtGui.QCheckBox()
    self.checkBox.setEnabled(editable)

    layout = QtGui.QHBoxLayout()
    layout.setMargin(0)
    layout.setSpacing(0)
    layout.addWidget(self.checkBox)
    self.setFocusProxy(self.checkBox)
    self.setLayout(layout)

  def set_value(self, value):
    value = CustomEditor.set_value(self, value)
    if value:
      self.checkBox.setCheckState(Qt.Checked)
    else:
      self.checkBox.setCheckState(Qt.Unchecked)

  def get_value(self):
    value = self.checkBox.isChecked()
    return CustomEditor.get_value(self) or value

  def editingFinished(self, value=None):
    if value == None:
      value = self.checkBox.isChecked()
    self.emit(QtCore.SIGNAL('editingFinished()'), value)
    
    
  
  
  def set_enabled(self, editable=True):
    value = self.get_value()
    self.checkBox.setDisabled(not editable)
    self.set_value(value)
  
  def sizeHint(self):
    size = QtGui.QComboBox().sizeHint()
    return size
