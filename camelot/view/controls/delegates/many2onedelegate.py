
from customdelegate import *

import logging
logger = logging.getLogger('camelot.view.controls.delegates.many2onedelegate')

class Many2OneDelegate(CustomDelegate):
  """Custom delegate for many 2 one relations
  
.. image:: ../_static/manytoone.png
"""

  def __init__(self,
               parent=None,
               admin=None,
               embedded=False,
               editable=True,
               **kwargs):
    logger.debug('create many2onecolumn delegate')
    assert admin != None
    CustomDelegate.__init__(self, parent, editable, **kwargs)
    self.admin = admin
    self._embedded = embedded
    self._kwargs = kwargs
    self._dummy_editor = editors.Many2OneEditor(self.admin, None)

#  def paint(self, painter, option, index):
#    painter.save()
#    self.drawBackground(painter, option, index)
#    print option.state, '%08x'%(option.state)
#    if not (option.state & QtGui.QStyle.State_Editing):
#      self.drawDisplay(painter,
#                       option,
#                       option.rect,
#                       index.data(Qt.DisplayRole).toString())
#    painter.restore()
    
  def createEditor(self, parent, option, index):
    if self._embedded:
      editor = editors.EmbeddedMany2OneEditor(self.admin, parent)
    else:
      editor = editors.Many2OneEditor(self.admin, parent)
    self.connect(editor,
                 SIGNAL('editingFinished()'),
                 self.commitAndCloseEditor)
    return editor

  def setEditorData(self, editor, index):
    value = index.data(Qt.EditRole).toPyObject()
    if value!=ValueLoading:
      editor.set_value(create_constant_function(value))
    else:
      editor.set_value(ValueLoading)

  def setModelData(self, editor, model, index):
    if editor.entity_instance_getter:
      model.setData(index, editor.entity_instance_getter)
    
  def sizeHint(self, option, index):
    return self._dummy_editor.sizeHint()    
