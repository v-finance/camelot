from PyQt4 import QtGui, QtCore

from customeditor import AbstractCustomEditor
import sip

class ChoicesEditor(QtGui.QComboBox, AbstractCustomEditor):

    def __init__(self, parent=None, editable=True, **kwargs):
        QtGui.QComboBox.__init__(self, parent)
        AbstractCustomEditor.__init__(self)
        self.setEnabled(editable)
        
    def set_choices(self, choices):
        """
    :param choices: a list of (value,name) tuples.  name will be displayed in the combobox,
    while value will be used within get_value and set_value
        """
        if not sip.isdeleted(self):
            allready_in_combobox = dict(self.get_choices())
            items_to_remove = []
            for i,(value,name) in enumerate(choices):
                if value not in allready_in_combobox:
                    self.insertItem(i, unicode(name), QtCore.QVariant(value))
                else:
                    # the editor data might allready have been set, but its name is
                    # still ..., therefore we set the name now correct
                    self.setItemText(i, unicode(name))
            current_value = self.get_value()
            new_choices = dict(choices)
            for i,(value,name) in enumerate(self.get_choices()):
                if (value not in new_choices) and (value!=current_value):
                    items_to_remove.append(i)
            removed_items = 0
            for i in items_to_remove:
                self.removeItem(i-removed_items)
                removed_items += 1
        
        
        
    def set_enabled(self, editable=True):
        self.setEnabled(editable)
    
    
    
              
    def get_choices(self):
        """
    :rtype: a list of (value,name) tuples
    """
        from camelot.core.utils import variant_to_pyobject
        return [(variant_to_pyobject(self.itemData(i)),unicode(self.itemText(i))) for i in range(self.count())]
        
    def set_value(self, value):
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
        if not sip.isdeleted(self):
            from camelot.core.utils import variant_to_pyobject
            current_index = self.currentIndex()
            if current_index>=0:
                value = variant_to_pyobject(self.itemData(self.currentIndex()))
            else:
                value = None
            return AbstractCustomEditor.get_value(self) or value
