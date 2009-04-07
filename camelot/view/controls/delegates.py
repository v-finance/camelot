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

logger = logging.getLogger('camelot.view.controls.delegates')

from PyQt4 import QtGui
from PyQt4 import QtCore
from PyQt4.QtCore import Qt

import datetime
import StringIO

import camelot.types
from camelot.view.art import Icon
from camelot.view.controls import editors 
from camelot.view.model_thread import get_model_thread


"""Dictionary mapping widget types to an associated delegate"""

_registered_delegates_ = {}

_not_editable_background_ = QtGui.QColor(235, 233, 237)
_not_editable_foreground_ = QtGui.QColor(Qt.darkGray)

def _paint_not_editable(painter, option, index):
  text = index.model().data(index, Qt.DisplayRole).toString()
  painter.save()
  if (option.state & QtGui.QStyle.State_Selected):
    painter.fillRect(option.rect, option.palette.highlight())
    painter.setPen(option.palette.highlightedText().color())
  else:
    painter.fillRect(option.rect, _not_editable_background_)
    painter.setPen(_not_editable_foreground_)
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
    logger.debug('inserting delegate for column %s' % column)
    delegate.setParent(self)
    self.delegates[column] = delegate
    self.connect(delegate, QtCore.SIGNAL('commitData(QWidget*)'), self.commitData)
    self.connect(delegate, QtCore.SIGNAL('closeEditor(QWidget*)'), self.closeEditor)   

  def commitData(self, editor):
    self.emit(QtCore.SIGNAL('commitData(QWidget*)'), editor)
    
  def closeEditor(self, editor):
    self.emit(QtCore.SIGNAL('closeEditor(QWidget*)'), editor)
    
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
    logger.debug('setting editor data for column %s' % index.column())
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
      
  def sizeHint(self, option, index):
    option = QtGui.QStyleOptionViewItem()
    delegate = self.delegates.get(index.column())
    if delegate is not None:
      return delegate.sizeHint(option, index)
    else:
      return QtGui.QItemDelegate.sizeHint(self, option, index)

class StarDelegate(QtGui.QItemDelegate):
  """Custom delegate for integer values from (1 to 5)(Rating Delegate)"""

  def __init__(self, maximum=5, editable=True, parent=None, **kwargs):
    super(StarDelegate, self).__init__(parent)
    self.maximum = maximum
    self.editable = True

  def createEditor(self, parent, option, index):
    editor = editors.StarEditor(parent, self.maximum, self.editable)
    self.connect(editor, QtCore.SIGNAL('editingFinished()'), self.commitAndCloseEditor)
    return editor

  def setEditorData(self, editor, index):
    value = index.model().data(index, Qt.EditRole).toInt()[0]
    editor.setValue(value)

  def setModelData(self, editor, model, index):
    #editor.interpretText()
    model.setData(index, create_constant_function(editor.getValue()))


  def commitAndCloseEditor(self):
    editor = self.sender()

    self.emit(QtCore.SIGNAL('commitData(QWidget*)'), editor)
    
    
    
  def paint(self, painter, option, index):
    painter.save()
    self.drawBackground(painter, option, index)
    stars = index.model().data(index, Qt.EditRole).toInt()[0]
    editor = editors.StarEditor(parent=None, maximum=self.maximum, editable=self.editable)
    rect = option.rect
    rect = QtCore.QRect(rect.left()+3, rect.top()+6, rect.width()-5, rect.height())
    
    
    for i in range(5):
      if i+1<=stars:
        icon = Icon('tango/16x16/status/weather-clear.png').getQPixmap()
        QtGui.QApplication.style().drawItemPixmap(painter, rect, 1, icon)

        rect = QtCore.QRect(rect.left()+20, rect.top(), rect.width(), rect.height())
        
#      else:
#        icon = Icon('').getQPixmap()
#        QtGui.QApplication.style().drawItemPixmap(painter, rect, 1, icon)
#        rect = QtCore.QRect(rect.left()+20, rect.top(), rect.width(), rect.height())
#      

    painter.restore()


_registered_delegates_[editors.StarEditor] = StarDelegate

