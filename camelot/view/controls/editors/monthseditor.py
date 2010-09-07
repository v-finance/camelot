#  ============================================================================
#
#  Copyright (C) 2007-2010 Conceptive Engineering bvba. All rights reserved.
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

from PyQt4.QtGui import QSpinBox
from PyQt4.QtGui import QHBoxLayout
from PyQt4.QtGui import QAbstractSpinBox

from camelot.core.utils import ugettext as _
from camelot.view.controls.editors import CustomEditor
from camelot.view.controls.editors import editingFinished
from camelot.view.controls.editors.customeditor import ValueLoading


class MonthsEditor(CustomEditor):
    """MonthsEditor

    composite months and years editor
    """

    def __init__(self, parent=None, editable=True, **kw):
        CustomEditor.__init__(self, parent)
        self.years = 0
        self.months = 0

        self.years_spinbox = QSpinBox()
        self.months_spinbox = QSpinBox()
        self.years_spinbox.setMinimum(0)
        self.months_spinbox.setMinimum(0)
        self.years_spinbox.setSuffix(_(' years'))
        self.months_spinbox.setSuffix(_(' months'))

        layout = QHBoxLayout()
        layout.addWidget(self.months_spinbox)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.years_spinbox)
        self.setLayout(layout)

        self.years_spinbox.valueChanged.connect(self.value_changed)
        self.months_spinbox.valueChanged.connect(self.value_changed)

    def set_field_attributes(self, editable=True, bgcolor=None, **kw):
        self.set_enabled(editable)
        self.set_background_color(bgcolor)

    def value_changed(self):
        if self.years != self.years_spinbox.value():
            self.years = self.years_spinbox.value()
        if self.months != self.months_spinbox.value():
            self.months = self.months_spinbox.value()
        self.emit(editingFinished)

    def set_enabled(self, editable=True):
        self.years_spinbox.setReadOnly(not editable)
        self.years_spinbox.setEnabled(editable)
        self.months_spinbox.setReadOnly(not editable)
        self.months_spinbox.setEnabled(editable)
        if not editable:
            self.years_spinbox.setButtonSymbols(QAbstractSpinBox.NoButtons)
            self.months_spinbox.setButtonSymbols(QAbstractSpinBox.NoButtons)

    def set_value(self, value):
        # will set privates value_is_none and _value_loading
        CustomEditor.set_value(self, value)

        # TODO: might be better to have accessors for these
        if self._value_loading:
            return

        if self.value_is_none:
            return

        # value comes as a months total
        self.years = int(value / 12)
        self.months = value - self.years
        self.years_spinbox.setValue(self.years)
        self.months_spinbox.setValue(self.months)

    def get_value(self):
        if CustomEditor.get_value(self) is ValueLoading:
            return ValueLoading

        value = (self.years * 12) + self.months
        return value
