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

from math import floor

import six

from ....core.qt import QtGui, QtCore, Qt
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
                       field_name = 'integer',
                       **kwargs):
        
        CustomEditor.__init__(self, parent)
        self.setObjectName( field_name )
        self.setSizePolicy( QtGui.QSizePolicy.Preferred,
                            QtGui.QSizePolicy.Fixed )        
        action = QtGui.QAction(self)
        action.setShortcut( QtGui.QKeySequence( Qt.Key_F4 ) )
        self.setFocusPolicy(Qt.StrongFocus)
        
        spin_box = CustomDoubleSpinBox(option, parent)
        spin_box.setRange(minimum-1, maximum)
        spin_box.setDecimals(0)
        spin_box.setAlignment(Qt.AlignRight|Qt.AlignVCenter)
        spin_box.addAction(action)
        spin_box.setObjectName('spin_box')
        
        self.calculatorButton = QtGui.QToolButton()
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

        layout = QtGui.QHBoxLayout()
        layout.setContentsMargins( 0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(spin_box)
        self._calculator = calculator
        if calculator==True:
            layout.addWidget(self.calculatorButton)
        self.setFocusProxy(spin_box)
        self.setLayout(layout)
        self._nullable = True
        
        self.option = option

    def set_field_attributes(self, editable = True,
                                   background_color = None, 
                                   tooltip = None,
                                   prefix = '',
                                   suffix = '',
                                   nullable = True,
                                   single_step = 1, **kwargs):
        self.set_enabled(editable)
        spin_box = self.findChild(CustomDoubleSpinBox, 'spin_box')
        if spin_box is not None:
            set_background_color_palette(spin_box.lineEdit(), background_color )
    
            spin_box.setToolTip(six.text_type(tooltip or ''))
            
            if prefix:
                spin_box.setPrefix(u'%s '%(six.text_type(prefix).lstrip()))
            else:
                spin_box.setPrefix('')
            if suffix:
                spin_box.setSuffix(u' %s'%(six.text_type(suffix).rstrip()))
            else:
                spin_box.setSuffix(u'')
            
            spin_box.setSingleStep(single_step)
            self._nullable = nullable

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
                spin_box.setButtonSymbols(QtGui.QAbstractSpinBox.NoButtons)
            else:
                self.calculatorButton.setVisible(editable and self._calculator)
                if not editable:
                    spin_box.setButtonSymbols(QtGui.QAbstractSpinBox.NoButtons)

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