camelot_maxint = 2147483647
camelot_minint = -2147483648

class IntegerColumnDelegate(QtGui.QItemDelegate):
  """Custom delegate for integer values"""

  def __init__(self, parent, minimum=camelot_minint, maximum=camelot_maxint, editable=True, **kwargs):
    super(IntegerColumnDelegate, self).__init__(parent)
    self.minimum = minimum
    self.maximum = maximum
    self.editable = editable

  def paint(self, painter, option, index):
    self.drawBackground(painter, option, index)
    painter.save()
    if (option.state & QtGui.QStyle.State_Selected):
      painter.fillRect(option.rect, option.palette.highlight())
      painter.setPen(option.palette.highlightedText().color())
    elif not self.editable:
      painter.fillRect(option.rect, _not_editable_background_)
      painter.setPen(_not_editable_foreground_)
    value =  index.model().data(index, Qt.DisplayRole).toString()
    painter.drawText(option.rect.x()+2,
                     option.rect.y(),
                     option.rect.width()-4,
                     option.rect.height(),
                     Qt.AlignVCenter | Qt.AlignRight,
                     value)
    painter.restore()
      
  def createEditor(self, parent, option, index):
    editor = editors.IntegerEditor(parent, self.minimum, self.maximum, self.editable)
    self.connect(editor, QtCore.SIGNAL('editingFinished()'), self.commitAndCloseEditor)
    return editor

  def setEditorData(self, editor, index):
    value = index.model().data(index, Qt.EditRole).toInt()[0]
    editor.setValue(value)

  def setModelData(self, editor, model, index):
    model.setData(index, create_constant_function(editor.value()))

  def commitAndCloseEditor(self):
    editor = self.sender()
    self.emit(QtCore.SIGNAL('commitData(QWidget*)'), editor)

_registered_delegates_[QtGui.QSpinBox] = IntegerColumnDelegate

class SliderDelegate(IntegerColumnDelegate):
  """A delegate for horizontal sliders"""
  
  def createEditor(self, parent, option, index):
    editor = QtGui.QSlider(Qt.Horizontal, parent)
    editor.setRange(self.minimum, self.maximum)
    editor.setTickPosition(QtGui.QSlider.TicksBelow)
    return editor
  
  def setModelData(self, editor, model, index):
    model.setData(index, create_constant_function(editor.value()))  

class PlainTextColumnDelegate(QtGui.QItemDelegate):
  """Custom delegate for simple string values"""

  def __init__(self, maxlength=None, parent=None, **kwargs):
    super(PlainTextColumnDelegate, self).__init__(parent)
    self.maxlength = maxlength

  def paint(self, painter, option, index):
    if (option.state & QtGui.QStyle.State_Selected):
      QtGui.QItemDelegate.paint(self, painter, option, index)
    elif not self.parent().columnsdesc[index.column()][1]['editable']:
      _paint_not_editable(painter, option, index)
    else:
      QtGui.QItemDelegate.paint(self, painter, option, index)

  def createEditor(self, parent, option, index):
    editor = QtGui.QLineEdit(parent)
    editor.setMaxLength(self.maxlength)
    if not self.parent().columnsdesc[index.column()][1]['editable']:
      editor.setEnabled(False)
    return editor

  def setEditorData(self, editor, index):
    value = index.model().data(index, Qt.EditRole).toString()
    editor.setText(value)

  def setModelData(self, editor, model, index):
    model.setData(index, create_constant_function(unicode(editor.text())))

_registered_delegates_[QtGui.QLineEdit] = PlainTextColumnDelegate


class TextEditColumnDelegate(QtGui.QItemDelegate):
  """Edit plain text with a QTextEdit widget"""
  
  def __init__(self, parent=None, editable=True, **kwargs):
    super(TextEditColumnDelegate, self).__init__(parent)
    self.editable = editable
    
  def createEditor(self, parent, option, index):
    editor = QtGui.QTextEdit(parent)
    return editor

  def setEditorData(self, editor, index):
    value = index.model().data(index, Qt.EditRole).toString()
    editor.setText(value)

  def setModelData(self, editor, model, index):
    model.setData(index, create_constant_function(unicode(editor.toPlainText())))

