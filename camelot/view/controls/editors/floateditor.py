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



from ....core.qt import QtGui, QtWidgets, QtCore, Qt
from .customeditor import CustomEditor, set_background_color_palette
from ...art import FontIcon

class CustomDoubleSpinBox(QtWidgets.QDoubleSpinBox):
    """Spinbox that doesn't accept mouse scrolling as input"""
    
    def __init__(self, option = None, parent = None):
        self._option = option
        super(CustomDoubleSpinBox, self).__init__(parent)
    
    def wheelEvent(self, wheel_event):
        wheel_event.ignore()
        
    def stepBy(self, steps):
        """Overwritten from :class:`QtGui.QAbstractSpinBox to set the 
        value of the spinbox to 0 if the value was `None`"""
        if steps!=0 and self.value()==self.minimum():
            self.setValue(0)
            steps = steps - (steps / abs(steps))
        super(CustomDoubleSpinBox, self).stepBy(steps)
        
    def keyPressEvent(self, key_event):
        # Disable the default behaviour when pressing the up or down arrow
        # which would respectively increment and decrement the value
        # inside the spinbox. This custom behaviour is only applicable
        # when being displayed inside a table view, hence the version check.
        # By ignoring key_event, the table view itself is scrolled instead.
        if key_event.key() in (Qt.Key.Key_Up, Qt.Key.Key_Down):
            if self._option and self._option.version != 5:
                key_event.ignore()
                return
        decimal_point = QtCore.QLocale().decimalPoint()
        # Make sure that the Period key on the numpad is *always* 
        # represented by the systems locale decimal separator to 
        # facilitate user input.
        decimal_point_in_unicode = ord(decimal_point)
        decimal_point_string = decimal_point

        if key_event.key() == Qt.Key.Key_Period and decimal_point_in_unicode != Qt.Key.Key_Period:
            # Dynamically build a 'new' event that holds this locales decimal separator
            new_key_event = QtGui.QKeyEvent(
                QtGui.QKeyEvent.Type(key_event.type()),
                decimal_point_in_unicode,
                key_event.modifiers(),
                decimal_point_string
            )
            key_event.accept() # Block 'old' event
            QtWidgets.QApplication.sendEvent(self, new_key_event)
        # Propagate all other events to the super class
        else:
            super(CustomDoubleSpinBox, self).keyPressEvent(key_event)

    def textFromValue(self, value):
        if value==self.minimum():
            return ''
        return super(CustomDoubleSpinBox, self).textFromValue(value)

    def stripped(self, qinput):
        """Strip a string from its prefix, suffix and spaces
        
        :param qinput: a :class:`QtCore.QString`
        """
        # this code is based on QAbstractSpinBoxPrivate::stripped
        copy_from = 0
        copy_to = len(qinput)
        if len(self.prefix()):
            if qinput.startswith(self.prefix()):
                copy_from += len(self.prefix())
        if len(self.suffix()):
            if qinput.endswith(self.suffix()):
                copy_to = -1*len(self.suffix())
        partial_input = str(qinput)[copy_from:copy_to]
        return partial_input.strip()
    
    def validate(self, qinput, pos):
        """Method overwritten from :class:`QtWidgets.QDoubleSpinBox` to handle
        an empty string as a special value for `None`.
        """
        result = super(CustomDoubleSpinBox, self).validate(qinput, pos)
        valid, qinput, new_pos = result
        if valid!=QtGui.QValidator.State.Acceptable:
            # this code is based on QSpinBoxPrivate::validateAndInterpret
            if len(self.stripped(qinput))==0:
                valid = QtGui.QValidator.State.Acceptable
        return valid, qinput, new_pos
    
    def valueFromText(self, text):
        # this code is based on QSpinBoxPrivate::validateAndInterpret
        if len(self.stripped(text))==0:
            return self.minimum()
        return super(CustomDoubleSpinBox, self).valueFromText(text)

