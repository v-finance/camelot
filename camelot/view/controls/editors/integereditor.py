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

from PyQt4 import QtGui
from PyQt4 import QtCore
from PyQt4.QtCore import Qt

import six

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
        
        self.spinBox = CustomDoubleSpinBox(option, parent)
        self.spinBox.setRange(minimum-1, maximum)
        self.spinBox.setDecimals(0)
        self.spinBox.setAlignment(Qt.AlignRight|Qt.AlignVCenter)
        self.spinBox.addAction(action)
        
        self.calculatorButton = QtGui.QToolButton()
        self.calculatorButton.setIcon(self.calculator_icon.getQIcon())
        self.calculatorButton.setAutoRaise(True)
        self.calculatorButton.setFocusPolicy(Qt.ClickFocus)
        self.calculatorButton.setFixedHeight(self.get_height())
        self.calculatorButton.clicked.connect(
            lambda:self.popupCalculator(self.spinBox.value())
        )
        action.triggered.connect(
            lambda:self.popupCalculator(self.spinBox.value())
        )
        self.spinBox.editingFinished.connect( self.spinbox_editing_finished )

        layout = QtGui.QHBoxLayout()
        layout.setContentsMargins( 0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self.spinBox)
        self._calculator = calculator
        if calculator==True:
            layout.addWidget(self.calculatorButton)
        self.setFocusProxy(self.spinBox)
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
        set_background_color_palette(self.spinBox.lineEdit(), background_color )

        self.spinBox.setToolTip(six.text_type(tooltip or ''))
        
        if prefix:
            self.spinBox.setPrefix(u'%s '%(six.text_type(prefix).lstrip()))
        else:
            self.spinBox.setPrefix('')
        if suffix:
            self.spinBox.setSuffix(u' %s'%(six.text_type(suffix).rstrip()))
        else:
            self.spinBox.setSuffix(u'')
        
        self.spinBox.setSingleStep(single_step)
        self._nullable = nullable

    def set_value(self, value):
        value = CustomEditor.set_value(self, value)
        if value is None:
            self.spinBox.setValue(self.spinBox.minimum())
        else:
            self.spinBox.setValue(value)

    def get_value(self):
        value_loading = CustomEditor.get_value(self)
        if value_loading is not None:
            return value_loading
        self.spinBox.interpretText()
        value = int(self.spinBox.value())
        if value==int(self.spinBox.minimum()):
            return None
        return value

    def set_enabled(self, editable=True):
        self.spinBox.setReadOnly(not editable)
        self.spinBox.setEnabled(editable)
        
        # Version '5' indicates that this widget is put into a form.
        # If so, the calculatorButton and the spinBox's controls should be hidden.
        if self.option and self.option.version != 5:
            self.calculatorButton.hide()
            self.spinBox.setButtonSymbols(QtGui.QAbstractSpinBox.NoButtons)
        else:
            self.calculatorButton.setVisible(editable and self._calculator)
            if not editable:
                self.spinBox.setButtonSymbols(QtGui.QAbstractSpinBox.NoButtons)

    def popupCalculator(self, value):
        from camelot.view.controls.calculator import Calculator
        calculator = Calculator(self)
        calculator.setValue(value)
        calculator.calculation_finished_signal.connect( self.calculation_finished )
        calculator.exec_()

    @QtCore.pyqtSlot(six.text_type)
    def calculation_finished(self, value):
        self.spinBox.setValue(floor(float(six.text_type(value))))
        self.editingFinished.emit()

    @QtCore.pyqtSlot()
    def spinbox_editing_finished(self):
        self.editingFinished.emit()