class IntervalsColumnDelegate(QtGui.QItemDelegate):
  """Custom delegate for visualizing camelot.container.IntervalsContainer
  data"""

  def __init__(self, parent=None, **kwargs):
    super(IntervalsColumnDelegate, self).__init__(parent)
    
  def paint(self, painter, option, index):
    painter.save()
    self.drawBackground(painter, option, index)
    intervals = index.model().data(index, Qt.EditRole).toPyObject()
    if intervals:
      rect = option.rect
      xscale = float(rect.width()-4)/(intervals.max-intervals.min)
      xoffset = intervals.min * xscale + rect.x()
      yoffset = rect.y() + rect.height()/2
      for interval in intervals.intervals:
        qcolor = QtGui.QColor()
        qcolor.setRgb(*interval.color)
        pen = QtGui.QPen(qcolor)
        pen.setWidth(3)
        painter.setPen(pen)
        x1, x2 =  xoffset + interval.begin*xscale, xoffset + interval.end*xscale
        painter.drawLine(x1, yoffset, x2, yoffset)
        painter.drawEllipse(x1-1, yoffset-1, 2, 2)
        painter.drawEllipse(x2-1, yoffset-1, 2, 2)
    painter.restore()
      
  def createEditor(self, parent, option, index):
    pass
    
  def setEditorData(self, editor, index):
    pass

  def setModelData(self, editor, model, index):
    pass

class ColorColumnDelegate(QtGui.QItemDelegate):

  def __init__(self, parent=None, **kwargs):
    super(ColorColumnDelegate, self).__init__(parent)
    
  def paint(self, painter, option, index):
    painter.save()
    self.drawBackground(painter, option, index)
    color = index.model().data(index, Qt.EditRole).toPyObject()  
    if color:
      pixmap = QtGui.QPixmap(16, 16)
      qcolor = QtGui.QColor()
      qcolor.setRgb(*color)
      pixmap.fill(qcolor)
      QtGui.QApplication.style().drawItemPixmap(painter, option.rect, Qt.AlignVCenter, pixmap)
    painter.restore()
      
  def createEditor(self, parent, option, index):
    editor = editors.ColorEditor(parent)
    self.connect(editor, QtCore.SIGNAL('editingFinished()'), self.commitAndCloseEditor)
    return editor

  def commitAndCloseEditor(self):
    editor = self.sender()
    self.emit(QtCore.SIGNAL('commitData(QWidget*)'), editor)
    
  def setEditorData(self, editor, index):
    value = index.model().data(index, Qt.EditRole).toPyObject()
    if value:
      color = QtGui.QColor()
      color.setRgb(*value)
      editor.setColor(color)
    else:
      editor.setColor(value)

  def setModelData(self, editor, model, index):
    color = editor.getColor()
    if color:
      model.setData(index, create_constant_function((color.red(), color.green(), color.blue(), color.alpha())))
    else:
      model.setData(index, create_constant_function(None))

class TimeColumnDelegate(QtGui.QItemDelegate):
  def __init__(self, parent, format='hh:mm', default=None, nullable=True, **kwargs):
    super(TimeColumnDelegate, self).__init__(parent)
    self.nullable = nullable
    self.format = format
    self.default = default
    self.kwargs = kwargs
    
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
  

