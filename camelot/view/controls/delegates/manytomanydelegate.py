from PyQt4 import QtCore

from camelot.view.controls import editors
from one2manydelegate import One2ManyDelegate

class ManyToManyDelegate(One2ManyDelegate):
    """
  .. image:: ../_static/manytomany.png
  """
    
    def createEditor(self, parent, option, index):
        editor = editors.ManyToManyEditor(parent=parent, **self.kwargs)
        self.setEditorData(editor, index)
        self.connect(editor, 
                     editors.editingFinished,
                     self.commitAndCloseEditor)
        return editor
      
    def commitAndCloseEditor(self):
        editor = self.sender()
        self.emit(QtCore.SIGNAL('commitData(QWidget*)'), editor)
        
    def setModelData(self, editor, model, index):
        if editor.getModel():
            model.setData(index, editor.getModel().collection_getter)
