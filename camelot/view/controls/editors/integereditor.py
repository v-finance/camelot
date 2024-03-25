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



from ....core.qt import QtGui, QtWidgets, QtCore, Qt
from camelot.view.art import FontIcon

from .customeditor import CustomEditor, set_background_color_palette
from camelot.view.controls.editors.floateditor import CustomDoubleSpinBox

class IntegerEditor(CustomEditor):
    """Widget for editing an integer field, with a calculator
    """

    calculator_icon = FontIcon('calculator') # 'tango/16x16/apps/accessories-calculator.png'
    
    def __init__(self, parent = None,
                       calculator = True,
                       option = None,
                       field_name = 'integer'):
        CustomEditor.__init__(self, parent)
        self.setObjectName( field_name )
        self.setSizePolicy( QtWidgets.QSizePolicy.Policy.Preferred,
                            QtWidgets.QSizePolicy.Policy.Fixed )
        action = QtGui.QAction(self)
        action.setShortcut( QtGui.QKeySequence( Qt.Key.Key_F4.value ) )
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        
        spin_box = CustomDoubleSpinBox(option, parent)
        spin_box.setDecimals(0)
        spin_box.setAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignVCenter)
        spin_box.addAction(action)
        spin_box.setObjectName('spin_box')
        
        self.calculatorButton = QtWidgets.QToolButton()
        self.calculatorButton.setIcon(self.calculator_icon.getQIcon())
        self.calculatorButton.setAutoRaise(True)
        self.calculatorButton.setFocusPolicy(Qt.FocusPolicy.ClickFocus)
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

    def set_suffix(self, suffix):
        spin_box = self.findChild(CustomDoubleSpinBox, 'spin_box')
        if spin_box is not None:
            spin_box.setSuffix(str(suffix or ''))

    def set_prefix(self, prefix):
        spin_box = self.findChild(CustomDoubleSpinBox, 'spin_box')
        if spin_box is not None:
            spin_box.setPrefix(str(prefix or ''))

    def set_single_step(self, single_step):
        spin_box = self.findChild(CustomDoubleSpinBox, 'spin_box')
        if spin_box is not None:
            single_step = single_step if single_step is not None else 1
            spin_box.setSingleStep(single_step)

    def set_minimum(self, minimum):
        if minimum is not None:
            spin_box = self.findChild(CustomDoubleSpinBox, 'spin_box')
            if spin_box is not None:
                spin_box.setMinimum(minimum-1)

    def set_maximum(self, maximum):
        if maximum is not None:
            spin_box = self.findChild(CustomDoubleSpinBox, 'spin_box')
            if spin_box is not None:
                spin_box.setMaximum(maximum)

    def set_tooltip(self, tooltip):
        super().set_tooltip(tooltip)
        spin_box = self.findChild(CustomDoubleSpinBox, 'spin_box')
        if spin_box is not None:
            spin_box.setToolTip(str(tooltip or ''))

    def set_editable(self, editable):
        self.set_enabled(editable)

    def set_background_color(self, background_color):
        super().set_background_color(background_color)
        spin_box = self.findChild(CustomDoubleSpinBox, 'spin_box')
        if spin_box is not None:
            set_background_color_palette(spin_box.lineEdit(), background_color)

    def set_value(self, value):
        spin_box = self.findChild(CustomDoubleSpinBox, 'spin_box')
        if spin_box is not None:
            if value is None:
                spin_box.setValue(spin_box.minimum())
            else:
                spin_box.setValue(value)

    def get_value(self):
        spin_box = self.findChild(CustomDoubleSpinBox, 'spin_box')
        if spin_box is not None:
            spin_box.interpretText()
            value = int(spin_box.value())
            if value==int(spin_box.minimum()):
                return None
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
                spin_box.setButtonSymbols(QtWidgets.QAbstractSpinBox.ButtonSymbols.NoButtons)
            else:
                self.calculatorButton.setVisible(editable and self._calculator)
                if not editable:
                    spin_box.setButtonSymbols(QtWidgets.QAbstractSpinBox.ButtonSymbols.NoButtons)

    def popupCalculator(self, value):
        from camelot.view.controls.calculator import Calculator
        calculator = Calculator(self)
        calculator.setValue(value)
        calculator.calculation_finished_signal.connect( self.calculation_finished )
        calculator.exec()

    @QtCore.qt_slot(str)
    def calculation_finished(self, value):
        spin_box = self.findChild(CustomDoubleSpinBox, 'spin_box')
        if spin_box is not None:
            spin_box.setValue(floor(float(str(value))))
            self.editingFinished.emit()

    @QtCore.qt_slot()
    def spinbox_editing_finished(self):
        self.editingFinished.emit()

