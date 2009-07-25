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

"""Camelot includes a number of QT delegates, most of them are used as default delegates
for the various sqlalchemy and camelot field types.

Some delegates take specific arguments into account for their construction.  All :attr:`field_attributes`
specified for a certain field will be propagated towards the constructor of the
delegate.
"""

import logging

logger = logging.getLogger('camelot.view.controls.delegates')

try:
  from PyQt4 import QtGui
  from PyQt4 import QtCore
  from PyQt4.QtCore import Qt
  from PyQt4.QtGui import QItemDelegate
  
  from camelot.view.controls import editors
  from camelot.view.model_thread import get_model_thread

  _not_editable_background_ = QtGui.QColor(235, 233, 237)
  _not_editable_foreground_ = QtGui.QColor(Qt.darkGray)
except:
  #
  # dummy class when QT has not been found, this allows the documentation to be build
  # without qt dependency
  #
  class QItemDelegate(object):
    pass
  
  class editors(object):
    FileEditor = None
  

import datetime

import camelot.types
from camelot.view.art import Icon
from camelot.view.proxy import ValueLoading

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

class DelegateManager(QItemDelegate):
  """Manages custom delegates, should not be used by the application developer"""

  def __init__(self, parent=None, **kwargs):
    QtGui.QItemDelegate.__init__(self, parent)
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

class CustomDelegate(QItemDelegate):
  """Base class for implementing custom delegates.
  
.. attribute:: editor 

class attribute specifies the editor class that should be used
"""
  
  editor = None
  
  def __init__(self, parent=None, editable=True, **kwargs):
    QtGui.QItemDelegate.__init__(self, parent)
    self.editable = editable
    self.kwargs = kwargs
    
  def createEditor(self, parent, option, index):
    editor = self.editor(parent, editable=self.editable, **self.kwargs)
    self.connect(editor, editors.editingFinished, self.commitAndCloseEditor)
    return editor

  def commitAndCloseEditor(self):
    editor = self.sender()
    self.emit(QtCore.SIGNAL('commitData(QWidget*)'), editor)

  def setEditorData(self, editor, index):
    qvariant = index.model().data(index, Qt.EditRole)
    #
    # Conversion from a qvariant to a python object is highly dependent on the
    # version of pyqt that is being used, we'll try to circumvent most problems
    # here and always return nice python objects.
    #
    type = qvariant.type()
    if type==QtCore.QVariant.String:
      value = unicode(qvariant.toString())
    elif type==QtCore.QVariant.Date:
      value = qvariant.toDate()
      value = datetime.date(year=value.year(), month=value.month(), day=value.day())
    elif type==QtCore.QVariant.Int:
      value = int(qvariant.toInt())
    else:
      value = index.model().data(index, Qt.EditRole).toPyObject()
    editor.set_value(value)

  def setModelData(self, editor, model, index):
    model.setData(index, create_constant_function(editor.get_value()))

class FileDelegate(CustomDelegate):
  """Delegate for camelot.types.file fields
 
.. image:: ../_static/file_delegate.png 
"""
  
  editor = editors.FileEditor
  
  def paint(self, painter, option, index):
    self.drawBackground(painter, option, index)
    painter.save()
    if (option.state & QtGui.QStyle.State_Selected):
      painter.fillRect(option.rect, option.palette.highlight())
      painter.setPen(option.palette.highlightedText().color())
    elif not self.editable:
      painter.fillRect(option.rect, _not_editable_background_)
      painter.setPen(_not_editable_foreground_)
    value =  index.model().data(index, Qt.EditRole).toPyObject()
    if value:
      painter.drawText(option.rect.x()+2,
                       option.rect.y(),
                       option.rect.width()-4,
                       option.rect.height(),
                       Qt.AlignVCenter | Qt.AlignLeft,
                       value.verbose_name)
    painter.restore()

    
class StarDelegate(CustomDelegate):
  """Delegate for integer values from (1 to 5)(Rating Delegate)

.. image:: ../_static/rating.png
  
"""
 
  editor = editors.StarEditor

  def __init__(self, parent, editable=True, maximum=5, **kwargs):
    CustomDelegate.__init__(self, parent=parent, editable=editable, maximum=maximum, **kwargs)
    self.maximum = maximum
    
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
    painter.restore()

camelot_maxint = 2147483647
camelot_minint = -2147483648

class IntegerColumnDelegate(CustomDelegate):
  """Custom delegate for integer values"""

  editor = editors.IntegerEditor

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

  def setEditorData(self, editor, index):
    value = index.model().data(index, Qt.EditRole).toInt()[0]
    editor.set_value(value)

