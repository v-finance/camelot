from PyQt4 import QtGui, QtCore
from PyQt4.QtCore import Qt, SIGNAL
from PyQt4.QtGui import QItemDelegate
from camelot.core.utils import variant_to_pyobject

from camelot.view.controls import editors
from camelot.core.utils import create_constant_function
from camelot.view.proxy import ValueLoading

# custom color
not_editable_background = QtGui.QColor(235, 233, 237)
# darkgray
not_editable_foreground = QtGui.QColor(Qt.darkGray)


def DocumentationMetaclass(name, bases, dct):

    dct['__doc__'] = dct.get('__doc__','') + """

.. image:: ../_static/delegates/%s_unselected_disabled.png
.. image:: ../_static/delegates/%s_unselected_editable.png
.. image:: ../_static/delegates/%s_selected_disabled.png
.. image:: ../_static/delegates/%s_selected_editable.png
"""%(name, name, name, name)
    return type(name, bases, dct)
  
class CustomDelegate(QItemDelegate):
  """Base class for implementing custom delegates.

.. attribute:: editor 

class attribute specifies the editor class that should be used
"""

  editor = None
  
  def __init__(self, parent=None, editable=True, **kwargs):
    """
:param parent: the parent object for the delegate
:param editable: a boolean indicating if the field associated to the delegate is editable
"""
    QItemDelegate.__init__(self, parent)
    self.editable = editable
    self.kwargs = kwargs
    self._dummy_editor = self.editor(parent=None, editable=editable, **kwargs)
    
  def createEditor(self, parent, option, index):
    editor = self.editor(parent, editable=self.editable, **self.kwargs)
    self.connect(editor, editors.editingFinished, self.commitAndCloseEditor)
    return editor
  
  def sizeHint(self, option, index):
    return self._dummy_editor.sizeHint()

  def commitAndCloseEditor(self):
    editor = self.sender()
    self.emit(SIGNAL('commitData(QWidget*)'), editor)
    #self.emit(SIGNAL('closeEditor(QWidget*, QAbstractItemDelegate::EndEditHint)'), editor, QtGui.QAbstractItemDelegate.NoHint)

  def setEditorData(self, editor, index):
    value = variant_to_pyobject( index.model().data(index, Qt.EditRole) )
    editor.set_value(value)
    index.model().data(index, Qt.ToolTipRole)
    tooltip = variant_to_pyobject( index.model().data(index, Qt.ToolTipRole) )
    if tooltip!=None:
      editor.setToolTip(unicode(tooltip))
    else:
      editor.setToolTip('')

  def setModelData(self, editor, model, index):
    model.setData(index, create_constant_function(editor.get_value()))
