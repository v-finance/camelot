#  ============================================================================
#
#  Copyright (C) 2007-2013 Conceptive Engineering bvba. All rights reserved.
#  www.conceptive.be / info@conceptive.be
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
#  visit www.python-camelot.com or contact info@conceptive.be
#
#  This file is provided AS IS with NO WARRANTY OF ANY KIND, INCLUDING THE
#  WARRANTY OF DESIGN, MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE.
#
#  For use of this library in commercial applications, please contact
#  info@conceptive.be
#
#  ============================================================================

from PyQt4 import QtGui
from PyQt4 import QtCore
from PyQt4.QtCore import Qt

from customeditor import CustomEditor, set_background_color_palette, draw_tooltip_visualization
from camelot.view.art import Icon
from camelot.core import constants

class CustomDoubleSpinBox(QtGui.QDoubleSpinBox):
    """Spinbox that doesn't accept mouse scrolling as input"""
    
    def __init__(self, option = None, parent = None):
        self._option = option
        self._locale = QtCore.QLocale()        
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
            QtGui.QApplication.sendEvent(self, new_key_event)
        # Propagate all other events to the super class
        else:
            super(CustomDoubleSpinBox, self).keyPressEvent(key_event)

    def textFromValue(self, value):
        if value==self.minimum():
            return ''
        text = unicode( self._locale.toString( float(value), 
                                               'f', 
                                               self.decimals() ) )
        return text
    
    def stripped(self, qinput):
        """Strip a string from its prefix, suffix and spaces
        
        :param qinput: a :class:`QtCore.QString`
        """
        # this code is based on QAbstractSpinBoxPrivate::stripped
        copy_from = 0
        copy_to = -1
        if self.prefix().size() and qinput.startsWith(self.prefix()):
            copy_from += self.prefix().size()
        if self.suffix().size() and qinput.endsWith(self.suffix()):
            copy_to = -1*self.suffix().size()
        partial_input = unicode(qinput)[copy_from:copy_to]
        return partial_input.strip()
    
    def validate(self, qinput, pos):
        """Method overwritten from :class:`QtGui.QDoubleSpinBox` to handle
        an empty string as a special value for `None`.
        """
        valid, new_pos = super(CustomDoubleSpinBox, self).validate(qinput, pos)
        if valid!=QtGui.QValidator.Acceptable:
            # this code is based on QSpinBoxPrivate::validateAndInterpret
            if len(self.stripped(qinput))==0:
                valid = QtGui.QValidator.Acceptable
        return valid, new_pos
    
    def valueFromText(self, text):
        # this code is based on QSpinBoxPrivate::validateAndInterpret
        if len(self.stripped(text))==0:
            return self.minimum()
        return super(CustomDoubleSpinBox, self).valueFromText(text)
        
    def paintEvent(self, event):
        super(CustomDoubleSpinBox, self).paintEvent(event)
        if self.toolTip():
            draw_tooltip_visualization(self)

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
        action = QtGui.QAction(self)
        action.setShortcut( QtGui.QKeySequence( Qt.Key_F4 ) )
        self.setFocusPolicy(Qt.StrongFocus)
        spinBox = CustomDoubleSpinBox(option, parent)
        spinBox.setObjectName('spinbox')
        

        spinBox.setRange(minimum-1, maximum)
        spinBox.setDecimals(2)
        spinBox.setAlignment(Qt.AlignRight|Qt.AlignVCenter)

        spinBox.addAction(action)
        self.calculatorButton = QtGui.QToolButton()
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

        layout = QtGui.QHBoxLayout()
        layout.setContentsMargins( 0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(spinBox)
        layout.addWidget(self.calculatorButton)
        self.setFocusProxy(spinBox)
        self.setLayout(layout)

    def set_field_attributes(self, editable = True,
                                   background_color = None,
                                   tooltip = None,
                                   prefix = '',
                                   suffix = '',
                                   precision = 2,
                                   single_step = 1.0, **kwargs):
        self.set_enabled(editable)
        self.set_background_color(background_color)
        spinBox = self.findChild(CustomDoubleSpinBox, 'spinbox')
        spinBox.setToolTip(unicode(tooltip or ''))
        spinBox.setPrefix(u'%s '%(unicode(prefix or '').lstrip()))
        spinBox.setSuffix(u' %s'%(unicode(suffix or '').rstrip()))
        spinBox.setSingleStep(single_step)
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
            return decimal.Decimal('%.*f' % (self.spinBox.decimals(), value))
        return value

    def set_enabled(self, editable=True):
        spinBox = self.findChild(CustomDoubleSpinBox, 'spinbox')
        spinBox.setReadOnly(not editable)
        spinBox.setEnabled(editable)
        self.calculatorButton.setShown(editable and self._calculator)
        if editable:
            spinBox.setButtonSymbols(QtGui.QAbstractSpinBox.UpDownArrows)
        else:
            spinBox.setButtonSymbols(QtGui.QAbstractSpinBox.NoButtons)

    def popupCalculator(self, value):
        from camelot.view.controls.calculator import Calculator
        calculator = Calculator(self)
        calculator.setValue(value)
        calculator.calculation_finished_signal.connect( self.calculation_finished )
        calculator.exec_()

    @QtCore.pyqtSlot(QtCore.QString)
    def calculation_finished(self, value):
        spinBox = self.findChild(CustomDoubleSpinBox, 'spinbox')
        spinBox.setValue(float(unicode(value)))
        self.editingFinished.emit()

    @QtCore.pyqtSlot()
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


