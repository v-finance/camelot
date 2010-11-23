#  ============================================================================
#
#  Copyright (C) 2007-2010 Conceptive Engineering bvba. All rights reserved.
#  www.conceptive.be / project-camelot@conceptive.be
#
#  This file is part of the Camelot Library.
#
#  This file may be used under the terms of the GNU General Public
#  License version 2.0 as published by the Free Software Foundation
#  and appearing in the file license.txt included in the packaging of
#  this file.  Please review this information to ensure GNU
#  General Public Licensing requirements will be met.
#
#  If you are unsure which license is appropriate for your use, please
#  visit www.python-camelot.com or contact project-camelot@conceptive.be
#
#  This file is provided AS IS with NO WARRANTY OF ANY KIND, INCLUDING THE
#  WARRANTY OF DESIGN, MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE.
#
#  For use of this library in commercial applications, please contact
#  project-camelot@conceptive.be
#
#  ============================================================================

import datetime

from PyQt4 import QtGui, QtCore

from customeditor import CustomEditor
from camelot.core import constants

class DateTimeEditor(CustomEditor):
    """Widget for editing date and time separated and with popups"""
  
    def __init__(self,
                 parent,
                 editable=True,
                 format=constants.camelot_datetime_format,
                 nullable=True,
                 **kwargs):
        CustomEditor.__init__(self, parent)
        import itertools
        self.nullable = nullable
        dateformat, _timeformat = format.split(' ')
        layout = QtGui.QHBoxLayout()
        self.dateedit = QtGui.QDateEdit(self)
        self.dateedit.setEnabled(editable)
        self.dateedit.setDisplayFormat(dateformat)
        self.dateedit.setCalendarPopup(True)
        self.dateedit.dateChanged.connect( self.editing_finished )
        layout.addWidget(self.dateedit, 1)
            
        class TimeValidator(QtGui.QValidator):
            def __init__(self, parent):
                QtGui.QValidator.__init__(self, parent)
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
        if not editable:
            self.timeedit.setEnabled(False)
        
        time_entries = [entry
                        for entry in itertools.chain(*(('%02i:00'%i, '%02i:30'%i)
                        for i in range(0,24)))]
        self.timeedit.addItems(time_entries)
        self.timeedit.setValidator(TimeValidator(self))
        self.timeedit.currentIndexChanged.connect( self.editing_finished )
        self.timeedit.editTextChanged.connect( self.editing_finished )
    
#    self.timeedit = QtGui.QTimeEdit(self)
#    self.timeedit.setDisplayFormat(timeformat)
#
#    setting the tab order does not seem to work inside a table
#
#    self.dateedit.setTabOrder(self.dateedit, self.timeedit)

#    Completion doesn't seems to work with a QTimeEdit widget
#
#    time_lineedit = self.timeedit.lineEdit()
#    time_completions_model = QtGui.QStringListModel(['00:00', '00:30'], parent)
#    time_completer = QtGui.QCompleter()
#    time_completer.setModel(time_completions_model)
#    time_completer.setCaseSensitivity(Qt.CaseInsensitive)
#    time_completer.setCompletionMode(QtGui.QCompleter.UnfilteredPopupCompletion)
#    time_lineedit.setCompleter(time_completer)

        layout.addWidget(self.timeedit, 1)
        self.setFocusProxy(self.dateedit)
        self.setLayout(layout)
        layout.setMargin(0)
        layout.setSpacing(0)
        layout.addStretch(1)
        
    @QtCore.pyqtSlot(QtCore.QDate)
    @QtCore.pyqtSlot(QtCore.QString)
    @QtCore.pyqtSlot(int)
    def editing_finished(self, _arg):
        if self.time() and self.date():
            self.editingFinished.emit()
        
    def get_value(self):
        time_value = self.time()
        date_value = self.date()
        if time_value!=None and date_value!=None:
            value = datetime.datetime(hour=time_value.hour(),
                                      minute=time_value.minute(),
                                      second=time_value.second(),
                                      year=date_value.year(),
                                      month=date_value.month(),
                                      day=date_value.day())
        else:
            value = None
        return CustomEditor.get_value(self) or value
    
    def set_value(self, value):
        value = CustomEditor.set_value(self, value)
        if value:
            self.dateedit.setDate(QtCore.QDate(value.year, value.month, value.day))
            self.timeedit.lineEdit().setText('%02i:%02i'%(value.hour, value.minute))
        else:
            self.dateedit.setDate(self.dateedit.minimumDate())
            self.timeedit.lineEdit().setText('--:--')
      
    def date(self):
        return self.dateedit.date()
    
    def time(self):
        text = str(self.timeedit.currentText())
        if text=='--:--':
            return None
        parts = text.split(':')
        return QtCore.QTime(int(parts[0]), int(parts[1]))
      
    def set_enabled(self, editable=True):
        self.timeedit.setEnabled(editable)
        self.dateedit.setEnabled(editable)

