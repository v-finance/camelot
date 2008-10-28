#  ============================================================================
#
#  Copyright (C) 2007-2008 Conceptive Engineering bvba. All rights reserved.
#  www.conceptive.be / project-camelot@conceptive.be
#
#  This file is part of the Camelot Library.
#
#  This file may be used under the terms of the GNU General Public
#  License version 2.0 as published by the Free Software Foundation
#  and appearing in the file LICENSE.GPL included in the packaging of
#  this file.  Please review the following information to ensure GNU
#  General Public Licensing requirements will be met:
#  http://www.trolltech.com/products/qt/opensource.html
#
#  If you are unsure which license is appropriate for your use, please
#  review the following information:
#  http://www.trolltech.com/products/qt/licensing.html or contact
#  project-camelot@conceptive.be.
#
#  This file is provided AS IS with NO WARRANTY OF ANY KIND, INCLUDING THE
#  WARRANTY OF DESIGN, MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE.
#
#  For use of this library in commercial applications, please contact
#  project-camelot@conceptive.be
#
#  ============================================================================

"""Contains classes for using custom delegates"""

import logging

logger = logging.getLogger('delegates')

from PyQt4 import QtGui
from PyQt4 import QtCore
from PyQt4.QtCore import Qt

import datetime
from camelot.view.controls.editors import *

"""Dictionary mapping widget types to an associated delegate"""
_registered_delegates_ = {}

def _paint_required(painter, option, index):
  text = index.model().data(index, Qt.DisplayRole).toString()
  painter.save()

  #painter.setPen(QtGui.QColor(Qt.red))

  font = painter.font()
  font.setBold(True)
  painter.setFont(font)

  painter.drawText(option.rect.x()+2,
                   option.rect.y(),
                   option.rect.width()-4,
                   option.rect.height(),
                   Qt.AlignVCenter,
                   text)

  painter.restore()


def _paint_not_editable(painter, option, index):
  text = index.model().data(index, Qt.DisplayRole).toString()
  color = QtGui.QColor(235, 233, 237)
  painter.save()

  painter.fillRect(option.rect, color)
  painter.setPen(QtGui.QColor(Qt.darkGray))
  painter.drawText(option.rect.x()+2,
                   option.rect.y(),
                   option.rect.width()-4,
                   option.rect.height(),
                   Qt.AlignVCenter,
                   text)

  painter.restore()

def create_constant_function(constant):
  return lambda:constant

class GenericDelegate(QtGui.QItemDelegate):
  """Manages custom delegates"""

  def __init__(self, parent=None):
    super(GenericDelegate, self).__init__(parent)
    self.delegates = {}

  def set_columns_desc(self, columnsdesc):
    self.columnsdesc = columnsdesc

  def insertColumnDelegate(self, column, delegate):
    """Inserts a custom column delegate"""
    logger.debug('inserting a new custom column delegate')
    delegate.setParent(self)
    self.delegates[column] = delegate

  def removeColumnDelegate(self, column):
    """Removes custom column delegate"""
    logger.debug('removing a new custom column delegate')
    if column in self.delegates:
      del self.delegates[column]

  def paint(self, painter, option, index):
    """Use a custom delegate paint method if it exists"""
    delegate = self.delegates.get(index.column())
    if delegate is not None:
      delegate.paint(painter, option, index)
    else:
      QtGui.QItemDelegate.paint(self, painter, option, index)

  def createEditor(self, parent, option, index):
    """Use a custom delegate createEditor method if it exists"""
    delegate = self.delegates.get(index.column())
    if delegate is not None:
      return delegate.createEditor(parent, option, index)
    else:
      QtGui.QItemDelegate.createEditor(self, parent, option, index)

  def setEditorData(self, editor, index):
    """Use a custom delegate setEditorData method if it exists"""
    logger.debug('setting delegate data editor for column %s' % index.column())
    delegate = self.delegates.get(index.column())
    if delegate is not None:
      delegate.setEditorData(editor, index)
    else:
      QtGui.QItemDelegate.setEditorData(self, editor, index)

  def setModelData(self, editor, model, index):
    """Use a custom delegate setModelData method if it exists"""
    logger.debug('setting model data for column %s' % index.column())
    delegate = self.delegates.get(index.column())
    if delegate is not None:
      delegate.setModelData(editor, model, index)
    else:
      QtGui.QItemDelegate.setModelData(self, editor, model, index)


class IntegerColumnDelegate(QtGui.QItemDelegate):
  """Custom delegate for integer values"""

  def __init__(self, minimum=0, maximum=100, parent=None):
    super(IntegerColumnDelegate, self).__init__(parent)
    self.minimum = minimum
    self.maximum = maximum

  def createEditor(self, parent, option, index):
    editor = QtGui.QSpinBox(parent)
    editor.setRange(self.minimum, self.maximum)
    editor.setAlignment(Qt.AlignRight|Qt.AlignVCenter)
    return editor

  def setEditorData(self, editor, index):
    value = index.model().data(index, Qt.EditRole).toInt()[0]
    editor.setValue(value)

  def setModelData(self, editor, model, index):
    editor.interpretText()
    model.setData(index, create_constant_function(editor.value()))

