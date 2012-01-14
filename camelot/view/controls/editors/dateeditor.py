#  ============================================================================
#
#  Copyright (C) 2007-2012 Conceptive Engineering bvba. All rights reserved.
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

from PyQt4 import QtGui
from PyQt4 import QtCore
from PyQt4.QtCore import Qt

from customeditor import CustomEditor, set_background_color_palette

from camelot.view.art import Icon
from camelot.view.utils import local_date_format, date_from_string, ParsingError
from camelot.view.controls.decorated_line_edit import DecoratedLineEdit
from camelot.core.utils import ugettext as _

class DateEditor(CustomEditor):
    """Widget for editing date values"""

    calendar_action_trigger = QtCore.pyqtSignal()
    special_date_icon = Icon('tango/16x16/apps/office-calendar.png')
    
    def __init__(self, parent = None,
                       editable = True,
                       nullable = True, 
                       field_name = 'date',
                       **kwargs):
        CustomEditor.__init__(self, parent)

        self.setObjectName( field_name )
        self.date_format = local_date_format()
        self.line_edit = DecoratedLineEdit()
        self.line_edit.set_minimum_width( len( self.date_format ) )
        self.line_edit.set_background_text( QtCore.QDate(2000,1,1).toString(self.date_format) )

        # The order of creation of this widgets and their parenting
        # seems very sensitive under windows and creates system crashes
        # so don't change this without extensive testing on windows
        special_date_menu = QtGui.QMenu(self)
        calendar_widget_action = QtGui.QWidgetAction(special_date_menu)
        self.calendar_widget = QtGui.QCalendarWidget(special_date_menu)
        self.calendar_widget.activated.connect(self.calendar_widget_activated)
        self.calendar_widget.clicked.connect(self.calendar_widget_activated)
        calendar_widget_action.setDefaultWidget(self.calendar_widget)

        self.calendar_action_trigger.connect( special_date_menu.hide )
        special_date_menu.addAction(calendar_widget_action)
        special_date_menu.addAction(_('Today'))
        special_date_menu.addAction(_('Far future'))
        self.special_date = QtGui.QToolButton(self)
        self.special_date.setIcon( self.special_date_icon.getQIcon() )
        self.special_date.setAutoRaise(True)
        self.special_date.setToolTip(_('Calendar and special dates'))
        self.special_date.setMenu(special_date_menu)
        self.special_date.setPopupMode(QtGui.QToolButton.InstantPopup)
        self.special_date.setFixedHeight(self.get_height())
        self.special_date.setFocusPolicy(Qt.ClickFocus)
        # end of sensitive part

        if nullable:
            special_date_menu.addAction(_('Clear'))

        self.hlayout = QtGui.QHBoxLayout()
        self.hlayout.addWidget(self.line_edit)
        self.hlayout.addWidget(self.special_date)

        self.hlayout.setContentsMargins(0, 0, 0, 0)
        self.hlayout.setSpacing(0)
        self.hlayout.setAlignment(Qt.AlignRight|Qt.AlignVCenter)
        
        self.setContentsMargins(0, 0, 0, 0)
        self.setLayout(self.hlayout)

        self.minimum = datetime.date.min
        self.maximum = datetime.date.max
        self.setFocusProxy(self.line_edit)

        self.line_edit.editingFinished.connect( self.line_edit_finished )
        self.line_edit.textEdited.connect(self.text_edited)
        special_date_menu.triggered.connect(self.set_special_date)

    def calendar_widget_activated(self, date):
        self.calendar_action_trigger.emit()
        self.set_value(date)
        self.editingFinished.emit()
        self.line_edit.setFocus()

    def line_edit_finished(self):
        self.setProperty( 'value', QtCore.QVariant( self.get_value() ) )
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
        self.setProperty( 'value', QtCore.QVariant( value ) )
        if value:
            qdate = QtCore.QDate(value)
            formatted_date = qdate.toString(self.date_format)
            self.line_edit.set_user_input(formatted_date)
            self.calendar_widget.setSelectedDate(qdate)
        else:
            self.line_edit.set_user_input('')
        self.valueChanged.emit()

    def text_edited(self, text ):
        try:
            date_from_string( self.line_edit.user_input() )
            self.line_edit.set_valid(True)
            self.valueChanged.emit()
        except ParsingError:
            self.line_edit.set_valid(False)

    def get_value(self):
        try:
            value = date_from_string( self.line_edit.user_input() )
        except ParsingError:
            value = None
        return CustomEditor.get_value(self) or value

    def set_field_attributes(self, editable = True,
                                   background_color = None,
                                   tooltip = None, **kwargs):
        self.set_enabled(editable)
        self.set_background_color(background_color)
        self.line_edit.setToolTip(unicode(tooltip or ''))

    def set_background_color(self, background_color):
        set_background_color_palette( self.line_edit, background_color )

    def set_enabled(self, editable=True):
        self.line_edit.setEnabled(editable)
        if editable:
            self.special_date.show()
        else:
            self.special_date.hide()

    def set_special_date(self, action):
        if action.text().compare(_('Today')) == 0:
            self.set_value(datetime.date.today())
        elif action.text().compare(_('Far future')) == 0:
            self.set_value(datetime.date( year = 2400, month = 12, day = 31 ))
        elif action.text().compare(_('Clear')) == 0:
            self.set_value(None)
        self.line_edit.setFocus()
        self.editingFinished.emit()

