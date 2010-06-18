from PyQt4 import QtGui, QtCore

from customeditor import AbstractCustomEditor
import sip

class ChoicesEditor(QtGui.QComboBox, AbstractCustomEditor):
    """A ComboBox aka Drop Down box that can be assigned a list of 
    keys and values"""

    def __init__(self, parent=None, editable=True, **kwargs):
        QtGui.QComboBox.__init__(self, parent)
        AbstractCustomEditor.__init__(self)
        self.setEnabled(editable)
        
    def set_choices(self, choices):
        """
    :param choices: a list of (value,name) tuples.  name will be displayed in the combobox,
    while value will be used within get_value and set_value.  This method changes the items
    in the combo box while preserving the current value, even if this value is not in the
    new list of choices.
        """
        if not sip.isdeleted(self):
            current_index = self.currentIndex()
            if current_index >= 0:
                current_name = unicode(self.itemText(current_index))
            current_value = self.get_value()
            current_value_available = False
            for i in range(self.count(), 0, -1):
                self.removeItem(i-1)
            for i, (value, name) in enumerate(choices):
                self.insertItem(i, unicode(name), QtCore.QVariant(value))
                if value == current_value:
                    current_value_available = True
            if not current_value_available and current_index > 0:
                self.insertItem(i+1, current_name, QtCore.QVariant(current_value))
            self.set_value(current_value)
        
    def set_enabled(self, editable=True):
        self.setEnabled(editable)
              
    def get_choices(self):
        """
    :rtype: a list of (value,name) tuples
    """
        from camelot.core.utils import variant_to_pyobject
        return [(variant_to_pyobject(self.itemData(i)), 
                 unicode(self.itemText(i))) for i in range(self.count())]
        
    def set_value(self, value):
        """Set the current value of the combobox where value, the name displayed
        is the one that matches the value in the list set with set_choices"""
        if not sip.isdeleted(self):
            from camelot.core.utils import variant_to_pyobject
            value = AbstractCustomEditor.set_value(self, value)
            if value not in (None, NotImplemented):
                for i in range(self.count()):
                    if value == variant_to_pyobject(self.itemData(i)):
                        self.setCurrentIndex(i)
                        return
                # it might happen, that when we set the editor data, the set_choices 
                # method has not happened yet, therefore, we temporary set ... in the
                # text while setting the correct data to the editor
                self.insertItem(self.count(), '...', QtCore.QVariant(value))
                self.setCurrentIndex(self.count()-1)
            
    def get_value(self):
        """Get the current value of the combobox"""
        if not sip.isdeleted(self):
            from camelot.core.utils import variant_to_pyobject
            current_index = self.currentIndex()
            if current_index >= 0:
                value = variant_to_pyobject(self.itemData(self.currentIndex()))
            else:
                value = None
            return AbstractCustomEditor.get_value(self) or value