_registered_delegates_[QtGui.QSpinBox] = IntegerColumnDelegate

class PlainTextColumnDelegate(QtGui.QItemDelegate):
  """Custom delegate for simple string values"""

  def __init__(self, parent=None):
    super(PlainTextColumnDelegate, self).__init__(parent)

  def paint(self, painter, option, index):
    if (option.state & QtGui.QStyle.State_Selected):
      QtGui.QItemDelegate.paint(self, painter, option, index)
    elif not self.parent().columnsdesc[index.column()][1]['editable']:
      _paint_not_editable(painter, option, index)
  #  elif not self.parent().columnsdesc[index.column()][1]['nullable']:
  #    _paint_required(painter, option, index)
    else:
      QtGui.QItemDelegate.paint(self, painter, option, index)

  def createEditor(self, parent, option, index):
    editor = QtGui.QLineEdit(parent)
    if not self.parent().columnsdesc[index.column()][1]['editable']:
      editor.setEnabled(False)
    return editor

  def setEditorData(self, editor, index):
    value = index.model().data(index, Qt.EditRole).toString()
    editor.setText(value)

  def setModelData(self, editor, model, index):
    model.setData(index, create_constant_function(unicode(editor.text())))

_registered_delegates_[QtGui.QLineEdit] = PlainTextColumnDelegate

class TimeColumnDelegate(QtGui.QItemDelegate):
  
  def __init__(self, format, default, nullable, parent=None):
    super(TimeColumnDelegate, self).__init__(parent)
    self.nullable = nullable
    self.format = format
    self.default = default
    
  def createEditor(self, parent, option, index):
    editor = QtGui.QTimeEdit(parent)
    editor.setDisplayFormat(self.format)
    return editor
  
  def setEditorData(self, editor, index):
    value = index.model().data(index, Qt.EditRole).toTime()
    editor.index = index
    if value:
      editor.setTime(value)
    else:
      editor.setTime(editor.minimumTime())
  
  def setModelData(self, editor, model, index):
    value = editor.time()
    t = datetime.time(hour=value.hour(), minute=value.minute(), second=value.second())
    model.setData(index, create_constant_function(t))
  
class DateColumnDelegate(QtGui.QItemDelegate):
  """Custom delegate for date values"""

  def __init__(self,
               format='dd/MM/yyyy',
               default=None,
               nullable=True,
               parent=None):

    super(DateColumnDelegate, self).__init__(parent)
    self.format = format
    self.default = default
    self.nullable = nullable

  def createEditor(self, parent, option, index):
    
    editor = DateEditor(self, self.nullable, self.format, parent)
    return editor

  def setEditorData(self, editor, index):
    value = index.model().data(index, Qt.EditRole).toDate()
    editor.index = index
    if value:
      editor.setDate(value)
    else:
      editor.setDate(editor.minimumDate())

  def setModelData(self, editor, model, index):
    value = editor.date()
    
    if value == editor.minimumDate():
      model.setData(index, create_constant_function(None))
    else:
      d = datetime.date(value.year(), value.month(), value.day())
      model.setData(index, create_constant_function(d))

_registered_delegates_[DateEditor] = DateColumnDelegate

class CodeColumnDelegate(QtGui.QItemDelegate):

  def __init__(self, parts, parent=None):
    super(CodeColumnDelegate, self).__init__(parent)
    self.parts = parts

  def createEditor(self, parent, option, index):
    return CodeEditor(self.parts, self, parent)

  def setEditorData(self, editor, index):
    value = index.data(Qt.EditRole).toPyObject()
    editor.index = index
    if value:
      for part_editor, part in zip(editor.part_editors, value):
        part_editor.setText(unicode(part))

  def setModelData(self, editor, model, index):
    from camelot.types import Code
    value = []
    for part in editor.part_editors:
      value.append(unicode(part.text()))
    model.setData(index, create_constant_function(value))
    
  def editingFinished(self, widget):
    self.emit(QtCore.SIGNAL('commitData(QWidget*)'), widget)

_registered_delegates_[CodeEditor] = CodeColumnDelegate

class VirtualAddressColumnDelegate(QtGui.QItemDelegate):

  def __init__(self, parent=None):
    super(VirtualAddressColumnDelegate, self).__init__(parent)

  def createEditor(self, parent, option, index):
    return VirtualAddressEditor(parent)

  def setEditorData(self, editor, index):
    import camelot.types
    value = index.data(Qt.EditRole).toPyObject()
    editor.index = index
    editor.delegate = self
    if value:
      editor.editor.setText(value[1])
      editor.combo.setCurrentIndex(camelot.types.VirtualAddress.virtual_address_types.index(value[0]))
      
  def setModelData(self, editor, model, index):
    value = (unicode(editor.combo.currentText()), unicode(editor.editor.text()))
    model.setData(index, create_constant_function(value))