#class SliderDelegate(IntegerColumnDelegate):
#  """A delegate for horizontal sliders"""
#  
#  def createEditor(self, parent, option, index):
#    editor = QtGui.QSlider(Qt.Horizontal, parent)
#    editor.setRange(self.minimum, self.maximum)
#    editor.setTickPosition(QtGui.QSlider.TicksBelow)
#    return editor
#  
#  def setModelData(self, editor, model, index):
#    model.setData(index, create_constant_function(editor.value()))  

class PlainTextColumnDelegate(CustomDelegate):
  """Custom delegate for simple string values"""

  editor = editors.TextLineEditor

  def paint(self, painter, option, index):
    if (option.state & QtGui.QStyle.State_Selected):
      QtGui.QItemDelegate.paint(self, painter, option, index)
    elif not self.editable:
      _paint_not_editable(painter, option, index)
    else:
      QtGui.QItemDelegate.paint(self, painter, option, index)

class TextEditColumnDelegate(QItemDelegate):
  """Edit plain text with a QTextEdit widget"""
  
  def __init__(self, parent=None, editable=True, **kwargs):
    QtGui.QItemDelegate.__init__(self, parent)
    self.editable = editable
    
  def createEditor(self, parent, option, index):
    editor = QtGui.QTextEdit(parent)
    return editor

  def setEditorData(self, editor, index):
    value = index.model().data(index, Qt.EditRole).toString()
    editor.setText(value)

  def setModelData(self, editor, model, index):
    model.setData(index, create_constant_function(unicode(editor.toPlainText())))

class IntervalsColumnDelegate(QItemDelegate):
  """Custom delegate for visualizing camelot.container.IntervalsContainer
  data"""

  def __init__(self, parent=None, **kwargs):
    QtGui.QItemDelegate.__init__(self, parent)
    
  def paint(self, painter, option, index):
    painter.save()
    self.drawBackground(painter, option, index)
    intervals = index.model().data(index, Qt.EditRole).toPyObject()
    if intervals and intervals!=ValueLoading:
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
        pen = QtGui.QPen(Qt.white)      
        
    painter.restore()
      
  def createEditor(self, parent, option, index):
    pass
    
  def setEditorData(self, editor, index):
    pass

  def setModelData(self, editor, model, index):
    pass

class ColorColumnDelegate(CustomDelegate):
  """
.. image:: ../_static/color.png
"""
    
  editor = editors.ColorEditor
  
  def paint(self, painter, option, index):
    painter.save()
    self.drawBackground(painter, option, index)
    if (option.state & QtGui.QStyle.State_Selected):
      pass
    elif not self.editable:
      painter.fillRect(option.rect, _not_editable_background_)
    color = index.model().data(index, Qt.EditRole).toPyObject()  
    if color:
      pixmap = QtGui.QPixmap(16, 16)
      qcolor = QtGui.QColor()
      qcolor.setRgb(*color)
      pixmap.fill(qcolor)
      QtGui.QApplication.style().drawItemPixmap(painter, option.rect, Qt.AlignVCenter, pixmap)
    painter.restore()

class TimeColumnDelegate(CustomDelegate):
  
  editor = editors.TimeEditor
  
  def setModelData(self, editor, model, index):
    value = editor.time()
    t = datetime.time(hour=value.hour(), minute=value.minute(), second=value.second())
    model.setData(index, create_constant_function(t))

class DateTimeColumnDelegate(CustomDelegate):
  
  editor = editors.DateTimeEditor
  
  def __init__(self, parent, editable, **kwargs):
    CustomDelegate.__init__(self, parent, editable=editable, **kwargs)
    self._dummy_editor = self.editor(parent, editable=editable, **kwargs)
    
  def sizeHint(self, option, index):
    return self._dummy_editor.sizeHint()
    
class DateColumnDelegate(CustomDelegate):
  """Custom delegate for date values"""

  editor = editors.DateEditor

  def paint(self, painter, option, index):
    myoption = QtGui.QStyleOptionViewItem(option)
    myoption.displayAlignment |= Qt.AlignRight|Qt.AlignVCenter
    QtGui.QItemDelegate.paint(self, painter, myoption, index)

  def sizeHint(self, option, index):
    return editors.DateEditor().sizeHint()

class CodeColumnDelegate(CustomDelegate):
  
  editor = editors.CodeEditor
  
  def __init__(self, parent=None, parts=[], **kwargs):
    CustomDelegate.__init__(self, parent=parent, parts=parts, **kwargs)
    self._dummy_editor = editors.CodeEditor(parent=None, parts=parts)

  def sizeHint(self, option, index):
    return self._dummy_editor.sizeHint() 
    
