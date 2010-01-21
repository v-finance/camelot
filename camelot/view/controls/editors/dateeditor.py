
import datetime

from PyQt4 import QtGui, QtCore
from PyQt4.QtCore import Qt

from customeditor import CustomEditor, editingFinished
from camelot.core import constants
from camelot.view.art import Icon
from camelot.view.utils import local_date_format, date_from_string, ParsingError
from camelot.view.controls.decorated_line_edit import DecoratedLineEdit

class DateEditor(CustomEditor):
    """Widget for editing date values"""
  
    calendar_action_trigger = QtCore.SIGNAL('trigger()')
    
    def __init__(self,
                 parent=None,
                 editable=True,
                 nullable=True,
                 format=constants.camelot_date_format,
                 **kwargs):
        CustomEditor.__init__(self, parent)
        
        self.date_format = local_date_format()
        self.line_edit = DecoratedLineEdit()
        self.line_edit.setAlignment(Qt.AlignRight|Qt.AlignVCenter)
        self.line_edit.set_background_text( QtCore.QDate(2000,1,1).toString(self.date_format) )
            
        calendar_widget_action = QtGui.QWidgetAction(self)
        self.calendar_widget = QtGui.QCalendarWidget()
        self.connect( self.calendar_widget, QtCore.SIGNAL('activated(const QDate&)'), self.calendar_widget_activated)
        self.connect( self.calendar_widget, QtCore.SIGNAL('clicked(const QDate&)'), self.calendar_widget_activated)        
        calendar_widget_action.setDefaultWidget(self.calendar_widget)
        
        special_date_menu = QtGui.QMenu(self)
        self.connect( self, self.calendar_action_trigger, special_date_menu.hide )
        special_date_menu.addAction(calendar_widget_action)
        special_date_menu.addAction('Today')
        special_date_menu.addAction('Far future')
        self.special_date = QtGui.QToolButton(None)
        self.special_date.setIcon(
            Icon('tango/16x16/apps/office-calendar.png').getQIcon())
        self.special_date.setAutoRaise(True)
        self.special_date.setToolTip('Calendar and special dates')
        self.special_date.setMenu(special_date_menu)
        self.special_date.setPopupMode(QtGui.QToolButton.InstantPopup)
        self.special_date.setFixedHeight(self.get_height())
    
        if not editable:
            self.special_date.setEnabled(False)
            self.line_edit.setEnabled(False)
      
        if nullable:
            special_date_menu.addAction('Clear')
      
        self.hlayout = QtGui.QHBoxLayout()
        self.hlayout.addWidget(self.line_edit)
        self.hlayout.addWidget(self.special_date)
    
        self.hlayout.setContentsMargins(0, 0, 0, 0)
        self.hlayout.setMargin(0)
        self.hlayout.setSpacing(0)
    
        self.setContentsMargins(0, 0, 0, 0)
        self.setLayout(self.hlayout)
    
        self.minimum = datetime.date.min
        self.maximum = datetime.date.max
        self.setFocusProxy(self.line_edit)
    
        self.connect(self.line_edit,
                     QtCore.SIGNAL('editingFinished()'),
                     self.editingFinished)
        self.connect(self.line_edit,
                     QtCore.SIGNAL('textEdited(const QString&)'),
                     self.text_edited)
        self.connect(special_date_menu,
                     QtCore.SIGNAL('triggered(QAction*)'),
                     self.setSpecialDate)
    
    def calendar_widget_activated(self, date):
        self.emit(self.calendar_action_trigger)
        self.set_value(date)
        self.emit(editingFinished)
    
    def editingFinished(self):
        self.emit(QtCore.SIGNAL('editingFinished()'))
        
    def focusOutEvent(self, event):
        self.emit(QtCore.SIGNAL('editingFinished()'))
    
    def set_value(self, value):
        value = CustomEditor.set_value(self, value)
        if value:
            qdate = QtCore.QDate(value)
            formatted_date = qdate.toString(self.date_format)
            self.line_edit.set_user_input(formatted_date)
        else:
            self.line_edit.set_user_input('')
      
    def text_edited(self, text ):
        try:
            date_from_string( self.line_edit.user_input() )
            self.line_edit.set_valid(True)
        except ParsingError:
            self.line_edit.set_valid(False)
                    
    def get_value(self):
        try:
            value = date_from_string( self.line_edit.user_input() )
        except ParsingError:
            value = None    
        return CustomEditor.get_value(self) or value 
      
    def set_enabled(self, editable=True):
        self.line_edit.setEnabled(editable)
        self.special_date.setEnabled(editable)
    
    def setSpecialDate(self, action):
        if action.text().compare('Today') == 0:
            self.set_value(datetime.date.today())
        elif action.text().compare('Far future') == 0:
            self.set_value(datetime.date( year = 2400, month = 12, day = 31 ))
        elif action.text().compare('Clear') == 0:
            self.set_value(None)
        self.emit(QtCore.SIGNAL('editingFinished()'))
