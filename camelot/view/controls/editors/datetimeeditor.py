#  ============================================================================
#
#  Copyright (C) 2007-2016 Conceptive Engineering bvba.
#  www.conceptive.be / info@conceptive.be
#
#  Redistribution and use in source and binary forms, with or without
#  modification, are permitted provided that the following conditions are met:
#      * Redistributions of source code must retain the above copyright
#        notice, this list of conditions and the following disclaimer.
#      * Redistributions in binary form must reproduce the above copyright
#        notice, this list of conditions and the following disclaimer in the
#        documentation and/or other materials provided with the distribution.
#      * Neither the name of Conceptive Engineering nor the
#        names of its contributors may be used to endorse or promote products
#        derived from this software without specific prior written permission.
#  
#  THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
#  ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
#  WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
#  DISCLAIMED. IN NO EVENT SHALL <COPYRIGHT HOLDER> BE LIABLE FOR ANY
#  DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
#  (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
#  LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
#  ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
#  (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
#  SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#
#  ============================================================================

import datetime



from ....core.qt import QtGui, QtCore, Qt, QtWidgets
from .customeditor import CustomEditor, set_background_color_palette
from .dateeditor import DateEditor
from camelot.view.proxy import ValueLoading

class TimeValidator(QtGui.QValidator):
    
    def __init__(self, parent=None):
        QtGui.QValidator.__init__(self, parent)
    
    def validate(self, input, pos):
        accept, input, pos = self._validate(input, pos)
        return accept, input, pos

    def _validate(self, input, pos):
        input = str(input).strip()
        # allow None
        if len(input)==0:
            return (QtGui.QValidator.State.Acceptable, input, pos)
        parts = input.split(':')
        if len(parts)>2:
            return (QtGui.QValidator.State.Invalid, input, pos)
        # validate individual parts
        for i, part in enumerate(parts):
            if len(part)==0:
                return (QtGui.QValidator.State.Intermediate, input, pos)
            if len(part)<1:
                return (QtGui.QValidator.State.Intermediate, input, pos)
            if len(part)>2:
                return (QtGui.QValidator.State.Invalid, input, pos)
            if not part.isdigit():
                return (QtGui.QValidator.State.Invalid, input, pos)
            if i==1 or (i==0 and len(parts)==1):
                if int(part) > 59:
                    return (QtGui.QValidator.State.Invalid, input, pos)
            elif int(part) > 23:
                return (QtGui.QValidator.State.Invalid, input, pos)
        # validate the number of parts
        if len(parts)<2:
            return (QtGui.QValidator.State.Intermediate, input, pos)
        return (QtGui.QValidator.State.Acceptable, input, pos)
    
class DateTimeEditor(CustomEditor):
    """Widget for editing date and time separated and with popups"""
  
    def __init__(self,
                 parent,
                 editable=True,
                 nullable=True,
                 field_name = 'datetime'):
        CustomEditor.__init__(self, parent)
        self.setSizePolicy( QtWidgets.QSizePolicy.Policy.Preferred,
                            QtWidgets.QSizePolicy.Policy.Fixed )        
        self.setObjectName( field_name )
        import itertools
        self.nullable = nullable

        layout = QtWidgets.QHBoxLayout()
        self.dateedit = DateEditor(self, nullable=nullable)
        self.dateedit.editingFinished.connect( self.editing_finished )
        layout.addWidget(self.dateedit, 1)

        self.timeedit = QtWidgets.QComboBox(self)
        self.timeedit.setEditable(True)
        if not editable:
            self.timeedit.setEnabled(False)
        
        time_entries = [entry
                        for entry in itertools.chain(*(('%02i:00'%i, '%02i:30'%i)
                        for i in range(0,24)))]
        self.timeedit.addItems(time_entries)
        self.timeedit.setValidator(TimeValidator(self))
        self.timeedit.activated.connect( self.editing_finished )
        self.timeedit.lineEdit().editingFinished.connect( self.editing_finished )
        self.timeedit.lineEdit().setPlaceholderText('--:--')
        self.timeedit.setFocusPolicy( Qt.FocusPolicy.StrongFocus )

        layout.addWidget(self.timeedit, 1)
        # focus proxy is needed to activate the editor with a single click
        self.setFocusProxy(self.dateedit)
        self.setLayout(layout)
        layout.setContentsMargins( 0, 0, 0, 0)
        layout.setSpacing(0)

    @QtCore.qt_slot(str)
    @QtCore.qt_slot(int)
    @QtCore.qt_slot()
    def editing_finished(self, _arg=None):
        if self.time() and self.date():
            self.editingFinished.emit()
        
    def get_value(self):
        time_value = self.time()
        date_value = self.date()
        if time_value not in (None, ValueLoading) and date_value not in (None, ValueLoading):
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
            assert isinstance(value, QtCore.QDateTime)
            self.dateedit.set_value(value.date())
            self.timeedit.lineEdit().setText('%02i:%02i'%(value.time().hour(), value.time().minute()))
        else:
            self.dateedit.set_value(None)
            self.timeedit.lineEdit().setText('')
      
    def date(self):
        return self.dateedit.get_value()
    
    def time(self):
        text = str(self.timeedit.currentText())
        if not len(text):
            return None
        parts = text.split(':')
        return QtCore.QTime(int(parts[0]), int(parts[1]))
      
    def set_enabled(self, editable=True):
        self.timeedit.setEnabled(editable)
        self.dateedit.setEnabled(editable)

    def set_tooltip(self, tooltip):
        super().set_tooltip(tooltip)
        line_edit = self.findChild(QtWidgets.QWidget, 'date_line_edit')
        if line_edit is not None:
            line_edit.setToolTip(str(tooltip or ''))

    def set_editable(self, editable):
        line_edit = self.findChild(QtWidgets.QWidget, 'date_line_edit')
        if line_edit is not None:
            self.set_enabled(editable)

    def set_background_color(self, background_color):
        self.dateedit.set_background_color( background_color )
        set_background_color_palette( self.timeedit.lineEdit(), background_color )