class VirtualAddressColumnDelegate(CustomDelegate):
  """
.. image:: ../_static/virtualaddress_editor.png
"""

  editor = editors.VirtualAddressEditor

  def paint(self, painter, option, index):
    painter.save()
    self.drawBackground(painter, option, index)
    virtual_address = index.model().data(index, Qt.EditRole).toPyObject()  
    if virtual_address and virtual_address!=ValueLoading and virtual_address[1]:
      painter.drawText(option.rect, Qt.AlignLeft, '%s : %s'%(unicode(virtual_address[0]), unicode(virtual_address[1])))
      rect = option.rect
      rect = QtCore.QRect(rect.width()-19, rect.top()+6, 16, 16)
      if virtual_address[0] == 'email':
        icon = Icon('tango/16x16/apps/internet-mail.png').getQPixmap()
        painter.drawPixmap(rect, icon)
      else:
      #if virtual_adress[0] == 'telephone':
        icon = Icon('tango/16x16/apps/preferences-desktop-sound.png').getQPixmap()
        painter.drawPixmap(rect, icon)
    painter.restore()

class FloatColumnDelegate(CustomDelegate):
  """Custom delegate for float values

 
"""

  editor = editors.FloatEditor
  
  def __init__(self, minimum=-1e15, maximum=1e15, precision=2,
               editable=True, parent=None, **kwargs):
    """
:param precision:  The number of digits after the decimal point displayed.  This defaults
to the precision specified in the definition of the Field.     
"""
    CustomDelegate.__init__(self, parent=parent, editable=editable)
    self.minimum = minimum
    self.maximum = maximum
    self.precision = precision
    self.editable = editable

  def setEditorData(self, editor, index):
    value = index.model().data(index, Qt.EditRole).toDouble()[0]
    editor.set_value(value)

  def setModelData(self, editor, model, index):
    model.setData(index, create_constant_function(editor.get_value()))

class ColoredFloatColumnDelegate(CustomDelegate):
  """Custom delegate for float values, representing them in green when they are
  positive and in red when they are negative."""

  editor = editors.ColoredFloatEditor
  
  def __init__(self, parent=None, minimum=-1e15, maximum=1e15, precision=2,
               editable=True, unicode_format=None, **kwargs):
    CustomDelegate.__init__(self, parent=parent, editable=editable, minimum=minimum, maximum=maximum,
                            precision=precision, unicode_format=unicode_format, **kwargs)
    self.minimum = minimum
    self.maximum = maximum
    self.precision = precision
    self.editable = editable
    self.unicode_format = unicode_format
    
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

class Many2OneColumnDelegate(CustomDelegate):
  """Custom delegate for many 2 one relations
  
.. image:: ../_static/manytoone.png
"""

  def __init__(self, parent=None, admin=None, embedded=False, editable=True, **kwargs):
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
#      self.drawDisplay(painter, option, option.rect, index.data(Qt.DisplayRole).toString())
#    painter.restore()
    
  def createEditor(self, parent, option, index):
    if self._embedded:
      editor = editors.EmbeddedMany2OneEditor(self.admin, parent)
    else:
      editor = editors.Many2OneEditor(self.admin, parent)
    self.connect(editor, QtCore.SIGNAL('editingFinished()'), self.commitAndCloseEditor)
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

class One2ManyColumnDelegate(QItemDelegate):
  """Custom delegate for many 2 one relations

.. image:: ../_static/onetomany.png  
"""

  def __init__(self, parent=None, **kwargs):
    logger.debug('create one2manycolumn delegate')
    assert 'admin' in kwargs
    QtGui.QItemDelegate.__init__(self, parent)
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

class ManyToManyColumnDelegate(One2ManyColumnDelegate):
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

class BoolColumnDelegate(CustomDelegate):
  """Custom delegate for boolean values"""

  editor = editors.BoolEditor
    
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

class ImageColumnDelegate(CustomDelegate):
  """
.. image:: ../_static/image.png
"""
    
  editor = editors.ImageEditor
    
  def setModelData(self, editor, model, index):
    if editor.isModified():
      model.setData(index, 
                    create_constant_function(
                      camelot.types.StoredImage(editor.image)))

class RichTextColumnDelegate(CustomDelegate):
  """
.. image:: ../_static/richtext.png
"""

  editor = editors.RichTextEditor


class OneToManyChoicesDelegate(CustomDelegate):
  """
Display a OneToMany field as a ComboBox, filling the list of choices with the
objects of the target class. 

.. image:: ../_static/enumeration.png   
"""
  
  editor = editors.OneToManyChoicesEditor

class ComboBoxColumnDelegate(CustomDelegate):
  """
.. image:: ../_static/enumeration.png 
"""

  editor = editors.ChoicesEditor
  
  def __init__(self, parent, choices, editable=True, **kwargs):
    CustomDelegate.__init__(self, parent, editable=editable, **kwargs)
    self.choices = choices
              
  def createEditor(self, parent, option, index):
    
    def create_choices_getter(model, row):
      
      def choices_getter():
        return list(self.choices(model._get_object(row)))
      
      return choices_getter
    
    editor = self.editor(parent=parent, editable=self.editable, 
                         choices=create_choices_getter(index.model(), index.row()))
    return editor
