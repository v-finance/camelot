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

"""Editors for various type of values"""
import os
import os.path
import tempfile
import datetime
import logging
logger = logging.getLogger('camelot.view.controls.editors')

import settings

from PyQt4.QtCore import Qt
from PyQt4 import QtGui, QtCore

import camelot.types
from camelot.view.art import Icon
from camelot.view.model_thread import gui_function, model_function
from camelot.view.workspace import get_workspace
from camelot.view.search import create_entity_search_query_decorator

def create_constant_function(constant):
  return lambda:constant

class DateTimeEditor(QtGui.QWidget):
  """Widget for editing date and time separated and with popups"""
  
  def __init__(self, parent, format, nullable=True, **kwargs):
    import itertools
    self.nullable = nullable
    super(QtGui.QWidget, self).__init__(parent)
    dateformat, timeformat = format.split(' ')
    layout = QtGui.QHBoxLayout()
    self.dateedit = QtGui.QDateEdit(self)
    self.dateedit.setDisplayFormat(dateformat)
    self.dateedit.setCalendarPopup(True)
    layout.addWidget(self.dateedit)
    
    class TimeValidator(QtGui.QValidator):
      def __init__(self, parent):
        super(TimeValidator, self).__init__(parent)
      def validate(self, input, pos):
        parts = str(input).split(':')
        if len(parts)!=2:
          return (QtGui.QValidator.Invalid, pos)
        if str(input)=='--:--' and nullable:
          return (QtGui.QValidator.Acceptable, pos)
        for part in parts:
          if not part.isdigit():
            return (QtGui.QValidator.Invalid, pos)          
          if len(part) not in (1,2):
            return (QtGui.QValidator.Intermediate, pos)
        if not int(parts[0]) in range(0,24):
          return (QtGui.QValidator.Invalid, pos)
        if not int(parts[1]) in range(0,60):
          return (QtGui.QValidator.Invalid, pos)        
        return (QtGui.QValidator.Acceptable, pos)
        
    self.timeedit = QtGui.QComboBox(self)
    self.timeedit.setEditable(True)
    time_entries = [entry for entry in itertools.chain(*(('%02i:00'%i, '%02i:30'%i) for i in range(0,24)))]
    self.timeedit.addItems(time_entries)
    self.timeedit.setValidator(TimeValidator(self))
    
#    self.timeedit = QtGui.QTimeEdit(self)
#    self.timeedit.setDisplayFormat(timeformat)
#  
#    setting the tab order does not seem to work inside a table
#
#    self.dateedit.setTabOrder(self.dateedit, self.timeedit)
    
#   
#    Completion doesn't seems to work with a QTimeEdit widget
#
#    time_lineedit = self.timeedit.lineEdit()
#    time_completions_model = QtGui.QStringListModel(['00:00', '00:30'], parent)
#    time_completer = QtGui.QCompleter()
#    time_completer.setModel(time_completions_model)
#    time_completer.setCaseSensitivity(Qt.CaseInsensitive)
#    time_completer.setCompletionMode(QtGui.QCompleter.UnfilteredPopupCompletion)
#    time_lineedit.setCompleter(time_completer)
    
    layout.addWidget(self.timeedit)
    self.setFocusProxy(self.dateedit)
    self.setLayout(layout)
    layout.setMargin(0)
    layout.setSpacing(0)
    layout.addStretch(1)
        
  def setDateTime(self, value):
    if value:
      self.dateedit.setDate(QtCore.QDate(*value[:3]))
      self.timeedit.lineEdit().setText('%02i:%02i'%(value[3], value[4]))
    else:
      self.dateedit.setDate(self.dateedit.minimumDate())
      self.timeedit.lineEdit().setText('--:--')

  def date(self):
    return self.dateedit.date()
        
  def time(self):
    text = str(self.timeedit.lineEdit().text())
    if text=='--:--':
      return None
    parts = text.split(':')
    return QtCore.QTime(int(parts[0]), int(parts[1]))
    
class DateEditor(QtGui.QWidget):
  """Widget for editing date values"""
  def __init__(self, nullable=True, format='dd/MM/yyyy', parent=None):
    super(DateEditor, self).__init__(parent)
    self.format = format
    self.qdateedit = QtGui.QDateEdit(self)
    self.connect(self.qdateedit,
                 QtCore.SIGNAL('editingFinished ()'),
                 self.editingFinished)
    self.qdateedit.setAlignment(Qt.AlignRight|Qt.AlignVCenter)
    self.qdateedit.setDisplayFormat(QtCore.QString(format))
    self.hlayout = QtGui.QHBoxLayout()
    self.hlayout.addWidget(self.qdateedit)

    if nullable:
      nullbutton = QtGui.QToolButton()
      icon = Icon('tango/16x16/places/user-trash.png').getQIcon()
      nullbutton.setIcon(icon)
      nullbutton.setAutoRaise(True)
      self.connect(nullbutton, QtCore.SIGNAL('clicked()'), self.setMinimumDate)
      self.qdateedit.setSpecialValueText('0/0/0')
      self.hlayout.addWidget(nullbutton)
    else:
      self.qdateedit.setCalendarPopup(True)

    self.hlayout.setContentsMargins(0, 0, 0, 0)
    self.hlayout.setMargin(0)
    self.hlayout.setSpacing(0)

    self.setContentsMargins(0, 0, 0, 0)
    self.setLayout(self.hlayout)

    self.minimum = datetime.date.min
    self.maximum = datetime.date.max
    self.set_date_range()

    self.setFocusProxy(self.qdateedit)
    self.setAutoFillBackground(True)

  def _python_to_qt(self, value):
    return QtCore.QDate(value.year, value.month, value.day)

  def _qt_to_python(self, value):
    return datetime.date(value.year(), value.month(), value.day())
  
  def editingFinished(self):
    self.emit(QtCore.SIGNAL('editingFinished()'))
      
  def set_date_range(self):
    qdate_min = self._python_to_qt(self.minimum)
    qdate_max = self._python_to_qt(self.maximum)
    self.qdateedit.setDateRange(qdate_min, qdate_max)

  def date(self):
    return self.qdateedit.date()

  def minimumDate(self):
    return self.qdateedit.minimumDate()

  def setMinimumDate(self):
    self.qdateedit.setDate(self.minimumDate())
    self.emit(QtCore.SIGNAL('editingFinished()'))

  def setDate(self, date):
    self.qdateedit.setDate(date)

class VirtualAddressEditor(QtGui.QWidget):
  def __init__(self, parent=None):
    super(VirtualAddressEditor, self).__init__(parent)
    self.layout = QtGui.QHBoxLayout()
    self.layout.setMargin(0)
    self.combo = QtGui.QComboBox()
    self.combo.addItems(camelot.types.VirtualAddress.virtual_address_types)
    self.layout.addWidget(self.combo)
    self.editor = QtGui.QLineEdit()
    self.layout.addWidget(self.editor)
    
    
    print camelot.types.VirtualAddress.virtual_address_types
    
    
