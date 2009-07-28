
from customdelegate import *

import logging
logger = logging.getLogger('camelot.view.controls.delegates.one2manydelegate')

class One2ManyDelegate(QItemDelegate):
  """Custom delegate for many 2 one relations

.. image:: ../_static/onetomany.png  
"""

  def __init__(self, parent=None, **kwargs):
    logger.debug('create one2manycolumn delegate')
    assert 'admin' in kwargs
    QItemDelegate.__init__(self, parent)
    self.kwargs = kwargs

  def createEditor(self, parent, option, index):
    logger.debug('create a one2many editor')
    editor = editors.One2ManyEditor(parent=parent, **self.kwargs)
    self.setEditorData(editor, index)
    return editor

  def setEditorData(self, editor, index):
    logger.debug('set one2many editor data')
    model = index.data(Qt.EditRole).toPyObject()
    editor.set_value(model)

  def setModelData(self, editor, model, index):
    pass
