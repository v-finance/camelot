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

from math import floor

import six

from ....core.qt import QtGui, QtWidgets, QtCore, Qt
from camelot.view.art import Icon
from camelot.core.constants import camelot_minint
from camelot.core.constants import camelot_maxint

from .customeditor import CustomEditor, set_background_color_palette
from camelot.view.controls.editors.floateditor import CustomDoubleSpinBox

class IntegerEditor(CustomEditor):
    """Widget for editing an integer field, with a calculator
    """

    calculator_icon = Icon('tango/16x16/apps/accessories-calculator.png')
    
    def __init__(self, parent = None,
                       minimum = camelot_minint,
                       maximum = camelot_maxint,
                       calculator = True,
                       option = None,
                       decimal = False,
                       field_name = 'integer',
                       **kwargs):
        
        CustomEditor.__init__(self, parent)
        self.setObjectName( field_name )
        self.setSizePolicy( QtWidgets.QSizePolicy.Preferred,
                            QtWidgets.QSizePolicy.Fixed )
        action = QtWidgets.QAction(self)
        action.setShortcut( QtGui.QKeySequence( Qt.Key_F4 ) )
        self.setFocusPolicy(Qt.StrongFocus)
        
        spin_box = CustomDoubleSpinBox(option, parent)
        spin_box.setRange(minimum-1, maximum)
        spin_box.setDecimals(0)
        spin_box.setAlignment(Qt.AlignRight|Qt.AlignVCenter)
        spin_box.addAction(action)
        spin_box.setObjectName('spin_box')
        
        self.calculatorButton = QtWidgets.QToolButton()
        self.calculatorButton.setIcon(self.calculator_icon.getQIcon())
        self.calculatorButton.setAutoRaise(True)
        self.calculatorButton.setFocusPolicy(Qt.ClickFocus)
        self.calculatorButton.setFixedHeight(self.get_height())
        self.calculatorButton.clicked.connect(
            lambda:self.popupCalculator(spin_box.value())
        )
        action.triggered.connect(
            lambda:self.popupCalculator(spin_box.value())
        )
        spin_box.editingFinished.connect( self.spinbox_editing_finished )

        layout = QtWidgets.QHBoxLayout()
        layout.setContentsMargins( 0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(spin_box)
        self._calculator = calculator
        if calculator==True:
            layout.addWidget(self.calculatorButton)
        self.setFocusProxy(spin_box)
        self.setLayout(layout)
        self.option = option
        self.decimal = decimal

    def set_field_attributes(self, **kwargs):
        super(IntegerEditor, self).set_field_attributes(**kwargs)
        self.set_enabled(kwargs.get('editable', False))
        spin_box = self.findChild(CustomDoubleSpinBox, 'spin_box')
        if spin_box is not None:
            set_background_color_palette(spin_box.lineEdit(), kwargs.get('background_color', None))
            spin_box.setToolTip(six.text_type(kwargs.get('tooltip') or ''))
            spin_box.setPrefix(six.text_type(kwargs.get('prefix', '')))
            spin_box.setSuffix(six.text_type(kwargs.get('suffix', '')))
            spin_box.setSingleStep(kwargs.get('single_step', 1))

    def set_value(self, value):
        value = CustomEditor.set_value(self, value)
        spin_box = self.findChild(CustomDoubleSpinBox, 'spin_box')
        if spin_box is not None:
            if value is None:
                spin_box.setValue(spin_box.minimum())
            else:
                spin_box.setValue(value)

    def get_value(self):
        value_loading = CustomEditor.get_value(self)
        if value_loading is not None:
            return value_loading
        spin_box = self.findChild(CustomDoubleSpinBox, 'spin_box')
        if spin_box is not None:
            spin_box.interpretText()
            value = int(spin_box.value())
            if value==int(spin_box.minimum()):
                return None
            elif self.decimal:
                import decimal
                return decimal.Decimal(value)
            return value

    def set_enabled(self, editable=True):
        spin_box = self.findChild(CustomDoubleSpinBox, 'spin_box')
        if spin_box is not None:
            spin_box.setReadOnly(not editable)
            spin_box.setEnabled(editable)
            
            # Version '5' indicates that this widget is put into a form.
            # If so, the calculatorButton and the spinBox's controls should be hidden.
            if self.option and self.option.version != 5:
                self.calculatorButton.hide()
                spin_box.setButtonSymbols(QtWidgets.QAbstractSpinBox.NoButtons)
            else:
                self.calculatorButton.setVisible(editable and self._calculator)
                if not editable:
                    spin_box.setButtonSymbols(QtWidgets.QAbstractSpinBox.NoButtons)

    def popupCalculator(self, value):
        from camelot.view.controls.calculator import Calculator
        calculator = Calculator(self)
        calculator.setValue(value)
        calculator.calculation_finished_signal.connect( self.calculation_finished )
        calculator.exec_()

    @QtCore.qt_slot(six.text_type)
    def calculation_finished(self, value):
        spin_box = self.findChild(CustomDoubleSpinBox, 'spin_box')
        if spin_box is not None:
            spin_box.setValue(floor(float(six.text_type(value))))
            self.editingFinished.emit()

    @QtCore.qt_slot()
    def spinbox_editing_finished(self):
        self.editingFinished.emit()

