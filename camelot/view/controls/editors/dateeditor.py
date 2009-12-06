
import datetime

from PyQt4 import QtGui, QtCore
from PyQt4.QtCore import Qt

from customeditor import CustomEditor
from camelot.core import constants
from camelot.view.art import Icon
from camelot.core.utils import ugettext_lazy as _

class DateEditor(CustomEditor):
    """Widget for editing date values"""
  
    def __init__(self,
                 parent=None,
                 editable=True,
                 nullable=True,
                 format=constants.camelot_date_format,
                 **kwargs):
        CustomEditor.__init__(self, parent)
        self.format = format
        self.qdateedit = QtGui.QDateEdit()
        self.qdateedit.setAlignment(Qt.AlignRight|Qt.AlignVCenter)
        self.qdateedit.setDisplayFormat(QtCore.QString(format))
    
        special_date_menu = QtGui.QMenu(self)
        special_date_menu.addAction('Today')
        special_date_menu.addAction('Last date')
        special_date = QtGui.QToolButton(self)
        special_date.setIcon(
            Icon('tango/16x16/apps/office-calendar.png').getQIcon())
        special_date.setAutoRaise(True)
        special_date.setToolTip('Special dates')
        special_date.setMenu(special_date_menu)
        special_date.setPopupMode(QtGui.QToolButton.InstantPopup)
        special_date.setFixedHeight(self.get_height())
    
        if not editable:
            special_date.setEnabled(False)
            self.qdateedit.setEnabled(False)
            self.qdateedit.setButtonSymbols(QtGui.QAbstractSpinBox.NoButtons)
      
        if nullable:
            special_date_menu.addAction('Clear')
            self.qdateedit.setSpecialValueText('0/0/0')
        else:
            self.qdateedit.setCalendarPopup(True)
      
        self.hlayout = QtGui.QHBoxLayout()
        
        self.hlayout.addWidget(special_date)
        self.special_date = special_date
        self.hlayout.addWidget(self.qdateedit)
    
        self.hlayout.setContentsMargins(0, 0, 0, 0)
        self.hlayout.setMargin(0)
        self.hlayout.setSpacing(0)
    
        self.setContentsMargins(0, 0, 0, 0)
        self.setLayout(self.hlayout)
    
        self.minimum = datetime.date.min
        self.maximum = datetime.date.max
        self.set_date_range()
        
        self.qdateedit.setFocus(Qt.OtherFocusReason)
    
        self.setFocusProxy(self.qdateedit)
    
        self.connect(self.qdateedit,
                     QtCore.SIGNAL('editingFinished()'),
                     self.editingFinished)
        self.connect(special_date_menu,
                     QtCore.SIGNAL('triggered(QAction*)'),
                     self.setSpecialDate)
    
    # TODO: consider using QDate.toPyDate(), PyQt4.1
    @staticmethod
    def _python_to_qt(value):
        return QtCore.QDate(value.year, value.month, value.day)
    
    # TODO: consider using QDate.toPyDate(), PyQt4.1
    @staticmethod
    def _qt_to_python(value):
        return datetime.date(value.year(), value.month(), value.day())
    
    def editingFinished(self):
        self.emit(QtCore.SIGNAL('editingFinished()'))
        
    def focusOutEvent(self, event):
        self.emit(QtCore.SIGNAL('editingFinished()'))
    
    # TODO: consider using QDate.toPyDate(), PyQt4.1
    def set_date_range(self):
        qdate_min = DateEditor._python_to_qt(self.minimum)
        qdate_max = DateEditor._python_to_qt(self.maximum)
        self.qdateedit.setDateRange(qdate_min, qdate_max)
    
    def set_value(self, value):
        value = CustomEditor.set_value(self, value)
        if value:
            newDate = QtCore.QDate()
            newDate.setDate(value.year, value.month, value.day)
            self.qdateedit.setDate(newDate)
        else:
            self.qdateedit.setDate(self.minimumDate())
      
    def get_value(self):
        value = self.qdateedit.date()
        if value == self.minimumDate():
            value = None
        else:
            value = datetime.date(value.year(), value.month(), value.day())    
        return CustomEditor.get_value(self) or value 
      
    def set_enabled(self, editable=True):
        self.qdateedit.setEnabled(editable)
        self.special_date.setEnabled(editable)
  
    def minimumDate(self):
        return self.qdateedit.minimumDate()
    
    def setMinimumDate(self):
        self.qdateedit.setDate(self.minimumDate())
        self.emit(QtCore.SIGNAL('editingFinished()'))
    
    def setSpecialDate(self, action):
        if action.text().compare('Today') == 0:
            self.qdateedit.setDate(QtCore.QDate.currentDate())
        elif action.text().compare('Last date') == 0:
            self.qdateedit.setDate(QtCore.QDate(2400, 12, 31))
        # minimum date is our special value text
        elif action.text().compare('Clear') == 0:
            self.qdateedit.setDate(self.qdateedit.minimumDate())
        self.emit(QtCore.SIGNAL('editingFinished()'))