class DateTimeColumnDelegate(QtGui.QItemDelegate):
  def __init__(self, parent, format, **kwargs):
    from editors import DateTimeEditor
    super(DateTimeColumnDelegate, self).__init__(parent)
    self.format = format
    self.kwargs = kwargs
    self._dummy_editor = DateTimeEditor(parent, self.format, **self.kwargs)
    
  def createEditor(self, parent, option, index):
    from editors import DateTimeEditor
    editor = DateTimeEditor(parent, self.format, **self.kwargs)
    return editor
  
  def setEditorData(self, editor, index):
    editor.setDateTime(index.model().data(index, Qt.EditRole).toPyObject())
      
  def setModelData(self, editor, model, index):
    time_value = editor.time()
    date_value = editor.date()
    t = datetime.datetime(hour=time_value.hour(), minute=time_value.minute(), second=time_value.second(),
                          year=date_value.year(), month=date_value.month(), day=date_value.day())
    model.setData(index, create_constant_function(t))
    
  def sizeHint(self, option, index):
    return self._dummy_editor.sizeHint()
    

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
    editor = editors.DateEditor(self.nullable, self.format, parent)
    self.connect(editor, QtCore.SIGNAL('editingFinished()'), self.commitAndCloseEditor)  
    return editor

  def commitAndCloseEditor(self):
    editor = self.sender()
    self.emit(QtCore.SIGNAL('commitData(QWidget*)'), editor)
    #self.emit(QtCore.SIGNAL('closeEditor(QWidget*)'), editor)
  
  def setEditorData(self, editor, index):
    value = index.model().data(index, Qt.EditRole).toDate()
    editor._index = index
    if value:
      editor.setDate(value)
    else:
      editor.setDate(editor.minimumDate())

  def setModelData(self, editor, model, index):
    logger.debug('date delegate set model data')
    value = editor.date()
    logger.debug('date delegate got value')
    if value == editor.minimumDate():
      model.setData(index, create_constant_function(None))
    else:
      d = datetime.date(value.year(), value.month(), value.day())
      model.setData(index, create_constant_function(d))
    logger.debug('date delegate data set')

_registered_delegates_[editors.DateEditor] = DateColumnDelegate


class CodeColumnDelegate(QtGui.QItemDelegate):
  def __init__(self, parts, parent=None):
    super(CodeColumnDelegate, self).__init__(parent)
    self.parts = parts
    self._dummy_editor = editors.CodeEditor(self.parts, None)

  def createEditor(self, parent, option, index):
    editor = editors.CodeEditor(self.parts, parent)
    self.connect(editor, QtCore.SIGNAL('editingFinished()'), self.commitAndCloseEditor)
    return editor

  def commitAndCloseEditor(self):
    editor = self.sender()
    self.emit(QtCore.SIGNAL('commitData(QWidget*)'), editor)
    #self.emit(QtCore.SIGNAL('closeEditor(QWidget*)'), editor)
    
  def setEditorData(self, editor, index):
    value = index.data(Qt.EditRole).toPyObject()
    if value:
      for part_editor, part in zip(editor.part_editors, value):
        part_editor.setText(unicode(part))

  def sizeHint(self, option, index):
    return self._dummy_editor.sizeHint() 
  
  def setModelData(self, editor, model, index):
    value = []
    for part in editor.part_editors:
      value.append(unicode(part.text()))
    model.setData(index, create_constant_function(value))

_registered_delegates_[editors.CodeEditor] = CodeColumnDelegate


class VirtualAddressColumnDelegate(QtGui.QItemDelegate):
  def __init__(self, parent=None):
    super(VirtualAddressColumnDelegate, self).__init__(parent)

  def paint(self, painter, option, index):
    painter.save()
    self.drawBackground(painter, option, index)
    virtual_address = index.model().data(index, Qt.EditRole).toPyObject()  
    if virtual_address and virtual_address[1]:
      painter.drawText(option.rect, Qt.AlignLeft, '%s : %s'%virtual_address)
      rect = option.rect
      rect = QtCore.QRect(rect.width()-19, rect.top()+6, 16, 16)
      if virtual_adress[0] == 'email':
        icon = Icon('tango/16x16/apps/internet-mail.png').getQPixmap()
        painter.drawPixmap(rect, icon)
      else:
      #if virtual_adress[0] == 'telephone':
        icon = Icon('tango/16x16/apps/preferences-desktop-sound.png').getQPixmap()
        painter.drawPixmap(rect, icon)
        
        
    painter.restore()
    
  def commitAndCloseEditor(self):
    editor = self.sender()
    self.emit(QtCore.SIGNAL('commitData(QWidget*)'), editor)
    #self.emit(QtCore.SIGNAL('closeEditor(QWidget*)'), editor)
  
  def createEditor(self, parent, option, index):
    editor = editors.VirtualAddressEditor(parent)
    self.connect(editor, QtCore.SIGNAL('editingFinished()'), self.commitAndCloseEditor)
    return editor

  def setEditorData(self, editor, index):
    value = index.data(Qt.EditRole).toPyObject()
    editor.setData(value)
      
  def setModelData(self, editor, model, index):
    value = (unicode(editor.combo.currentText()), unicode(editor.editor.text()))
    model.setData(index, create_constant_function(value))

