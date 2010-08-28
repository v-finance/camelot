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

from PyQt4 import QtGui
from PyQt4 import QtCore
from PyQt4.QtCore import Qt

from customeditor import CustomEditor, editingFinished
from camelot.view.art import Icon
from camelot.core import constants
from math import floor


class CustomDoubleSpinBox(QtGui.QDoubleSpinBox):
    """Spinbox that doesn't accept mouse scrolling as input"""

    def wheelEvent(self, wheel_event):
        wheel_event.ignore()


class IntegerEditor(CustomEditor):
    """Widget for editing an integer field, with a calculator

Special use cases of the IntegerEditor :

case 1
------

we have a required integer field without a default.

so the model will do set_value( None )

since this is a required field, the user should be able
to enter a value, 0 is a legitimate value.

when get_value is called, 0 should be returned if the
user has set the editor to 0, and None if the user didn't
touch the editor.

so the editor should make a visual difference between
None and 0, so the user can see he didn't enter something
yet

case 2
------

we have a non required integer field without a default

the model will do set_value( None )

the get_value() should return None and not 0.  because
in case it returns 0, 0 will be written to the db, causing
an unneeded update of the db.
    
"""

    def __init__(self,
                 parent=None,
                 minimum=constants.camelot_minint,
                 maximum=constants.camelot_maxint,
                 calculator=True,
                 **kwargs):
        CustomEditor.__init__(self, parent)
        action = QtGui.QAction(self)
        action.setShortcut(Qt.Key_F3)
        self.setFocusPolicy(Qt.StrongFocus)

        self.spinBox = CustomDoubleSpinBox(parent)
        self.spinBox.setRange(minimum, maximum)
        self.spinBox.setDecimals(0)
        self.spinBox.setAlignment(Qt.AlignRight|Qt.AlignVCenter)
        self.spinBox.setSingleStep(1)
        self.spinBox.addAction(action)
        self.calculatorButton = QtGui.QToolButton()
        icon = Icon('tango/16x16/apps/accessories-calculator.png').getQIcon()
        self.calculatorButton.setIcon(icon)
        self.calculatorButton.setAutoRaise(True)
        self.calculatorButton.setFixedHeight(self.get_height())

        #self.connect(self.calculatorButton,
        #             QtCore.SIGNAL('clicked()'),
        #             lambda:self.popupCalculator(self.spinBox.value()))
        #self.connect(action,
        #             QtCore.SIGNAL('triggered(bool)'),
        #             lambda:self.popupCalculator(self.spinBox.value()))
        #self.connect(self.spinBox,
        #             QtCore.SIGNAL('editingFinished()'),
        #             lambda:self.editingFinished(self.spinBox.value()))
        self.calculatorButton.clicked.connect(
            lambda:self.popupCalculator(self.spinBox.value())
        )
        action.triggered.connect(
            lambda:self.popupCalculator(self.spinBox.value())
        )
        self.spinBox.editingFinished.connect(
            lambda:self.editingFinished(self.spinBox.value())
        )

        layout = QtGui.QHBoxLayout()
        layout.setMargin(0)
        layout.setSpacing(0)
        layout.addWidget(self.spinBox)
        layout.addWidget(self.calculatorButton)
        self.setFocusProxy(self.spinBox)
        self.setLayout(layout)

    def set_field_attributes(self, editable=True, background_color=None, prefix='', suffix='', **kwargs):
        self.set_enabled(editable)
        self.set_background_color(background_color)
        self.spinBox.setPrefix(u'%s '%(unicode(prefix).lstrip()))
        self.spinBox.setSuffix(u' %s'%(unicode(suffix).rstrip()))

    def set_value(self, value):
        value = CustomEditor.set_value(self, value)
        if value!=None:
            value = str(value).replace(',', '.')
            self.spinBox.setValue(eval(value))
        else:
            self.spinBox.setValue(0)

    def get_value(self):
        value_loading = CustomEditor.get_value(self)
        if value_loading is not None:
            return value_loading

        if self.value_is_none:
            return None

        self.spinBox.interpretText()
        value = int(self.spinBox.value())
        return value

    def set_enabled(self, editable=True):
        self.spinBox.setReadOnly(not editable)
        self.spinBox.setEnabled(editable)
        self.calculatorButton.setShown(editable)
        if not editable:
            self.spinBox.setButtonSymbols(QtGui.QAbstractSpinBox.NoButtons)

    def popupCalculator(self, value):
        from camelot.view.controls.calculator import Calculator
        calculator = Calculator(self)
        calculator.setValue(value)
        self.connect(calculator,
                     QtCore.SIGNAL('calculationFinished'),
                     self.calculationFinished)
        calculator.exec_()

    def calculationFinished(self, value):
        self.spinBox.setValue(floor(float(value)))
        self.emit(editingFinished)

    def editingFinished(self, value):
        self.emit(editingFinished)
