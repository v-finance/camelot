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

from PyQt4 import QtGui, QtCore
from PyQt4.QtCore import Qt

from customeditor import CustomEditor
from camelot.view.art import Icon
from camelot.core import constants
from camelot.view.proxy import ValueLoading

class CustomDoubleSpinBox(QtGui.QDoubleSpinBox):
    """Spinbox that doesn't accept mouse scrolling as input"""

    def wheelEvent(self, wheel_event):
        wheel_event.ignore()

    def textFromValue(self, value):
        return str( QtCore.QString("%L1").arg(float(value), 0, 'f', self.decimals()) )

    # def valueFromText(self, text):
    # maybe construct some cases to make other input formats possible
    #   return text

class FloatEditor(CustomEditor):
    """Widget for editing a float field, with a calculator"""

    def __init__(self,
                 parent,
                 precision=2,
                 minimum=constants.camelot_minfloat,
                 maximum=constants.camelot_maxfloat,
                 calculator=True,
                 decimal=False,
                 **kwargs):
        CustomEditor.__init__(self, parent)
        self._decimal = decimal
        action = QtGui.QAction(self)
        action.setShortcut(Qt.Key_F3)
        self.setFocusPolicy(Qt.StrongFocus)
        self.precision = precision
        self.spinBox = CustomDoubleSpinBox(parent)

        self.spinBox.setRange(minimum, maximum)
        self.spinBox.setDecimals(precision)
        self.spinBox.setAlignment(Qt.AlignRight|Qt.AlignVCenter)
        self.spinBox.setSingleStep(1.0)

        self.spinBox.addAction(action)
        self.calculatorButton = QtGui.QToolButton()
        icon = Icon('tango/16x16/apps/accessories-calculator.png').getQIcon()
        self.calculatorButton.setIcon(icon)
        self.calculatorButton.setAutoRaise(True)
        self.calculatorButton.setFixedHeight(self.get_height())

        self.connect(self.calculatorButton,
                     QtCore.SIGNAL('clicked()'),
                     lambda:self.popupCalculator(self.spinBox.value()))
        self.connect(action,
                     QtCore.SIGNAL('triggered(bool)'),
                     lambda:self.popupCalculator(self.spinBox.value()))
        self.connect(self.spinBox,
                     QtCore.SIGNAL('editingFinished()'),
                     lambda:self.editingFinished(self.spinBox.value()))

        self.releaseKeyboard()

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
        if value:
            self.spinBox.setValue(value)
        #else:
        #    self.spinBox.setValue(0.0)

    def get_value(self):
        val = CustomEditor.get_value(self)
        # ValueLoading?
        if val is not None:
            return val
        elif self.value_is_none:
            return None
        self.spinBox.interpretText()
        value = self.spinBox.value()
        if self._decimal:
            import decimal
            value = decimal.Decimal('%.*f' % (self.precision, value))
        #return CustomEditor.get_value(self) or value
        return value

    def set_enabled(self, editable=True):
        self.spinBox.setReadOnly(not editable)
        self.spinBox.setEnabled(editable)
        self.calculatorButton.setShown(editable)
        if editable:
            self.spinBox.setButtonSymbols(QtGui.QAbstractSpinBox.UpDownArrows)
        else:
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
        self.spinBox.setValue(float(value))
        self.emit(QtCore.SIGNAL('editingFinished()'))

    def editingFinished(self, value):
        self.emit(QtCore.SIGNAL('editingFinished()'))

    def set_background_color(self, background_color):
        if background_color not in (None, ValueLoading):
            selfpalette = self.spinBox.palette()
            sbpalette = self.spinBox.palette()
            lepalette = self.spinBox.lineEdit().palette()
            for x in [QtGui.QPalette.Active, QtGui.QPalette.Inactive, QtGui.QPalette.Disabled]:
                for y in [self.backgroundRole(), QtGui.QPalette.Window, QtGui.QPalette.Base]:
                    selfpalette.setColor(x, y, background_color)
                for y in [self.spinBox.backgroundRole(), QtGui.QPalette.Window, QtGui.QPalette.Base]:
                    sbpalette.setColor(x, y, background_color)
                for y in [self.spinBox.lineEdit().backgroundRole(), QtGui.QPalette.Window, QtGui.QPalette.Base]:
                    lepalette.setColor(x, y, background_color)
            self.setPalette(selfpalette)
            self.spinBox.setPalette(sbpalette)
            self.spinBox.lineEdit().setPalette(lepalette)
            return True
        else:
            return False

