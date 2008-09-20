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
logger.setLevel(logging.DEBUG)

from PyQt4 import QtGui
from PyQt4 import QtCore
from PyQt4.QtCore import Qt

import datetime
from camelot.view.controls import editors


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
    from camelot.view.controls.editors import IntegerEditor
    editor = IntegerEditor(self.minimum, self.maximum, parent)
    return editor

  def setEditorData(self, editor, index):
    value = index.model().data(index, Qt.EditRole).toInt()[0]
    editor.setValue(value)

  def setModelData(self, editor, model, index):
    editor.interpretText()
    model.setData(index, QtCore.QVariant(editor.value()))


class PlainTextColumnDelegate(QtGui.QItemDelegate):
  """Custom delegate for simple string values"""

  def __init__(self, parent=None):
    super(PlainTextColumnDelegate, self).__init__(parent)

  def paint(self, painter, option, index):
    if (option.state & QtGui.QStyle.State_Selected):
      QtGui.QItemDelegate.paint(self, painter, option, index)
    elif not self.parent().columnsdesc[index.column()][1]['editable']:
      _paint_not_editable(painter, option, index)
    elif not self.parent().columnsdesc[index.column()][1]['nullable']:
      _paint_required(painter, option, index)
    else:
      QtGui.QItemDelegate.paint(self, painter, option, index)

  def createEditor(self, parent, option, index):
    from camelot.view.controls.editors import PlainTextEditor
    editor = PlainTextEditor(parent)
    if not self.parent().columnsdesc[index.column()][1]['editable']:
      editor.setEnabled(False)
    return editor

  def setEditorData(self, editor, index):
    value = index.model().data(index, Qt.EditRole).toString()
    editor.setText(value)

  def setModelData(self, editor, model, index):
    model.setData(index, QtCore.QVariant(editor.text()))


class DateColumnDelegate(QtGui.QItemDelegate):
  """Custom delegate for date values"""

  def __init__(self,
               minimum=datetime.date.min,
               maximum=datetime.date.max,
               format='dd/MM/yyyy',
               parent=None):

    super(DateColumnDelegate, self).__init__(parent)
    self.minimum = minimum
    self.maximum = maximum
    self.format = format

  def createEditor(self, parent, option, index):
    from camelot.view.controls.editors import DateEditor
    editor = DateEditor(self.minimum, self.maximum, self.format, parent)
    return editor

  def setEditorData(self, editor, index):
    value = index.model().data(index, Qt.EditRole).toDate()
    editor.setDate(value)

  def setModelData(self, editor, model, index):
    value = editor.date()
    d = datetime.date(value.year(), value.month(), value.day())
    model.setData(index, QtCore.QVariant(d))


class CodeColumnDelegate(QtGui.QItemDelegate):

  def __init__(self, parts, parent=None):
    super(CodeColumnDelegate, self).__init__(parent)
    self.parts = parts

  def createEditor(self, parent, option, index):
    return editors.CodeEditor(self.parts, parent)

  def setEditorData(self, editor, index):
    value = index.data(Qt.EditRole).toPyObject()
    if value:
      for part_editor, part in zip(editor.part_editors, value):
        part_editor.setText(unicode(part))

  def setModelData(self, editor, model, index):
    value = []
    for part in editor.part_editors:
      value.append(unicode(part.text()))
    print value
    model.setData(index, QtCore.QVariant(value))


class FloatColumnDelegate(QtGui.QItemDelegate):
  """Custom delegate for float values"""

  def __init__(self, minimum=-100.0, maximum=100.0, precision=3, parent=None):
    super(FloatColumnDelegate, self).__init__(parent)
    self.minimum = minimum
    self.maximum = maximum
    self.precision = precision

  def createEditor(self, parent, option, index):
    from camelot.view.controls.editors import FloatEditor
    editor = FloatEditor(self.minimum, self.maximum, self.precision, parent)
    return editor

  def setEditorData(self, editor, index):
    value = index.model().data(index, Qt.EditRole).toDouble()[0]
    editor.setValue(value)

  def setModelData(self, editor, model, index):
    editor.interpretText()
    model.setData(index, QtCore.QVariant(editor.value()))


class Many2OneColumnDelegate(QtGui.QItemDelegate):
  """Custom delegate for many 2 one relations"""

  def __init__(self, entity_admin, parent=None):
    logger.info('create many2onecolumn delegate')
    assert entity_admin!=None
    super(Many2OneColumnDelegate, self).__init__(parent)
    self.entity_admin = entity_admin

  def createEditor(self, parent, option, index):
    from camelot.view.controls.editors import Many2OneEditor
    editor = Many2OneEditor(self.entity_admin, parent)
    self.setEditorData(editor, index)
    return editor

  def setEditorData(self, editor, index):
    editor.setEntity(lambda: index.data(Qt.EditRole).toPyObject())

  def setModelData(self, editor, model, index):
    print 'setModelData called'
    #print 'current index is :', editor.currentIndex()
    pass


class One2ManyColumnDelegate(QtGui.QItemDelegate):
  """Custom delegate for many 2 one relations"""

  def __init__(self, entity_admin, field_name, parent=None):
    logger.info('create one2manycolumn delegate')
    assert entity_admin!=None
    super(One2ManyColumnDelegate, self).__init__(parent)
    self.entity_admin = entity_admin
    self.field_name = field_name

  def createEditor(self, parent, option, index):
    logger.info('create a one2many editor')
    from camelot.view.controls.editors import One2ManyEditor
    editor = One2ManyEditor(self.entity_admin, self.field_name, parent)
    self.setEditorData(editor, index)
    return editor

  def setEditorData(self, editor, index):
    logger.info('set one2many editor data')

    def create_entity_instance_getter(model, row):
      return lambda: model._get_object(row)

    editor.setEntityInstance(create_entity_instance_getter(index.model(),
                                                           index.row()))

  def setModelData(self, editor, model, index):
    pass


class BoolColumnDelegate(QtGui.QItemDelegate):
  """Custom delegate for boolean values"""

  def __init__(self, parent=None):
    super(BoolColumnDelegate, self).__init__(parent)

  def createEditor(self, parent, option, index):
    from camelot.view.controls.editors import BoolEditor
    editor = BoolEditor(parent)
    return editor

  def setEditorData(self, editor, index):
    checked = index.model().data(index, Qt.EditRole).toBool()
    editor.setChecked(checked)

  def setModelData(self, editor, model, index):
    model.setData(index, QtCore.QVariant(editor.isChecked()))


class ImageColumnDelegate(QtGui.QItemDelegate):

  def createEditor(self, parent, option, index):
    from camelot.view.controls.editors import ImageEditor
    return ImageEditor(parent)

  def setEditorData(self, editor, index):
    import StringIO
    s = StringIO.StringIO()
    data = index.data(Qt.EditRole).toPyObject()
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
    pass