_registered_delegates_[editors.VirtualAddressEditor] = \
    VirtualAddressColumnDelegate


class FloatColumnDelegate(QtGui.QItemDelegate):
  """Custom delegate for float values"""

  def __init__(self, minimum=-1e15, maximum=1e15, precision=2,
               editable=True, parent=None, **kwargs):
    super(FloatColumnDelegate, self).__init__(parent)
    self.minimum = minimum
    self.maximum = maximum
    self.precision = precision
    self.editable = editable

  def createEditor(self, parent, option, index):
    editor = editors.FloatEditor(parent, self.precision, self.minimum, self.maximum, self.editable)
    self.connect(editor, QtCore.SIGNAL('editingFinished()'), self.commitAndCloseEditor)
    return editor

  def setEditorData(self, editor, index):
    value = index.model().data(index, Qt.EditRole).toDouble()[0]
    editor.setValue(value)

  def setModelData(self, editor, model, index):
    model.setData(index, create_constant_function(editor.value()))
    
    
  def commitAndCloseEditor(self):
    editor = self.sender()

    self.emit(QtCore.SIGNAL('commitData(QWidget*)'), editor)

_registered_delegates_[QtGui.QDoubleSpinBox] = FloatColumnDelegate



class ColoredFloatColumnDelegate(QtGui.QItemDelegate):
  """Custom delegate for float values, representing them in green when they are
  positive and in red when they are negative."""

  def __init__(self, minimum=-1e15, maximum=1e15, precision=2,
               editable=True, parent=None, unicode_format=None, **kwargs):
    super(ColoredFloatColumnDelegate, self).__init__(parent)
    self.minimum = minimum
    self.maximum = maximum
    self.precision = precision
    self.editable = editable
    self.unicode_format = unicode_format

  def createEditor(self, parent, option, index):
    editor = editors.ColoredFloatEditor(parent, self.precision, self.minimum, self.maximum, self.editable)
    self.connect(editor, QtCore.SIGNAL('editingFinished()'), self.commitAndCloseEditor)
    return editor

  def setEditorData(self, editor, index):
    value = index.model().data(index, Qt.EditRole).toDouble()[0]
    editor.setValue(value)

  def setModelData(self, editor, model, index):
    model.setData(index, create_constant_function(editor.value()))
    
    
  def commitAndCloseEditor(self):
    editor = self.sender()
    self.emit(QtCore.SIGNAL('commitData(QWidget*)'), editor)
    
  def paint(self, painter, option, index):
    painter.save()
    self.drawBackground(painter, option, index)
    value = index.model().data(index, Qt.EditRole).toDouble()[0]
    editor = editors.ColoredFloatEditor(parent=None, minimum=self.minimum, maximum=self.maximum, precision=self.precision, editable=self.editable)
    rect = option.rect
    rect = QtCore.QRect(rect.left()+3, rect.top()+6, 16, 16)
    fontColor = QtGui.QColor()
    if value >= 0:
      if value == 0:
        icon = Icon('tango/16x16/actions/zero.png').getQPixmap()
        QtGui.QApplication.style().drawItemPixmap(painter, rect, 1, icon)
        fontColor.setRgb(0, 0, 0)
      else:
        icon = Icon('tango/16x16/actions/go-up.png').getQPixmap()
        QtGui.QApplication.style().drawItemPixmap(painter, rect, 1, icon)
        fontColor.setRgb(0, 255, 0)
    else:
      icon = Icon('tango/16x16/actions/go-down-red.png').getQPixmap()
      QtGui.QApplication.style().drawItemPixmap(painter, rect, 1, icon)
      fontColor.setRgb(255, 0, 0)

    value_str = str(value)
    if self.unicode_format != None:
        value_str = self.unicode_format(value)

    fontColor = fontColor.darker()
    painter.setPen(fontColor.toRgb())
    rect = QtCore.QRect(option.rect.left()+23, option.rect.top(), option.rect.width()-23, option.rect.height())
    painter.drawText(rect.x()+2,
                     rect.y(),
                     rect.width()-4,
                     rect.height(),
                     Qt.AlignVCenter | Qt.AlignRight,
                     value_str)
    painter.restore()
    
