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

import six

from ....core.qt import (QtGui, QtWidgets, QtCore, Qt,
                         q_string_size, q_string_startswith, q_string_endswith)
from .customeditor import CustomEditor, set_background_color_palette
from ...art import Icon
from ...utils import locale
from ....core import constants

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
        if key_event.key() in (Qt.Key_Up, Qt.Key_Down):
            if self._option and self._option.version != 5:
                key_event.ignore()
                return
        decimal_point = QtCore.QLocale.system().decimalPoint()
        # Make sure that the Period key on the numpad is *always* 
        # represented by the systems locale decimal separator to 
        # facilitate user input.
        if key_event.key() == Qt.Key_Period and decimal_point.unicode() != Qt.Key_Period:
            # Dynamically build a 'new' event that holds this locales decimal separator
            new_key_event = QtGui.QKeyEvent( key_event.type(),
                                             decimal_point.unicode(),
                                             key_event.modifiers(),
                                             QtCore.QString(decimal_point) )
            key_event.accept() # Block 'old' event
            QtWidgets.QApplication.sendEvent(self, new_key_event)
        # Propagate all other events to the super class
        else:
            super(CustomDoubleSpinBox, self).keyPressEvent(key_event)

    def textFromValue(self, value):
        if value==self.minimum():
            return ''
        text = six.text_type( locale().toString( float(value),
                                                 'f', 
                                                 self.decimals() ) )
        return text
    
    def stripped(self, qinput):
        """Strip a string from its prefix, suffix and spaces
        
        :param qinput: a :class:`QtCore.QString`
        """
        # this code is based on QAbstractSpinBoxPrivate::stripped
        copy_from = 0
        copy_to = q_string_size(qinput)
        if q_string_size(self.prefix()):
            if q_string_startswith(qinput, self.prefix()):
                copy_from += q_string_size(self.prefix())
        if q_string_size(self.suffix()):
            if q_string_endswith(qinput, self.suffix()):
                copy_to = -1*q_string_size(self.suffix())
        partial_input = six.text_type(qinput)[copy_from:copy_to]
        return partial_input.strip()
    
    def validate(self, qinput, pos):
        """Method overwritten from :class:`QtWidgets.QDoubleSpinBox` to handle
        an empty string as a special value for `None`.
        """
        result = super(CustomDoubleSpinBox, self).validate(qinput, pos)
        if six.PY3:
            valid, qinput, new_pos = result
        else:
            valid, new_pos = result
        if valid!=QtGui.QValidator.Acceptable:
            # this code is based on QSpinBoxPrivate::validateAndInterpret
            if len(self.stripped(qinput))==0:
                valid = QtGui.QValidator.Acceptable
        if six.PY3:
            return valid, qinput, new_pos
        return valid, new_pos
    
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

    calculator_icon = Icon('tango/16x16/apps/accessories-calculator.png')
    
    def __init__(self, parent,
                       minimum = constants.camelot_minfloat,
                       maximum = constants.camelot_maxfloat,
                       calculator = True,
                       decimal = False, 
                       option = None,
                       field_name = 'float',
                       **kwargs):
        CustomEditor.__init__(self, parent)
        self.setObjectName( field_name )
        self.setSizePolicy( QtGui.QSizePolicy.Preferred,
                            QtGui.QSizePolicy.Fixed )        
        self._decimal = decimal
        self._calculator = calculator
        action = QtWidgets.QAction(self)
        action.setShortcut( QtGui.QKeySequence( Qt.Key_F4 ) )
        self.setFocusPolicy(Qt.StrongFocus)
        spinBox = CustomDoubleSpinBox(option, parent)
        spinBox.setObjectName('spinbox')
        

        spinBox.setRange(minimum-1, maximum)
        spinBox.setDecimals(2)
        spinBox.setAlignment(Qt.AlignRight|Qt.AlignVCenter)

        spinBox.addAction(action)
        self.calculatorButton = QtWidgets.QToolButton()
        self.calculatorButton.setIcon( self.calculator_icon.getQIcon() )
        self.calculatorButton.setAutoRaise(True)
        self.calculatorButton.setFixedHeight(self.get_height())
        self.calculatorButton.setToolTip('Calculator F4')
        self.calculatorButton.setFocusPolicy(Qt.ClickFocus)

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
        self.setFocusProxy(spinBox)
        self.setLayout(layout)

    def set_field_attributes(self, **kwargs):
        super(FloatEditor, self).set_field_attributes(**kwargs)
        editable = kwargs.get('editable', False)
        self.calculatorButton.setShown(editable and self._calculator)
        spinBox = self.findChild(CustomDoubleSpinBox, 'spinbox')
        spinBox.setToolTip(six.text_type(kwargs.get('tooltip') or ''))
        spinBox.setPrefix(six.text_type(kwargs.get('prefix', '')))
        spinBox.setSuffix(six.text_type(kwargs.get('suffix', '')))
        spinBox.setSingleStep(kwargs.get('single_step', 1.0))
        spinBox.setReadOnly(not editable)
        spinBox.setButtonSymbols(QtGui.QAbstractSpinBox.UpDownArrows if editable else QtGui.QAbstractSpinBox.NoButtons)
        precision = kwargs.get('precision', 2)
        if spinBox.decimals() != precision:
            spinBox.setDecimals( precision )

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
        calculator.exec_()

    @QtCore.qt_slot(six.text_type)
    def calculation_finished(self, value):
        spinBox = self.findChild(CustomDoubleSpinBox, 'spinbox')
        spinBox.setValue(float(six.text_type(value)))
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