#    if virtual_adress[0] == 'email':
#      icon = Icon('tango/16x16/apps/internet-mail.png').getQPixmap()
#    else:
#      #if virtual_adress[0] == 'telephone':
    icon = Icon('tango/16x16/actions/zero.png').getQPixmap()
#      
    self.label = QtGui.QLabel()
    self.label.setPixmap(icon)
    
    self.connect(self.editor, QtCore.SIGNAL('editingFinished()'), self.editingFinished)
    self.connect(self.combo, QtCore.SIGNAL('currentIndexChanged(int)'), lambda:self.comboIndexChanged())
    self.setLayout(self.layout)
    self.setAutoFillBackground(True);
    
    
  def comboIndexChanged(self):
    print 'comboIndexChanged'
    self.editingFinished()
    
  def setData(self, value):
    if value:
      self.editor.setText(value[1])
      self.combo.setCurrentIndex(camelot.types.VirtualAddress.virtual_address_types.index(value[0]))
      print self.combo.currentText()
      if str(self.combo.currentText()) == 'phone':
        icon = Icon('tango/16x16/devices/phone.png').getQPixmap()
      if str(self.combo.currentText()) == 'fax':
        icon = Icon('tango/16x16/devices/printer.png').getQPixmap()
      if str(self.combo.currentText()) == 'mobile':
        icon = Icon('tango/16x16/devices/mobile.png').getQPixmap()
      if str(self.combo.currentText()) == 'im':
        icon = Icon('tango/16x16/places/instant-messaging.png').getQPixmap()
      if str(self.combo.currentText()) == 'pager':
        icon = Icon('tango/16x16/devices/pager.png').getQPixmap()
        
      if str(self.combo.currentText()) == 'email':
        icon = Icon('tango/16x16/apps/internet-mail.png').getQIcon()
        self.label.deleteLater()
        self.label = QtGui.QToolButton()
        self.label.setFocusPolicy(Qt.StrongFocus)
        self.label.setAutoRaise(True)
        self.label.setAutoFillBackground(True)
        self.label.setIcon(icon)
        self.connect(self.label, QtCore.SIGNAL('clicked()'), lambda:self.mailClick(self.editor.text()))
      else:
        self.label.deleteLater()
        self.label = QtGui.QLabel()
        self.label.setPixmap(icon)
        
      self.layout.addWidget(self.label)
  
  
  
  def getData(self):
    return self.value
  
  
  
  def mailClick(self, adress):
    url = QtCore.QUrl()
    url.setUrl('mailto:'+str(adress)+'?subject=Camelot')
    mailSent = QtGui.QDesktopServices.openUrl(url)
    
    if not mailSent:
      print 'Failed to send Mail.'
    else:
      print 'mail client opened.'
      
    print adress
  
  
  

  def editingFinished(self):
    self.value = []
    self.value.append(str(self.combo.currentText()))
    self.value.append(str(self.editor.text()))
    self.setData(self.value)
    self.label.setFocus()
    self.emit(QtCore.SIGNAL('editingFinished()'))
        

class CodeEditor(QtGui.QWidget):
  def __init__(self, parts=['99', 'AA'], parent=None):
    super(CodeEditor, self).__init__(parent)
    self.setFocusPolicy(Qt.StrongFocus)
    self.parts = parts
    self.part_editors = []
    layout = QtGui.QHBoxLayout()
    #layout.setSpacing(0)
    layout.setMargin(0)

    for part in parts:
      editor = QtGui.QLineEdit()
      editor.setInputMask(part)
      editor.installEventFilter(self)
      self.part_editors.append(editor)
      layout.addWidget(editor)
      self.connect(editor,
                   QtCore.SIGNAL('editingFinished()'),
                   self.editingFinished)

    self.setLayout(layout)
    self.setAutoFillBackground(True);

  def editingFinished(self):
    self.emit(QtCore.SIGNAL('editingFinished()'))

    
class FloatEditor(QtGui.QWidget):
  """Widget for editing a float field, with a calculator"""
    
  def __init__(self, parent, precision, minimum, maximum, editable=True):
    super(FloatEditor, self).__init__(parent)
    action = QtGui.QAction(self)
    action.setShortcut(Qt.Key_F3)
    self.setFocusPolicy(Qt.StrongFocus)
    self.spinBox = QtGui.QDoubleSpinBox(parent)
    self.spinBox.setReadOnly(not editable)
    self.spinBox.setRange(minimum, maximum)
    self.spinBox.setDecimals(precision)
    self.spinBox.setAlignment(Qt.AlignRight|Qt.AlignVCenter)
    self.spinBox.setSingleStep(1.0)
    self.spinBox.addAction(action)
    calculatorButton = QtGui.QToolButton()
    icon = Icon('tango/16x16/apps/accessories-calculator.png').getQIcon()
    calculatorButton.setIcon(icon)
    calculatorButton.setAutoRaise(True)
    
    self.connect(calculatorButton, QtCore.SIGNAL('clicked()'), lambda:self.popupCalculator(self.spinBox.value()))
    self.connect(action, QtCore.SIGNAL('triggered(bool)'), lambda:self.popupCalculator(self.spinBox.value()))
    self.connect(self.spinBox, QtCore.SIGNAL('editingFinished()'), lambda:self.editingFinished(self.spinBox.value()))
    
    self.releaseKeyboard()
    
    layout = QtGui.QHBoxLayout()
    layout.setMargin(0)
    layout.setSpacing(0)
    layout.addWidget(self.spinBox)
    if editable:
      layout.addWidget(calculatorButton)
    
    self.setFocusProxy(self.spinBox)
    
    self.setLayout(layout)

  def setValue(self, value):
    self.spinBox.setValue(value)
    
  def value(self):
    self.spinBox.interpretText()
    value = self.spinBox.value()
    return value
    
  def popupCalculator(self, value):
    from calculator import Calculator
    calculator = Calculator(self)
    calculator.setValue(value)
    self.connect(calculator, QtCore.SIGNAL('calculationFinished'), self.calculationFinished)
    calculator.exec_()
    
  def calculationFinished(self, value):
    self.spinBox.setValue(float(value))
    self.emit(QtCore.SIGNAL('editingFinished()'), value)
    
  def editingFinished(self, value):
    self.emit(QtCore.SIGNAL('editingFinished()'), value)
          