class FloatEditor(CustomEditor):
    """Widget for editing a float field, with a calculator button.  
    The calculator button can be turned of with the **calculator** field
    attribute.
    """

    calculator_icon = FontIcon('calculator') # 'tango/16x16/apps/accessories-calculator.png'
    
    def __init__(self, parent,
                       calculator = True,
                       decimal = False,
                       action_routes = [],
                       option = None,
                       field_name = 'float'):
        CustomEditor.__init__(self, parent)
        self.setObjectName( field_name )
        self.setSizePolicy( QtWidgets.QSizePolicy.Policy.Preferred,
                            QtWidgets.QSizePolicy.Policy.Fixed )        
        self._decimal = decimal
        self._calculator = calculator
        action = QtGui.QAction(self)
        action.setShortcut( QtGui.QKeySequence( Qt.Key.Key_F4.value ) )
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        spinBox = CustomDoubleSpinBox(option, parent)
        spinBox.setObjectName('spinbox')
        spinBox.setDecimals(2)
        spinBox.setAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignVCenter)
        spinBox.setGroupSeparatorShown(True)

        spinBox.addAction(action)
        self.calculatorButton = QtWidgets.QToolButton()
        self.calculatorButton.setIcon( self.calculator_icon.getQIcon() )
        self.calculatorButton.setAutoRaise(True)
        self.calculatorButton.setFixedHeight(self.get_height())
        self.calculatorButton.setToolTip('Calculator F4')
        self.calculatorButton.setFocusPolicy(Qt.FocusPolicy.ClickFocus)

        self.calculatorButton.clicked.connect(
            lambda:self.popupCalculator(spinBox.value())
        )
        action.triggered.connect(
            lambda:self.popupCalculator(spinBox.value())
        )
        spinBox.editingFinished.connect(self.spinbox_editing_finished)

        self.releaseKeyboard()

        layout = QtWidgets.QHBoxLayout()
        layout.setContentsMargins( 0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(spinBox)
        layout.addWidget(self.calculatorButton)
        self.add_actions(action_routes, layout)
        self.setFocusProxy(spinBox)
        self.setLayout(layout)

    def set_suffix(self, suffix):
        spinBox = self.findChild(CustomDoubleSpinBox, 'spinbox')
        spinBox.setSuffix(str(suffix or ''))

    def set_prefix(self, prefix):
        spinBox = self.findChild(CustomDoubleSpinBox, 'spinbox')
        spinBox.setPrefix(str(prefix or ''))

    def set_single_step(self, single_step):
        spinBox = self.findChild(CustomDoubleSpinBox, 'spinbox')
        single_step = single_step if single_step is not None else 1.0
        spinBox.setSingleStep(single_step)

    def set_precision(self, precision):
        spinBox = self.findChild(CustomDoubleSpinBox, 'spinbox')
        # Set default precision of 2 when precision is undefined, instead of using the default argument of the dictionary's get method,
        # as that only handles the precision key not being present, not it being explicitly set to None.
        if precision is None:
            precision = 2
        if spinBox.decimals() != precision:
            spinBox.setDecimals( precision )

    def set_minimum(self, minimum):
        if minimum is not None:
            spinBox = self.findChild(CustomDoubleSpinBox, 'spinbox')
            spinBox.setMinimum(minimum-1)

    def set_maximum(self, maximum):
        if maximum is not None:
            spinBox = self.findChild(CustomDoubleSpinBox, 'spinbox')
            spinBox.setMaximum(maximum)

    def set_focus_policy(self, focus_policy):
        if focus_policy is not None:
            spinBox = self.findChild(CustomDoubleSpinBox, 'spinbox')
            spinBox.setFocusPolicy(Qt.FocusPolicy(focus_policy))

    def set_tooltip(self, tooltip):
        super().set_tooltip(tooltip)
        spinBox = self.findChild(CustomDoubleSpinBox, 'spinbox')
        spinBox.setToolTip(str(tooltip or ''))

    def set_editable(self, editable):
        self.calculatorButton.setVisible(editable and self._calculator)
        spinBox = self.findChild(CustomDoubleSpinBox, 'spinbox')
        spinBox.setReadOnly(not editable)
        spinBox.setButtonSymbols(QtWidgets.QAbstractSpinBox.ButtonSymbols.UpDownArrows if editable else QtWidgets.QAbstractSpinBox.ButtonSymbols.NoButtons)

    def set_value(self, value):
        value = CustomEditor.set_value(self, value)
        spinBox = self.findChild(CustomDoubleSpinBox, 'spinbox')
        if value is None:
            spinBox.setValue(spinBox.minimum())
        else:
            spinBox.setValue(float(value))

    def get_value(self):
        value_loading = CustomEditor.get_value(self)
        if value_loading is not None:
            return value_loading

        spinBox = self.findChild(CustomDoubleSpinBox, 'spinbox')
        spinBox.interpretText()
        value = spinBox.value()
        if value==spinBox.minimum():
            return None
        elif self._decimal:
            import decimal
            return decimal.Decimal('%.*f' % (spinBox.decimals(), value))
        return value

    def popupCalculator(self, value):
        from camelot.view.controls.calculator import Calculator
        calculator = Calculator(self)
        calculator.setValue(value)
        calculator.calculation_finished_signal.connect( self.calculation_finished )
        calculator.exec()

    @QtCore.qt_slot(str)
    def calculation_finished(self, value):
        spinBox = self.findChild(CustomDoubleSpinBox, 'spinbox')
        spinBox.setValue(float(str(value)))
        self.editingFinished.emit()

    @QtCore.qt_slot()
    def spinbox_editing_finished(self):
        self.editingFinished.emit()

    def set_background_color(self, background_color):
        #
        # WARNING : Changing this code requires extensive testing of all editors
        # in all states on all platforms (Mac, Linux, Win XP, Win Vista, Win 7)
        #
        # There seems to be a bug in Windows QStyle that requires the spinbox as
        # well as its line edit to require the bgcolor to be set, was however 
        # unable to reproduce this properly in a test case
        #
        spinBox = self.findChild(CustomDoubleSpinBox, 'spinbox')
        set_background_color_palette(spinBox.lineEdit(), background_color)
        set_background_color_palette(spinBox, background_color)

    value = property(fget=get_value,fset=set_value)


