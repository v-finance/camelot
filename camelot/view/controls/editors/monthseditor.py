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

from PyQt4.QtCore import Qt
from PyQt4 import QtCore
from PyQt4.QtGui import QHBoxLayout
from PyQt4.QtGui import QAbstractSpinBox

from camelot.core.utils import ugettext as _
from camelot.view.controls.editors import CustomEditor
from camelot.view.controls.editors.customeditor import ValueLoading
from camelot.view.controls.editors.integereditor import CustomDoubleSpinBox

class MonthsEditor(CustomEditor):
    """MonthsEditor

    composite months and years editor
    """

    def __init__(self, parent=None, editable=True, field_name='months', **kw):
        CustomEditor.__init__(self, parent)
        self.setObjectName( field_name )
        self.years_spinbox = CustomDoubleSpinBox()
        self.months_spinbox = CustomDoubleSpinBox()
        self.years_spinbox.setMinimum(0)
        self.years_spinbox.setMaximum(10000)
        self.months_spinbox.setMinimum(0)
        self.months_spinbox.setMaximum(12)
        self.years_spinbox.setSuffix(_(' years'))
        self.months_spinbox.setSuffix(_(' months'))
        
        self.years_spinbox.setDecimals(0)
        self.years_spinbox.setAlignment(Qt.AlignRight|Qt.AlignVCenter)
        self.years_spinbox.setSingleStep(1)
        
        self.months_spinbox.setDecimals(0)
        self.months_spinbox.setAlignment(Qt.AlignRight|Qt.AlignVCenter)
        self.months_spinbox.setSingleStep(1)

        self.years_spinbox.editingFinished.connect( self._spinbox_editing_finished )
        self.months_spinbox.editingFinished.connect( self._spinbox_editing_finished )
        
        layout = QHBoxLayout()
        layout.addWidget(self.years_spinbox)
        layout.addWidget(self.months_spinbox)
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)

    @QtCore.pyqtSlot()
    def _spinbox_editing_finished(self):
        self.editingFinished.emit()
        
    def set_field_attributes(self, editable = True,
                                   background_color = None,
                                   tooltip = None, **kwargs):
        self.set_enabled(editable)
        self.set_background_color(background_color)
        self.years_spinbox.setToolTip(unicode(tooltip or ''))

    def set_enabled(self, editable=True):
        self.years_spinbox.setReadOnly(not editable)
        self.years_spinbox.setEnabled(editable)
        self.months_spinbox.setReadOnly(not editable)
        self.months_spinbox.setEnabled(editable)
        if not editable:
            self.years_spinbox.setButtonSymbols(QAbstractSpinBox.NoButtons)
            self.months_spinbox.setButtonSymbols(QAbstractSpinBox.NoButtons)
        else:
            self.years_spinbox.setButtonSymbols(QAbstractSpinBox.UpDownArrows)
            self.months_spinbox.setButtonSymbols(QAbstractSpinBox.UpDownArrows)            

    def set_value(self, value):
        # will set privates value_is_none and _value_loading
        CustomEditor.set_value(self, value)

        # TODO: might be better to have accessors for these
        if self._value_loading:
            return

        if self.value_is_none:
            value = 0

        # value comes as a months total
        years, months = divmod( value, 12 )
        self.years_spinbox.setValue(years)
        self.months_spinbox.setValue(months)

    def get_value(self):
        if CustomEditor.get_value(self) is ValueLoading:
            return ValueLoading

        self.years_spinbox.interpretText()
        years = int(self.years_spinbox.value())
        self.months_spinbox.interpretText()
        months = int(self.months_spinbox.value())
        value = (years * 12) + months
        return value