class IntegerEditor(QtGui.QWidget):
  """Widget for editing a float field, with a calculator"""
    
  
  def __init__(self, parent, minimum, maximum, editable):
    super(IntegerEditor, self).__init__(parent)


    action = QtGui.QAction(self)
    action.setShortcut(Qt.Key_F3)
    self.setFocusPolicy(Qt.StrongFocus)
    self.spinBox = QtGui.QDoubleSpinBox(parent)
    self.spinBox.setReadOnly(not editable)
    self.spinBox.setRange(minimum, maximum)
    self.spinBox.setDecimals(0)
    self.spinBox.setAlignment(Qt.AlignRight|Qt.AlignVCenter)
    self.spinBox.setSingleStep(1)
    self.spinBox.addAction(action)
    calculatorButton = QtGui.QToolButton()
    icon = Icon('tango/16x16/apps/accessories-calculator.png').getQIcon()
    calculatorButton.setIcon(icon)
    calculatorButton.setAutoRaise(True)
    
    self.connect(calculatorButton, QtCore.SIGNAL('clicked()'), lambda:self.popupCalculator(self.spinBox.value()))
    self.connect(action, QtCore.SIGNAL('triggered(bool)'), lambda:self.popupCalculator(self.spinBox.value()))
    self.connect(self.spinBox, QtCore.SIGNAL('editingFinished()'), lambda:self.editingFinished(self.spinBox.value()))
    
#    self.releaseKeyboard()
    
    layout = QtGui.QHBoxLayout()
    layout.setMargin(0)
    layout.setSpacing(0)
    layout.addWidget(self.spinBox)
    if editable:
      layout.addWidget(calculatorButton)
    
    self.setFocusProxy(self.spinBox)
    
    self.setLayout(layout)
    


  def setValue(self, value):
    value = str(value).replace(',', '.')
    self.spinBox.setValue(eval(value))
    
    
  def value(self):
    self.spinBox.interpretText()
    value = self.spinBox.value()
    return value
  
    
  def popupCalculator(self, value):
    from calculator import Calculator
    calculator = Calculator(self)
    calculator.setValue(value)
    self.connect(calculator, QtCore.SIGNAL('calculationFinished'), self.calculationFinished)
    calculator.exec_()
    
  def calculationFinished(self, value):
    self.spinBox.setValue(float(value))
    self.emit(QtCore.SIGNAL('editingFinished()'), value)
    
  def editingFinished(self, value):
    self.emit(QtCore.SIGNAL('editingFinished()'), value)
    
    

    
    
    
class ColoredFloatEditor(QtGui.QWidget):
  """Widget for editing a float field, with a calculator"""
    
  def __init__(self, parent, precision, minimum, maximum, editable=True):
    super(ColoredFloatEditor, self).__init__(parent)
    action = QtGui.QAction(self)
    action.setShortcut(Qt.Key_F3)
    self.setFocusPolicy(Qt.StrongFocus)
    self.spinBox = QtGui.QDoubleSpinBox(parent)
    self.spinBox.setReadOnly(not editable)
    self.spinBox.setRange(minimum, maximum)
    self.spinBox.setDecimals(precision)
    self.spinBox.setAlignment(Qt.AlignRight|Qt.AlignVCenter)
    self.spinBox.setSingleStep(1.0)
    self.spinBox.addAction(action)
    self.arrow = QtGui.QLabel()
    self.arrow.setPixmap(Icon('tango/16x16/actions/go-up.png').getQPixmap())
    
    self.arrow.setAutoFillBackground(True)
    self.arrow.setMaximumWidth(19)
    
    calculatorButton = QtGui.QToolButton()
    icon = Icon('tango/16x16/apps/accessories-calculator.png').getQIcon()
    calculatorButton.setIcon(icon)
    calculatorButton.setAutoRaise(True)
    
    self.connect(calculatorButton, QtCore.SIGNAL('clicked()'), lambda:self.popupCalculator(self.spinBox.value()))
    self.connect(action, QtCore.SIGNAL('triggered(bool)'), lambda:self.popupCalculator(self.spinBox.value()))
    self.connect(self.spinBox, QtCore.SIGNAL('editingFinished()'), lambda:self.editingFinished(self.spinBox.value()))
    
    self.releaseKeyboard()
    
    layout = QtGui.QHBoxLayout()
    layout.setMargin(0)
    layout.setSpacing(0)
    layout.addSpacing(4)
    layout.addWidget(self.arrow)
    layout.addWidget(self.spinBox)
    if editable:
      layout.addWidget(calculatorButton)
    
    self.setFocusProxy(self.spinBox)
    
    self.setLayout(layout)

  def setValue(self, value):
    self.spinBox.setValue(value)
    if value >= 0:
      self.arrow.setPixmap(Icon('tango/16x16/actions/go-up.png').getQPixmap())
    else:
      self.arrow.setPixmap(Icon('tango/16x16/actions/go-down-red.png').getQPixmap())
    
  def value(self):
    self.spinBox.interpretText()
    value = self.spinBox.value()
    return value
    
  def popupCalculator(self, value):
    from calculator import Calculator
    calculator = Calculator(self)
    calculator.setValue(value)
    self.connect(calculator, QtCore.SIGNAL('calculationFinished'), self.calculationFinished)
    calculator.exec_()
    
  def calculationFinished(self, value):
    self.spinBox.setValue(float(value))
    self.emit(QtCore.SIGNAL('editingFinished()'), value)
    
  def editingFinished(self, value):
    self.emit(QtCore.SIGNAL('editingFinished()'), value)
          


    
class StarEditor(QtGui.QWidget):
  def __init__(self, parent, maximum, editable):
    QtGui.QWidget.__init__(self, parent)
    self.setFocusPolicy(Qt.StrongFocus)
    layout = QtGui.QHBoxLayout(self)
    layout.setMargin(0)
    layout.setSpacing(0)
    self.starIcon = Icon('tango/16x16/status/weather-clear.png').getQIcon()
    self.noStarIcon = Icon('tango/16x16/status/weather-clear-noStar.png').getQIcon()
    self.setAutoFillBackground(True)
    #self.starCount = maximum
    self.starCount = 5
    self.buttons = []
    
    for i in range(self.starCount):
      button = QtGui.QToolButton(self)
      button.setIcon(self.noStarIcon)
      if editable:
        button.setAutoRaise(True)
      else:
        button.setAutoRaise(True)
        button.setDisabled(True)
        
      self.buttons.append(button)
      
    
    def createStarClick(i):
      return lambda:self.starClick(i+1)
    
    for i in range(self.starCount):
      self.connect(self.buttons[i], QtCore.SIGNAL('clicked()'), createStarClick(i))
      
      
    
    for i in range(self.starCount):
      layout.addWidget(self.buttons[i])
      
      
    layout.addStretch()
    self.setLayout(layout)
    
    
    
  def getValue(self):
    return self.stars
    
  def starClick(self, value):
    
    
    if self.stars == value:
      self.stars -= 1
    else:
      self.stars = int(value)
    #print self.stars
   
    for i in range(self.starCount):
      if i+1 <= self.stars:
        self.buttons[i].setIcon(self.starIcon)
      else:
        self.buttons[i].setIcon(self.noStarIcon)
    self.emit(QtCore.SIGNAL('editingFinished()'), self.stars)
        

      
  def setValue(self, value):
    self.stars = int(value)
      
    for i in range(self.starCount):
      if i+1 <= self.stars:
        self.buttons[i].setIcon(self.starIcon)
      else:
        self.buttons[i].setIcon(self.noStarIcon)

