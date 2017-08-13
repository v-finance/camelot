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

import six

from ....core.qt import QtCore, QtWidgets, Qt, py_to_variant

from .customeditor import CustomEditor, set_background_color_palette

from ...validator import DateValidator
from camelot.view.art import Icon
from camelot.view.utils import local_date_format, date_from_string, ParsingError
from camelot.view.controls.decorated_line_edit import DecoratedLineEdit
from camelot.core.utils import ugettext as _

class DateEditor(CustomEditor):
    """Widget for editing date values"""

    calendar_action_trigger = QtCore.qt_signal()
    special_date_icon = Icon('tango/16x16/apps/office-calendar.png')
    
    def __init__(self, parent = None,
                       editable = True,
                       nullable = True, 
                       field_name = 'date',
                       validator = DateValidator(),
                       **kwargs):
        CustomEditor.__init__(self, parent)
        self.setSizePolicy( QtWidgets.QSizePolicy.Preferred,
                            QtWidgets.QSizePolicy.Fixed )
        self.setObjectName( field_name )
        self.date_format = local_date_format()
        line_edit = DecoratedLineEdit()
        line_edit.setValidator(validator)
        line_edit.setObjectName('date_line_edit')
        line_edit.set_minimum_width(six.text_type(QtCore.QDate(2000,12,22).toString(self.date_format)))
        line_edit.setPlaceholderText(QtCore.QDate(2000,1,1).toString(self.date_format))

        # The order of creation of this widgets and their parenting
        # seems very sensitive under windows and creates system crashes
        # so don't change this without extensive testing on windows
        special_date_menu = QtWidgets.QMenu(self)
        calendar_widget_action = QtWidgets.QWidgetAction(special_date_menu)
        self.calendar_widget = QtWidgets.QCalendarWidget(special_date_menu)
        self.calendar_widget.activated.connect(self.calendar_widget_activated)
        self.calendar_widget.clicked.connect(self.calendar_widget_activated)
        calendar_widget_action.setDefaultWidget(self.calendar_widget)

        self.calendar_action_trigger.connect( special_date_menu.hide )
        special_date_menu.addAction(calendar_widget_action)
        special_date_menu.addAction(_('Today'))
        special_date_menu.addAction(_('Far future'))
        self.special_date = QtWidgets.QToolButton(self)
        self.special_date.setIcon( self.special_date_icon.getQIcon() )
        self.special_date.setAutoRaise(True)
        self.special_date.setToolTip(_('Calendar and special dates'))
        self.special_date.setMenu(special_date_menu)
        self.special_date.setPopupMode(QtWidgets.QToolButton.InstantPopup)
        self.special_date.setFixedHeight(self.get_height())
        self.special_date.setFocusPolicy(Qt.ClickFocus)
        # end of sensitive part

        if nullable:
            special_date_menu.addAction(_('Clear'))

        self.hlayout = QtWidgets.QHBoxLayout()
        self.hlayout.addWidget(line_edit)
        self.hlayout.addWidget(self.special_date)

        self.hlayout.setContentsMargins(0, 0, 0, 0)
        self.hlayout.setSpacing(0)
        self.hlayout.setAlignment(Qt.AlignRight|Qt.AlignVCenter)
        
        self.setContentsMargins(0, 0, 0, 0)
        self.setLayout(self.hlayout)

        self.minimum = datetime.date.min
        self.maximum = datetime.date.max
        self.setFocusProxy(line_edit)

        line_edit.editingFinished.connect(self.line_edit_finished)
        special_date_menu.triggered.connect(self.set_special_date)

    def calendar_widget_activated(self, date):
        line_edit = self.findChild(QtWidgets.QWidget, 'date_line_edit')
        if line_edit is not None:
            self.calendar_action_trigger.emit()
            self.set_value(date)
            self.editingFinished.emit()
            line_edit.setFocus()

    def line_edit_finished(self):
        self.setProperty( 'value', py_to_variant( self.get_value() ) )
        self.valueChanged.emit()
        self.editingFinished.emit()

    def focusOutEvent(self, event):
        # explicitely set value on focus out to format the date in case
        # it was entered unformatted
        value = self.get_value()
        self.set_value( value )
        self.editingFinished.emit()

    def set_value(self, value):
        value = CustomEditor.set_value(self, value)
        self.setProperty( 'value', py_to_variant( value ) )
        line_edit = self.findChild(QtWidgets.QWidget, 'date_line_edit')
        if line_edit is not None:
            if value:
                qdate = QtCore.QDate(value)
                formatted_date = qdate.toString(self.date_format)
                line_edit.setText(formatted_date)
                self.calendar_widget.setSelectedDate(qdate)
            else:
                line_edit.setText('')
            self.valueChanged.emit()

    def get_value(self):
        line_edit = self.findChild(QtWidgets.QWidget, 'date_line_edit')
        if line_edit is not None:
            try:
                value = date_from_string( six.text_type( line_edit.text() ) )
            except ParsingError:
                value = None
        return CustomEditor.get_value(self) or value

    def set_field_attributes(self, **kwargs):
        super(DateEditor, self).set_field_attributes(**kwargs)
        line_edit = self.findChild(QtWidgets.QWidget, 'date_line_edit')
        if line_edit is not None:
            self.set_enabled(kwargs.get('editable', False))
            line_edit.setToolTip(six.text_type(kwargs.get('tooltip') or ''))

    def set_background_color(self, background_color):
        line_edit = self.findChild(QtWidgets.QWidget, 'date_line_edit')
        if line_edit is not None:
            set_background_color_palette(line_edit, background_color)

    def set_enabled(self, editable=True):
        line_edit = self.findChild(QtWidgets.QWidget, 'date_line_edit')
        if line_edit is not None:
            line_edit.setEnabled(editable) 
        if editable:
            self.special_date.show()
        else:
            self.special_date.hide()

    def set_special_date(self, action):
        line_edit = self.findChild(QtWidgets.QWidget, 'date_line_edit')
        if line_edit is not None:
            if action.text().compare(_('Today')) == 0:
                self.set_value(datetime.date.today())
            elif action.text().compare(_('Far future')) == 0:
                self.set_value(datetime.date( year = 2400, month = 12, day = 31 ))
            elif action.text().compare(_('Clear')) == 0:
                self.set_value(None)
            line_edit.setFocus()
            self.editingFinished.emit()