_registered_delegates_[editors.ColoredFloatEditor] = ColoredFloatColumnDelegate

class Many2OneColumnDelegate(QtGui.QItemDelegate):
  """Custom delegate for many 2 one relations"""

  def __init__(self, admin, embedded=False, parent=None, **kwargs):
    logger.debug('create many2onecolumn delegate')
    assert admin != None
    super(Many2OneColumnDelegate, self).__init__(parent)
    self.admin = admin
    self._embedded = embedded
    self._kwargs = kwargs
    self._dummy_editor = editors.Many2OneEditor(self.admin, None)

  def createEditor(self, parent, option, index):
    if self._embedded:
      editor = editors.EmbeddedMany2OneEditor(self.admin, parent)
    else:
      editor = editors.Many2OneEditor(self.admin, parent)
    self.connect(editor, QtCore.SIGNAL('editingFinished()'), self.commitAndCloseEditor)
    return editor

  def setEditorData(self, editor, index):
    editor.setEntity(create_constant_function(index.data(Qt.EditRole).toPyObject()), propagate=False)

  def setModelData(self, editor, model, index):
    if editor.entity_instance_getter:
      model.setData(index, editor.entity_instance_getter)

  def commitAndCloseEditor(self):
    editor = self.sender()
    self.emit(QtCore.SIGNAL('commitData(QWidget*)'), editor)
    
  def sizeHint(self, option, index):
    return self._dummy_editor.sizeHint()    
  
_registered_delegates_[editors.Many2OneEditor] = Many2OneColumnDelegate


class One2ManyColumnDelegate(QtGui.QItemDelegate):
  """Custom delegate for many 2 one relations"""

  def __init__(self, parent=None, **kwargs):
    logger.debug('create one2manycolumn delegate')
    assert 'admin' in kwargs
    super(One2ManyColumnDelegate, self).__init__(parent)
    self.kwargs = kwargs

  def createEditor(self, parent, option, index):
    logger.debug('create a one2many editor')
    editor = editors.One2ManyEditor(parent=parent, **self.kwargs)
    self.setEditorData(editor, index)
    return editor

  def setEditorData(self, editor, index):
    logger.debug('set one2many editor data')
    model = index.data(Qt.EditRole).toPyObject()
    if model:
      editor.setModel(model)

  def setModelData(self, editor, model, index):
    pass

_registered_delegates_[editors.One2ManyEditor] = One2ManyColumnDelegate


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
    
  def paint(self, painter, option, index):
    painter.save()
    self.drawBackground(painter, option, index)
    checked = index.model().data(index, Qt.EditRole).toBool()
    check_option = QtGui.QStyleOptionButton()
    check_option.rect = option.rect
    check_option.palette = option.palette
    if checked:
      check_option.state = option.state | QtGui.QStyle.State_On
    else:
      check_option.state = option.state | QtGui.QStyle.State_Off
    QtGui.QApplication.style().drawControl(QtGui.QStyle.CE_CheckBox, check_option, painter)
    painter.restore()

_registered_delegates_[QtGui.QCheckBox] = BoolColumnDelegate