class EmbeddedMany2OneEditor(QtGui.QWidget):
  """Widget for editing a many 2 one relation a a form embedded in another
  form.
  """
  
  def __init__(self, admin=None, parent=None, **kwargs):
    assert admin != None
    super(EmbeddedMany2OneEditor, self).__init__(parent)
    self.admin = admin    
    self.layout = QtGui.QHBoxLayout()
    self.entity_instance_getter = None
    self.form = None
    self.setLayout(self.layout)
    self.setEntity(lambda:None, propagate = False)

  def setEntity(self, entity_instance_getter, propagate=True):
    
    def create_instance_getter(entity_instance):
      return lambda:entity_instance
    
    def set_entity_instance():
      entity = entity_instance_getter()
      if entity:
        self.entity_instance_getter = create_instance_getter(entity)
      else:
        self.entity_instance_getter = create_instance_getter(self.admin.entity())
    
    def update_form(existing_entity):
      if self.form:
        self.form.deleteLater()
        self.layout.removeWidget(self.form)

      from camelot.view.proxy.collection_proxy import CollectionProxy
 
      def create_collection_getter(instance_getter):
        return lambda:[instance_getter()]
        
      model = CollectionProxy(self.admin,
                              create_collection_getter(self.entity_instance_getter),
                              self.admin.getFields)
      self.form = self.admin.createFormView('', model, 0, self)
      self.layout.addWidget(self.form)
      if propagate:
        self.emit(QtCore.SIGNAL('editingFinished()'))
          
    self.admin.mt.post(set_entity_instance, update_form)
  

