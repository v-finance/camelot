
try:
  from PyQt4 import QtGui, QtCore
  from PyQt4.QtCore import Qt, SIGNAL
  from PyQt4.QtGui import QItemDelegate
  from camelot.core.utils import variant_to_pyobject
  
  from camelot.view.controls import editors
except ImportError:
  raise
  #
  # dummy class when Qt has not been found, this allows the documentation to be
  # build without qt dependency
  #
  class QItemDelegate(object):
    pass
  
  class editors(object):
    FileEditor = None 

from camelot.view.proxy import ValueLoading
from camelot.view.model_thread import get_model_thread
from camelot.core.utils import create_constant_function

import datetime
import camelot.types

# custom color
not_editable_background = QtGui.QColor(235, 233, 237)
# darkgray
not_editable_foreground = QtGui.QColor(Qt.darkGray)


def DocumentationMetaclass(name, bases, dct):
    #print dct['__doc__']
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
    QItemDelegate.__init__(self, parent)
    self.editable = editable
    self.kwargs = kwargs
    
  def createEditor(self, parent, option, index):
    editor = self.editor(parent, editable=self.editable, **self.kwargs)
    self.connect(editor, editors.editingFinished, self.commitAndCloseEditor)
    return editor

  def commitAndCloseEditor(self):
    editor = self.sender()
    #print "commitAndCloseEditor"
    self.emit(SIGNAL('commitData(QWidget*)'), editor)
    self.emit(SIGNAL('closeEditor(QWidget*)'), editor)

  def setEditorData(self, editor, index):
    qvariant = index.model().data(index, Qt.EditRole)
    #
    # Conversion from a qvariant to a python object is highly dependent on the
    # version of pyqt that is being used, we'll try to circumvent most problems
    # here and always return nice python objects.
    #
#    type = qvariant.type()
#    if type == QtCore.QVariant.String:
#      value = unicode(qvariant.toString())
#    elif type == QtCore.QVariant.Date:
#      value = qvariant.toDate()
#      value = datetime.date(year=value.year(),
#                            month=value.month(),
#                            day=value.day())
#    elif type == QtCore.QVariant.Int:
#      value = int(qvariant.toInt()[0])
#    elif type == QtCore.QVariant.Double:
#      value = float(qvariant.toDouble()[0])
#    elif type == QtCore.QVariant.Bool:
#      value = bool(qvariant.toBool())
#    elif type == QtCore.QVariant.Time:
#        value = qvariant.toTime()
#        value = datetime.time(hour = value.hour(),
#                              minute = value.minute(),
#                              second = value.second())
#    else:
#      value = index.model().data(index, Qt.EditRole).toPyObject()
      
      
    value = variant_to_pyobject(qvariant)
      
    editor.set_value(value)

  def setModelData(self, editor, model, index):
    value = editor.get_value()
    #print value, type(value)
    model.setData(index, create_constant_function(editor.get_value()))