class ImageColumnDelegate(QtGui.QItemDelegate):
    
  def createEditor(self, parent, option, index):
    editor = editors.ImageEditor(parent)
    self.connect(editor, 
                 QtCore.SIGNAL('editingFinished()'),
                 self.commitAndCloseEditor)
    return editor

  def setEditorData(self, editor, index):
    s = StringIO.StringIO()
    data = index.data(Qt.EditRole).toPyObject()
    if data:
      editor.image = data.image
      data = data.image.copy()
      data.thumbnail((100, 100))
      data.save(s, 'png')
      s.seek(0)
      pixmap = QtGui.QPixmap()
      pixmap.loadFromData(s.read())
      s.close()
      editor.setPixmap(pixmap)
      editor.setModified(False)
    else:
      #@todo: clear pixmap
      editor.clearFirstImage()

  def commitAndCloseEditor(self):
    editor = self.sender()
    self.emit(QtCore.SIGNAL('commitData(QWidget*)'), editor)
    #self.emit(QtCore.SIGNAL('closeEditor(QWidget*)'), editor)
    
  def setModelData(self, editor, model, index):
    if editor.isModified():
      model.setData(index, 
                    create_constant_function(
                      camelot.types.StoredImage(editor.image)))
      editor.setModified(True)
  
_registered_delegates_[editors.ImageEditor] = ImageColumnDelegate


class RichTextColumnDelegate(QtGui.QItemDelegate):
  def __init__(self, parent = None, **kwargs):
    super(RichTextColumnDelegate, self).__init__(parent)
    self.kwargs = kwargs
    
  def createEditor(self, parent, option, index):
    editor = editors.RichTextEditor(parent, **self.kwargs)
    self.connect(editor, QtCore.SIGNAL('editingFinished()'), self.commitAndCloseEditor)
    return editor

  def commitAndCloseEditor(self):
    editor = self.sender()
    self.emit(QtCore.SIGNAL('commitData(QWidget*)'), editor)
    
  def setEditorData(self, editor, index):
    html = index.model().data(index, Qt.EditRole).toString()
    if html:
      editor.setHtml(html)
    else:
      editor.clear()

  def setModelData(self, editor, model, index):
    model.setData(index, create_constant_function(unicode(editor.toHtml())))

_registered_delegates_[editors.RichTextEditor] = RichTextColumnDelegate


class ComboBoxColumnDelegate(QtGui.QItemDelegate):
  def __init__(self, choices, parent=None, **kwargs):
    super(ComboBoxColumnDelegate, self).__init__(parent)
    self.choices = choices
    
  def qvariantToPython(self, variant):
    if variant.canConvert(QtCore.QVariant.String):
      return unicode(variant.toString())
    else:
      return variant.toPyObject()
          
  def createEditor(self, parent, option, index):
    editor = QtGui.QComboBox(parent)
    
    def create_choices_getter(model, row):
      
      def getChoices():
        return list(self.choices(model._get_object(row)))
      
      return getChoices
      
    def create_choices_setter(editor):
      
      def setChoices(choices):
        allready_in_combobox = dict((self.qvariantToPython(editor.itemData(i)),i) for i in range(editor.count()))
        for i,(value,name) in enumerate(choices):
          if value not in allready_in_combobox:
            editor.insertItem(i, unicode(name), QtCore.QVariant(value))
          else:
            # the editor data might allready have been set, but its name is still ...,
            # therefor we set the name now correct
            editor.setItemText(i, unicode(name))
          
      return setChoices
        
    get_model_thread().post(create_choices_getter(index.model(), index.row()), create_choices_setter(editor))
    return editor
  
  def setEditorData(self, editor, index):
    data = self.qvariantToPython(index.model().data(index, Qt.EditRole))
    if data!=None:
      for i in range(editor.count()):
        if data == self.qvariantToPython(editor.itemData(i)):
          editor.setCurrentIndex(i)
          return
      # it might happen, that when we set the editor data, the setChoices method has
      # not happened yes, therefore, we temporary set ... in the text while setting the
      # correct data to the editor
      editor.insertItem(editor.count(), '...', QtCore.QVariant(data))
      editor.setCurrentIndex(editor.count()-1)
    
  def setModelData(self, editor, model, index):
    editor_data = self.qvariantToPython(editor.itemData(editor.currentIndex()))
    model.setData(index, create_constant_function(editor_data))

_registered_delegates_[QtGui.QComboBox] = ComboBoxColumnDelegate