class Many2OneEditor(QtGui.QWidget):
  """Widget for editing many 2 one relations
  """
  
  class CompletionsModel(QtCore.QAbstractListModel):
    def __init__(self, parent=None):
      super(Many2OneEditor.CompletionsModel, self).__init__(parent)
      self._completions = []
    
    def setCompletions(self, completions):
      self._completions = completions
      self.emit(QtCore.SIGNAL('layoutChanged()'))
        
    def data(self, index, role):
      if role==Qt.DisplayRole:
        return QtCore.QVariant(self._completions[index.row()][0])
      elif role==Qt.EditRole:
        return QtCore.QVariant(self._completions[index.row()][1])
      return QtCore.QVariant()
        
    def rowCount(self, index=None):
      return len(self._completions)
    
    def columnCount(self, index=None):
      return 1
      
  def __init__(self, entity_admin=None, parent=None, **kwargs):
    """@param entity_admin : The Admin interface for the object on the one side of
       the relation"""    
    super(Many2OneEditor, self).__init__(parent)
    self.admin = entity_admin
    self.entity_instance_getter = None
    self._entity_representation = ''
    self.entity_set = False
    self.layout = QtGui.QHBoxLayout()
    self.layout.setSpacing(0)
    self.layout.setMargin(0)

    # Search button
    self.search_button = QtGui.QToolButton()
    self.search_button.setFocusPolicy(Qt.ClickFocus)
    icon = Icon('tango/16x16/actions/edit-clear.png').getQIcon()
    self.search_button.setIcon(icon)
    self.search_button.setAutoRaise(True)
    self.connect(self.search_button,
                 QtCore.SIGNAL('clicked()'),
                 self.searchButtonClicked)

    # Open button
    self.open_button = QtGui.QToolButton()
    self.open_button.setFocusPolicy(Qt.ClickFocus)
    icon = Icon('tango/16x16/actions/document-new.png').getQIcon()
    self.open_button.setIcon(icon)
    self.connect(self.open_button,
                 QtCore.SIGNAL('clicked()'),
                 self.openButtonClicked)
    self.open_button.setAutoRaise(True)  

    # Search input
    self.search_input = QtGui.QLineEdit(self)
    self.setFocusProxy(self.search_input)
    #self.search_input.setReadOnly(True)
    #self.connect(self.search_input, QtCore.SIGNAL('returnPressed()'), self.returnPressed)
    self.connect(self.search_input, QtCore.SIGNAL('textEdited(const QString&)'), self.textEdited)
    # suppose garbage was entered, we need to refresh the content
    self.connect(self.search_input, QtCore.SIGNAL('editingFinished()'), self.editingFinished)
    
    self.completer = QtGui.QCompleter()
    self.completions_model = self.CompletionsModel(self.completer)
    self.completer.setModel(self.completions_model)
    self.completer.setCaseSensitivity(Qt.CaseInsensitive)
    self.completer.setCompletionMode(QtGui.QCompleter.UnfilteredPopupCompletion)
    self.connect(self.completer, QtCore.SIGNAL('activated(const QModelIndex&)'), self.completionActivated)
    self.search_input.setCompleter(self.completer)
    # Setup layout
    self.layout.addWidget(self.search_input)
    self.layout.addWidget(self.search_button)
    self.layout.addWidget(self.open_button)
    self.setLayout(self.layout)
    self.setAutoFillBackground(True);
    
  def textEdited(self, text):
    
    def create_search_completion(text):
      return lambda: self.search_completions(text)
    
    self.admin.mt.post(create_search_completion(unicode(text)), self.display_search_completions)
    self.completer.complete()
    
  @model_function
  def search_completions(self, text):
    """Search for object that match text, to fill the list of completions

    @return: a list of tuples of (object_representation, object_getter)
    """
    search_decorator = create_entity_search_query_decorator(self.admin, text)
    return [(unicode(e),create_constant_function(e))
            for e in search_decorator(self.admin.entity.query).limit(20)]
  
  @gui_function
  def display_search_completions(self, completions):
    self.completions_model.setCompletions(completions)
    self.completer.complete()
  
  def completionActivated(self, index):
    object_getter = index.data(Qt.EditRole)
    self.setEntity(object_getter.toPyObject())
    
  def openButtonClicked(self):
    if self.entity_set:
      return self.createFormView()
    else:
      return self.createNew()
    
  def returnPressed(self):
    if not self.entity_set:
      self.createSelectView()
      
  def searchButtonClicked(self):
    if self.entity_set:
      self.setEntity(lambda:None)
    else:
      self.createSelectView()
      
  def trashButtonClicked(self):
    self.setEntity(lambda:None)
    
  @gui_function
  def createNew(self):
    
    @model_function
    def get_has_subclasses():
      return len(self.admin.getSubclasses())
    
    @gui_function
    def show_new_view(has_subclasses):
      selected = QtGui.QDialog.Accepted
      admin = self.admin
      if has_subclasses:
        from camelot.view.controls.inheritance import SubclassDialog
        select_subclass = SubclassDialog(self, self.admin)
        select_subclass.setWindowTitle('Select')
        selected = select_subclass.exec_()
        admin = select_subclass.selected_subclass
      if selected:
        workspace = get_workspace()
        form = admin.createNewView(workspace)
        workspace.addSubWindow(form)
        self.connect(form, form.entity_created_signal, self.selectEntity)
        form.show()
      
    self.admin.mt.post(get_has_subclasses, show_new_view)
        
  def createFormView(self):
    if self.entity_instance_getter:
      
      def get_admin_and_title():
        object = self.entity_instance_getter()
        admin = self.admin.getSubclassEntityAdmin(object.__class__)
        return admin, '%s : %s'%(admin.name,unicode(object))
      
      def show_form_view(admin_and_title):
        admin, title = admin_and_title
        
        def create_collection_getter(instance_getter):
          return lambda:[instance_getter()]
        
        from camelot.view.proxy.collection_proxy import CollectionProxy
  
        workspace = get_workspace()  
        model = CollectionProxy(admin,
                          create_collection_getter(self.entity_instance_getter),
                          admin.getFields)
        sig = 'dataChanged(const QModelIndex &, const QModelIndex &)'
        self.connect(model, QtCore.SIGNAL(sig), self.dataChanged)        
        form = admin.createFormView(title, model, 0, workspace)
        workspace.addSubWindow(form)
        form.show()
        
      self.admin.mt.post(get_admin_and_title, show_form_view)
    
  def dataChanged(self, index1, index2):
    self.setEntity(self.entity_instance_getter, False)
    
  def editingFinished(self):
    self.search_input.setText(self._entity_representation)
    
  def setEntity(self, entity_instance_getter, propagate=True):
    
    def create_instance_getter(entity_instance):
      return lambda:entity_instance
    
    def get_instance_represenation():
      """Get a representation of the instance

      @return: (unicode, pk) its unicode representation and its primary key 
      or ('', False) if the instance was None
      """
      entity = entity_instance_getter()
      self.entity_instance_getter = create_instance_getter(entity)
      if entity and hasattr(entity, 'id'):
        return (unicode(entity), entity.id)
      elif entity:
        return (unicode(entity), False)
      return ('', False)
    
    def set_instance_represenation(representation):
      """Update the gui"""
      desc, pk = representation
      self._entity_representation = desc
      self.search_input.setText(desc)
      if pk != False:
        icon = Icon('tango/16x16/places/folder.png').getQIcon()
        self.open_button.setIcon(icon)
        icon = Icon('tango/16x16/actions/edit-clear.png').getQIcon()
        self.search_button.setIcon(icon)
        self.entity_set = True
        #self.search_input.setReadOnly(True)
      else:
        icon = Icon('tango/16x16/actions/document-new.png').getQIcon()
        self.open_button.setIcon(icon)
        icon = Icon('tango/16x16/actions/system-search.png').getQIcon()
        self.search_button.setIcon(icon)
        self.entity_set = False
        #self.search_input.setReadOnly(False)
      if propagate:
        self.emit(QtCore.SIGNAL('editingFinished()'))
      
    self.admin.mt.post(get_instance_represenation, set_instance_represenation)
    
  def createSelectView(self):
    
    search_text = unicode(self.search_input.text())
    admin = self.admin
    query = self.admin.entity.query
    
    class SelectDialog(QtGui.QDialog):
      def __init__(self, parent):
        super(SelectDialog, self).__init__(parent)
        self.entity_selected_signal = QtCore.SIGNAL("entity_selected")
        layout = QtGui.QVBoxLayout()
        layout.setMargin(0)
        layout.setSpacing(0)
        self.setWindowTitle('Select %s'%admin.getName())
        self.select = admin.createSelectView(query, parent=parent, search_text=search_text)
        layout.addWidget(self.select)
        self.setLayout(layout)
        self.connect(self.select, self.select.entity_selected_signal, self.selectEntity)
      def selectEntity(self, entity_instance_getter):
        self.emit(self.entity_selected_signal, entity_instance_getter)
        self.close()
        
    selectDialog = SelectDialog(self)
    self.connect(selectDialog, selectDialog.entity_selected_signal, self.selectEntity)
    selectDialog.exec_()
    
  def selectEntity(self, entity_instance_getter):
    self.setEntity(entity_instance_getter)

