
from customeditor import *

class ChoicesEditor(QtGui.QComboBox, AbstractCustomEditor):

  def __init__(self, parent=None, editable=True, **kwargs):
    from camelot.view.model_thread import get_model_thread
    QtGui.QComboBox.__init__(self, parent)
    AbstractCustomEditor.__init__(self)
    self.setEnabled(editable)
    
  def qvariantToPython(self, variant):
    if variant.canConvert(QtCore.QVariant.String):
      return unicode(variant.toString())
    else:
      return variant.toPyObject()
    
  def set_choices(self, choices):
    allready_in_combobox = dict((self.qvariantToPython(self.itemData(i)),i)
                                 for i in range(self.count()))
    for i,(value,name) in enumerate(choices):
      if value not in allready_in_combobox:
        self.insertItem(i, unicode(name), QtCore.QVariant(value))
      else:
        # the editor data might allready have been set, but its name is
        # still ..., therefore we set the name now correct
        self.setItemText(i, unicode(name))
    
  def set_value(self, value):
    value = AbstractCustomEditor.set_value(self, value)
    if value!=None:
      for i in range(self.count()):
        if value == self.qvariantToPython(self.itemData(i)):
          self.setCurrentIndex(i)
          return
      # it might happen, that when we set the editor data, the setChoices 
      # method has not happened yet, therefore, we temporary set ... in the
      # text while setting the correct data to the editor
      self.insertItem(self.count(), '...', QtCore.QVariant(value))
      self.setCurrentIndex(self.count()-1)
    
  def get_value(self):
    current_index = self.currentIndex()
    if current_index>=0:
      value = self.qvariantToPython(self.itemData(self.currentIndex()))
    else:
      value = None
    return AbstractCustomEditor.get_value(self) or value