_registered_delegates_[VirtualAddressEditor] = VirtualAddressColumnDelegate

class FloatColumnDelegate(QtGui.QItemDelegate):
  """Custom delegate for float values"""

  def __init__(self, minimum=-100.0, maximum=100.0, precision=3, parent=None):
    super(FloatColumnDelegate, self).__init__(parent)
    self.minimum = minimum
    self.maximum = maximum
    self.precision = precision

  def createEditor(self, parent, option, index):
    editor = QtGui.QDoubleSpinBox(parent)
    editor.setRange(self.minimum, self.maximum)
    editor.setDecimals(self.precision)
    editor.setAlignment(Qt.AlignRight|Qt.AlignVCenter)
    editor.setSingleStep(1.0)
    return editor

  def setEditorData(self, editor, index):
    value = index.model().data(index, Qt.EditRole).toDouble()[0]
    editor.setValue(value)

  def setModelData(self, editor, model, index):
    editor.interpretText()
    model.setData(index, create_constant_function(editor.value()))

_registered_delegates_[QtGui.QDoubleSpinBox] = FloatColumnDelegate

class Many2OneColumnDelegate(QtGui.QItemDelegate):
  """Custom delegate for many 2 one relations"""

  def __init__(self, entity_admin, parent=None):
    logger.debug('create many2onecolumn delegate')
    assert entity_admin!=None
    super(Many2OneColumnDelegate, self).__init__(parent)
    self.entity_admin = entity_admin

  def createEditor(self, parent, option, index):
    editor = Many2OneEditor(self.entity_admin, self, parent)
    self.setEditorData(editor, index)
    return editor

  def setEditorData(self, editor, index):
    editor.index = index
    editor.setEntity(lambda: index.data(Qt.EditRole).toPyObject(), propagate=False)

  def setModelData(self, editor, model, index):
    model.setData(index, editor.entity_instance_getter)

_registered_delegates_[Many2OneEditor] = Many2OneColumnDelegate

class One2ManyColumnDelegate(QtGui.QItemDelegate):
  """Custom delegate for many 2 one relations"""

  def __init__(self, entity_admin, field_name, parent=None):
    logger.debug('create one2manycolumn delegate')
    assert entity_admin!=None
    super(One2ManyColumnDelegate, self).__init__(parent)
    self.entity_admin = entity_admin
    self.field_name = field_name

  def createEditor(self, parent, option, index):
    logger.debug('create a one2many editor')
    editor = One2ManyEditor(self.entity_admin, self.field_name, parent)
    self.setEditorData(editor, index)
    return editor

  def setEditorData(self, editor, index):
    logger.debug('set one2many editor data')
    model = index.data(Qt.EditRole).toPyObject()
    if model:
      editor.setModel(model)

  def setModelData(self, editor, model, index):
    pass

_registered_delegates_[One2ManyEditor] = One2ManyColumnDelegate

class BoolColumnDelegate(QtGui.QItemDelegate):
  """Custom delegate for boolean values"""

  def __init__(self, parent=None):
    super(BoolColumnDelegate, self).__init__(parent)

  def createEditor(self, parent, option, index):
    editor = QtGui.QCheckBox(parent)
    return editor

  def setEditorData(self, editor, index):
    checked = index.model().data(index, Qt.EditRole).toBool()
    editor.setChecked(checked)

  def setModelData(self, editor, model, index):
    model.setData(index, create_constant_function(editor.isChecked()))

_registered_delegates_[QtGui.QCheckBox] = BoolColumnDelegate

class ImageColumnDelegate(QtGui.QItemDelegate):

  def createEditor(self, parent, option, index):
    return ImageEditor(parent)

  def setEditorData(self, editor, index):
    import StringIO
    s = StringIO.StringIO()
    data = index.data(Qt.EditRole).toPyObject()
    editor.image = data
    editor.delegate = self
    editor.index = index
    if data:
      data.thumbnail((100, 100))
      data.save(s, 'png')
      s.seek(0)
      pixmap = QtGui.QPixmap()
      pixmap.loadFromData(s.read())
      s.close()
      editor.setPixmap(pixmap)
    else:
      #@todo: clear pixmap
      pass

  def setModelData(self, editor, model, index):
    model.setData(index, create_constant_function(editor.image))
  
_registered_delegates_[ImageEditor] = ImageColumnDelegate

class RichTextColumnDelegate(QtGui.QItemDelegate):

  def createEditor(self, parent, option, index):
    return RichTextEditor(parent)

  def setEditorData(self, editor, index):
    html = index.model().data(index, Qt.EditRole).toString()
    if html:
      editor.setHtml(html)
    else:
      editor.clear()

  def setModelData(self, editor, model, index):
    model.setData(index, create_constant_function(unicode(editor.toHtml())))

_registered_delegates_[RichTextEditor] = RichTextColumnDelegate