class One2ManyEditor(QtGui.QWidget):
  def __init__(self, admin=None, parent=None, create_inline=False, **kw):
    """@param admin: the Admin interface for the objects on the one side of
    the relation  

    @param create_inline: if False, then a new entity will be created within a
    new window, if True, it will be created inline
                        
    after creating the editor, setEntityInstance needs to be called to set the
    actual data to the editor
    """
    QtGui.QWidget.__init__(self, parent)
    layout = QtGui.QHBoxLayout()
    layout.setContentsMargins(0, 0, 0, 0)
    #
    # Setup table
    #
    from tableview import QueryTable
    # parent set by layout manager
    self.table = QueryTable()
    layout.setSizeConstraint(QtGui.QLayout.SetNoConstraint)
    layout.addWidget(self.table) 
    self.setSizePolicy(QtGui.QSizePolicy.Expanding,
                       QtGui.QSizePolicy.Expanding)
    self.connect(self.table.verticalHeader(),
                 QtCore.SIGNAL('sectionClicked(int)'),
                 self.createFormForIndex)
    self.admin = admin
    self.create_inline = create_inline
    #
    # Setup buttons
    #
    button_layout = QtGui.QVBoxLayout()
    button_layout.setSpacing(0)
    delete_button = QtGui.QToolButton()
    icon = Icon('tango/16x16/places/user-trash.png').getQIcon()
    delete_button.setIcon(icon)
    delete_button.setAutoRaise(True)
    self.connect(delete_button,
                 QtCore.SIGNAL('clicked()'),
                 self.deleteSelectedRows)
    add_button = QtGui.QToolButton()
    icon = Icon('tango/16x16/actions/document-new.png').getQIcon()
    add_button.setIcon(icon)
    add_button.setAutoRaise(True)
    self.connect(add_button, QtCore.SIGNAL('clicked()'), self.newRow)
    button_layout.addStretch()
    button_layout.addWidget(add_button)
    button_layout.addWidget(delete_button)
    layout.addLayout(button_layout)
    self.setLayout(layout)
    self.model = None
  
  def setModel(self, model):
    self.model = model
    self.table.setModel(model)
    
    def create_fill_model_cache(model):
      def fill_model_cache():
        model._extend_cache(0, 10)
        
      return fill_model_cache
    
    def create_delegate_updater(model):
      def update_delegates(*args):
        self.table.setItemDelegate(model.getItemDelegate())
        for i in range(self.model.columnCount()):
          self.table.setColumnWidth(i, max(self.model.headerData(i, Qt.Horizontal, Qt.SizeHintRole).toSize().width(), self.table.columnWidth(i)))
          
      return update_delegates
      
    self.admin.mt.post(create_fill_model_cache(model),
                       create_delegate_updater(model))
    
  def newRow(self):
    workspace = get_workspace()

    if self.create_inline:
      
      @model_function
      def create():
        o = self.admin.entity()
        self.model.insertEntityInstance(0,o)
        self.admin.setDefaults(o)
        
      self.admin.mt.post(create)
        
    else:
      prependentity = lambda o: self.model.insertEntityInstance(0, o)
      removeentity = lambda o: self.model.removeEntityInstance(o)
      form = self.admin.createNewView(workspace,
                                      oncreate=prependentity,
                                      onexpunge=removeentity)
      workspace.addSubWindow(form)
      form.show()
    
  def deleteSelectedRows(self):
    """Delete the selected rows in this tableview"""
    logger.debug('delete selected rows called')
    for row in set(map(lambda x: x.row(), self.table.selectedIndexes())):
      self.model.removeRow(row)
          
  def createFormForIndex(self, index):
    from camelot.view.proxy.collection_proxy import CollectionProxy
    model = CollectionProxy(self.admin,
                            self.model.collection_getter,
                            self.admin.getFields,
                            max_number_of_rows=1,
                            edits=None)
    title = self.admin.getName()
    form = self.admin.createFormView(title, model, index, get_workspace())
    get_workspace().addSubWindow(form)
    form.show()


try:
  from PIL import Image as PILImage
except:
  import Image as PILImage

filter = """Image files (*.bmp *.jpg *.jpeg *.mng *.png *.pbm *.pgm """\
         """*.ppm *.tiff *.xbm *.xpm) 
All files (*)"""


class ImageEditor(QtGui.QWidget):
  def __init__(self, parent=None):
    QtGui.QWidget.__init__(self, parent)
    self._modified = False
    self.image = None 
    self.layout = QtGui.QHBoxLayout()
    #
    # Setup label
    #
    self.label = QtGui.QLabel(parent)
    self.layout.addWidget(self.label)
    self.label.setAcceptDrops(True)
    # self.draw_border()
    self.label.setAlignment(Qt.AlignHCenter|Qt.AlignVCenter)
    self.label.__class__.dragEnterEvent = self.dragEnterEvent
    self.label.__class__.dragMoveEvent = self.dragEnterEvent
    self.label.__class__.dropEvent = self.dropEvent
    #
    # Setup buttons
    #
    button_layout = QtGui.QVBoxLayout()
    button_layout.setSpacing(0)
    button_layout.setMargin(0)

    file_button = QtGui.QToolButton()
    icon = Icon('tango/16x16/actions/document-new.png').getQIcon()
    file_button.setIcon(icon)
    file_button.setAutoRaise(True)
    file_button.setToolTip('Select image')
    self.connect(file_button, QtCore.SIGNAL('clicked()'), self.openFileDialog)
    
    app_button = QtGui.QToolButton()
    icon = Icon('tango/16x16/status/folder-open.png').getQIcon()
    app_button.setIcon(icon)
    app_button.setAutoRaise(True)
    app_button.setToolTip('Open image')
    self.connect(app_button, QtCore.SIGNAL('clicked()'), self.openInApp)
    
    clear_button = QtGui.QToolButton()
    icon = Icon('tango/16x16/places/user-trash.png').getQIcon()
    clear_button.setIcon(icon)
    clear_button.setToolTip('Clear image')
    clear_button.setAutoRaise(True)
    self.connect(clear_button, QtCore.SIGNAL('clicked()'), self.clearImage)

    vspacerItem = QtGui.QSpacerItem(20,
                                    20,
                                    QtGui.QSizePolicy.Minimum,
                                    QtGui.QSizePolicy.Expanding)
    
    button_layout.addItem(vspacerItem)
    button_layout.addWidget(file_button)      
    button_layout.addWidget(app_button)
    button_layout.addWidget(clear_button)    

    self.layout.addLayout(button_layout)
    
    hspacerItem = QtGui.QSpacerItem(20,
                                    20,
                                    QtGui.QSizePolicy.Expanding,
                                    QtGui.QSizePolicy.Minimum)
    self.layout.addItem(hspacerItem)
    self.setLayout(self.layout)
    #
    # Image
    #
    self.dummy_image = Icon('tango/32x32/apps/help-browser.png').fullpath()
    if self.image is None:
      testImage = QtGui.QImage(self.dummy_image)
      if not testImage.isNull():
        fp = open(self.dummy_image, 'rb')
        self.image = PILImage.open(fp)
        self.setPixmap(QtGui.QPixmap(self.dummy_image))

  def isModified(self):
    return self._modified

  def setModified(self, modified):
    self._modified = modified

  #
  # Drag & Drop
  #
  def dragEnterEvent(self, event):
    event.acceptProposedAction()

  def dragMoveEvent(self, event):
    event.acceptProposedAction()

  def dropEvent(self, event):
    if event.mimeData().hasUrls():
      url = event.mimeData().urls()[0]
      filename = url.toLocalFile()
      if filename != '':
        self.pilimage_from_file(filename)

  #
  # Buttons methods
  #
  def clearImage(self):
    self.pilimage_from_file(self.dummy_image)
    self.draw_border()

  def openFileDialog(self):
    filename = QtGui.QFileDialog.getOpenFileName(self, 'Open file', 
                                                 QtCore.QDir.currentPath(),
                                                 filter)
    if filename != '':
      self.pilimage_from_file(filename)

  def openInApp(self):
    if self.image != None:
      tmpfp, tmpfile = tempfile.mkstemp(suffix='.png')
      self.image.save(os.fdopen(tmpfp, 'wb'), 'png')
      QtGui.QDesktopServices.openUrl(QtCore.QUrl.fromLocalFile(tmpfile))

  #
  # Utils methods
  #
  def pilimage_from_file(self, filepath):
    testImage = QtGui.QImage(filepath)
    if not testImage.isNull():
      fp = open(filepath, 'rb')
      self.image = PILImage.open(fp)
      self._modified = True
      self.emit(QtCore.SIGNAL('editingFinished()'))
  
  def draw_border(self):
    self.label.setFrameShape(QtGui.QFrame.Box)
    self.label.setFrameShadow(QtGui.QFrame.Plain)
    self.label.setLineWidth(1)
    self.label.setFixedSize(100, 100)
   
  def setPixmap(self, pixmap):
    self.label.setPixmap(pixmap)      
    self.draw_border()

  def clearFirstImage(self):
    testImage = QtGui.QImage(self.dummy_image)
    if not testImage.isNull():
      fp = open(self.dummy_image, 'rb')
      self.image = PILImage.open(fp)
    self.draw_border()


class ColorEditor(QtGui.QWidget):
  
  def __init__(self, parent=None, **kwargs):
    QtGui.QWidget.__init__(self, parent)
    layout = QtGui.QVBoxLayout(self)
    layout.setSpacing(0)
    layout.setMargin(0)
    self.color_button = QtGui.QPushButton(parent)
    self.color_button.setMaximumSize(QtCore.QSize(20, 20))
    layout.addWidget(self.color_button)
    self.connect(self.color_button,
                 QtCore.SIGNAL('clicked(bool)'),
                 self.buttonClicked)
    self.setLayout(layout)
    self._color = None

  def getColor(self):
    return self._color
  
  def setColor(self, color):
    pixmap = QtGui.QPixmap(16, 16)
    if color:
      pixmap.fill(color)
    else:
      pixmap.fill(Qt.transparent)
    self.color_button.setIcon(QtGui.QIcon(pixmap))
    self._color = color
     
  def buttonClicked(self, raised):
    if self._color:
      color = QtGui.QColorDialog.getColor(self._color)
    else:
      color = QtGui.QColorDialog.getColor()
    if color.isValid() and color!=self._color:
      self.setColor(color)
      self.emit(QtCore.SIGNAL('editingFinished()'))
    
class RichTextEditor(QtGui.QWidget):
  def __init__(self, parent=None, editable=True, **kwargs):
    QtGui.QWidget.__init__(self, parent)
    
    self.layout = QtGui.QVBoxLayout(self)
    self.layout.setSpacing(0)
    self.layout.setMargin(0)
    self.editable = editable

    class CustomTextEdit(QtGui.QTextEdit):
      """A TextEdit editor that sends editingFinished events when the text was changed
      and focus is lost"""
      
      def __init__(self, parent):
        super(CustomTextEdit, self).__init__(parent)
        self._changed = False
        self.connect(self, QtCore.SIGNAL('textChanged()'), self.setTextChanged)

      def focusOutEvent(self, event):
        if self._changed:
          self.emit(QtCore.SIGNAL('editingFinished()'))
    
      def textChanged(self):
        return self._changed
      
      def setTextChanged(self, state=True):
        self._changed = state
        
      def setHtml(self, html):
        QtGui.QTextEdit.setHtml(self, html)
        self._changed = False
        
    self.textedit = CustomTextEdit(self)
    
    self.connect(self.textedit,
                 QtCore.SIGNAL('editingFinished()'),
                 self.editingFinished)
    self.textedit.setAcceptRichText(True)

    if not self.editable:
      self.textedit.setReadOnly(True)
    else:
      #
      # Buttons setup
      #
      self.toolbar = QtGui.QToolBar(self)
      self.toolbar.setContentsMargins(0, 0, 0, 0)
      
      self.bold_button = QtGui.QToolButton(self)
      icon = Icon('tango/16x16/actions/format-text-bold.png').getQIcon()
      self.bold_button.setIcon(icon)
      self.bold_button.setAutoRaise(True)
      self.bold_button.setCheckable(True)
      self.bold_button.setMaximumSize(QtCore.QSize(20, 20))
      self.bold_button.setShortcut(QtGui.QKeySequence('Ctrl+B'))
      self.connect(self.bold_button, QtCore.SIGNAL('clicked()'), self.set_bold)

      self.italic_button = QtGui.QToolButton(self)
      icon = Icon('tango/16x16/actions/format-text-italic.png').getQIcon()
      self.italic_button.setIcon(icon)
      self.italic_button.setAutoRaise(True)
      self.italic_button.setCheckable(True)
      self.italic_button.setMaximumSize(QtCore.QSize(20, 20))
      self.italic_button.setShortcut(QtGui.QKeySequence('Ctrl+I'))
      self.connect(self.italic_button,
                   QtCore.SIGNAL('clicked(bool)'),
                   self.set_italic)
  
      self.underline_button = QtGui.QToolButton(self)
      icon = Icon('tango/16x16/actions/format-text-underline.png').getQIcon()
      self.underline_button.setIcon(icon)
      self.underline_button.setAutoRaise(True)
      self.underline_button.setCheckable(True)
      self.underline_button.setMaximumSize(QtCore.QSize(20, 20))
      self.underline_button.setShortcut(QtGui.QKeySequence('Ctrl+U'))
      self.connect(self.underline_button,
                   QtCore.SIGNAL('clicked(bool)'),
                   self.set_underline)
  
      self.copy_button = QtGui.QToolButton(self)
      icon = Icon('tango/16x16/actions/edit-copy.png').getQIcon()
      self.copy_button.setIcon(icon)
      self.copy_button.setAutoRaise(True)
      self.copy_button.setMaximumSize(QtCore.QSize(20, 20))
      self.connect(self.copy_button,
                   QtCore.SIGNAL('clicked(bool)'),
                   self.textedit.copy)
  
      self.cut_button = QtGui.QToolButton(self)
      icon = Icon('tango/16x16/actions/edit-cut.png').getQIcon()
      self.cut_button.setIcon(icon)
      self.cut_button.setAutoRaise(True)
      self.cut_button.setMaximumSize(QtCore.QSize(20, 20))
      self.connect(self.cut_button,
                   QtCore.SIGNAL('clicked(bool)'),
                   self.textedit.cut)
  
      self.paste_button = QtGui.QToolButton(self)
      icon = Icon('tango/16x16/actions/edit-paste.png').getQIcon()
      self.paste_button.setIcon(icon)
      self.paste_button.setAutoRaise(True)
      self.paste_button.setMaximumSize(QtCore.QSize(20, 20))
      self.connect(self.paste_button,
                   QtCore.SIGNAL('clicked(bool)'),
                   self.textedit.paste)
  
      self.alignleft_button = QtGui.QToolButton(self)
      icon = Icon('tango/16x16/actions/format-justify-left.png').getQIcon()
      self.alignleft_button.setIcon(icon)
      self.alignleft_button.setAutoRaise(True)
      self.alignleft_button.setCheckable(True)
      self.alignleft_button.setMaximumSize(QtCore.QSize(20, 20))
      self.connect(self.alignleft_button,
                   QtCore.SIGNAL('clicked(bool)'),
                   self.set_alignleft)   
  
      self.aligncenter_button = QtGui.QToolButton(self)
      icon = Icon('tango/16x16/actions/format-justify-center.png').getQIcon()
      self.aligncenter_button.setIcon(icon)
      self.aligncenter_button.setAutoRaise(True)
      self.aligncenter_button.setCheckable(True)
      self.aligncenter_button.setMaximumSize(QtCore.QSize(20, 20))
      self.connect(self.aligncenter_button,
                   QtCore.SIGNAL('clicked(bool)'),
                   self.set_aligncenter)
  
      self.alignright_button = QtGui.QToolButton(self)
      icon = Icon('tango/16x16/actions/format-justify-right.png').getQIcon()
      self.alignright_button.setIcon(icon)
      self.alignright_button.setAutoRaise(True)
      self.alignright_button.setCheckable(True)
      self.alignright_button.setMaximumSize(QtCore.QSize(20, 20))
      self.connect(self.alignright_button,
                   QtCore.SIGNAL('clicked(bool)'),
                   self.set_alignright)
  
      self.color_button = QtGui.QToolButton(self)
      self.color_button.setAutoRaise(True)
      self.color_button.setMaximumSize(QtCore.QSize(20, 20))
      self.connect(self.color_button,
                   QtCore.SIGNAL('clicked(bool)'),
                   self.set_color)
 
      self.toolbar.addWidget(self.copy_button)
      self.toolbar.addWidget(self.cut_button)
      self.toolbar.addWidget(self.paste_button)
      self.toolbar.addSeparator()
      self.toolbar.addWidget(self.bold_button)
      self.toolbar.addWidget(self.italic_button)      
      self.toolbar.addWidget(self.underline_button) 
      self.toolbar.addSeparator()
      self.toolbar.addWidget(self.alignleft_button)
      self.toolbar.addWidget(self.aligncenter_button)      
      self.toolbar.addWidget(self.alignright_button)   
      self.toolbar.addSeparator()
      self.toolbar.addWidget(self.color_button)   
      
      #
      # Layout
      #
      self.layout.addWidget(self.toolbar)
    self.layout.addWidget(self.textedit)
   
    self.setLayout(self.layout)
    
    #
    # Format
    #
    self.textedit.setFontWeight(QtGui.QFont.Normal)
    self.textedit.setFontItalic(False)
    self.textedit.setFontUnderline(False)
    self.textedit.setFocus(Qt.OtherFocusReason)
    self.update_alignment()

    if self.editable:
      self.connect(self.textedit, QtCore.SIGNAL('currentCharFormatChanged (const QTextCharFormat&)'), self.update_format)
      self.connect(self.textedit, QtCore.SIGNAL('cursorPositionChanged ()'), self.update_text)
          
  def editingFinished(self):
    if self.textedit.textChanged():
      self.emit(QtCore.SIGNAL('editingFinished()'))
    
  #
  # Button methods
  #
  def set_bold(self):
    if self.bold_button.isChecked():
      self.textedit.setFocus(Qt.OtherFocusReason)
      self.textedit.setFontWeight(QtGui.QFont.Bold)
    else:
      self.textedit.setFocus(Qt.OtherFocusReason)
      self.textedit.setFontWeight(QtGui.QFont.Normal)

  def set_italic(self, bool):
    if bool:
      self.textedit.setFocus(Qt.OtherFocusReason)
      self.textedit.setFontItalic(True)
    else:
      self.textedit.setFocus(Qt.OtherFocusReason)
      self.textedit.setFontItalic(False)

  def set_underline(self, bool):
    if bool:
      self.textedit.setFocus(Qt.OtherFocusReason)
      self.textedit.setFontUnderline(True)
    else:
      self.textedit.setFocus(Qt.OtherFocusReason)
      self.textedit.setFontUnderline(False)


  def set_alignleft(self, bool):
    if bool:
      self.textedit.setFocus(Qt.OtherFocusReason)
      self.textedit.setAlignment(Qt.AlignLeft)
    self.update_alignment(Qt.AlignLeft)

  def set_aligncenter(self, bool):
    if bool:
      self.textedit.setFocus(Qt.OtherFocusReason)
      self.textedit.setAlignment(Qt.AlignCenter)
    self.update_alignment(Qt.AlignCenter)

  def set_alignright(self, bool):
    if bool:
      self.textedit.setFocus(Qt.OtherFocusReason)
      self.textedit.setAlignment(Qt.AlignRight)
    self.update_alignment(Qt.AlignRight)

  def update_alignment(self, al=None):
    if self.editable:
      if al is None:
          al = self.textedit.alignment()
      if al == Qt.AlignLeft:
          self.alignleft_button.setChecked(True)
          self.aligncenter_button.setChecked(False)
          self.alignright_button.setChecked(False)
      elif al == Qt.AlignCenter:
          self.aligncenter_button.setChecked(True)
          self.alignleft_button.setChecked(False)
          self.alignright_button.setChecked(False)
      elif al == Qt.AlignRight:
          self.alignright_button.setChecked(True)
          self.alignleft_button.setChecked(False)
          self.aligncenter_button.setChecked(False)

  def set_color(self):
    color = QtGui.QColorDialog.getColor(self.textedit.textColor())
    if color.isValid():
      self.textedit.setFocus(Qt.OtherFocusReason)
      self.textedit.setTextColor(color)
      pixmap = QtGui.QPixmap(16, 16)
      pixmap.fill(color)
      self.color_button.setIcon(QtGui.QIcon(pixmap))
  
  def update_color(self):
    if self.editable:
      color = self.textedit.textColor()
      pixmap = QtGui.QPixmap(16, 16)
      pixmap.fill(color)
      self.color_button.setIcon(QtGui.QIcon(pixmap))

  def update_format(self, format):
    if self.editable:
      font = format.font()
      self.bold_button.setChecked(font.bold())
      self.italic_button.setChecked(font.italic())
      self.underline_button.setChecked(font.underline())
      self.update_alignment(self.textedit.alignment())

  def update_text(self):
    if self.editable:
      self.update_alignment()
      self.update_color()
  
  #
  # Textedit functions
  #
  def clear(self):
    self.textedit.clear()

  def setHtml(self, html):
    if self.toHtml()!=html:
      self.update_alignment()
      self.textedit.setHtml(html)
      self.update_color()
   
  def toHtml(self):
    from xml.dom import minidom
    tree = minidom.parseString(self.textedit.toHtml())
    return u''.join([node.toxml() for node in tree.getElementsByTagName('html')[0].getElementsByTagName('body')[0].childNodes])
  