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

from ...core.qt import QtCore, QtWidgets, q_string_type
from camelot.view.art import FontIcon
from camelot.core.utils import ugettext as _

class Calculator(QtWidgets.QDialog):
    
    calculation_finished_signal = QtCore.qt_signal(q_string_type)
    
    def __init__(self, parent=None):
        QtWidgets.QDialog.__init__(self, parent)
        mainLayout = QtWidgets.QVBoxLayout()
        topLeftLayout = QtWidgets.QVBoxLayout()
        topRightLayout = QtWidgets.QHBoxLayout()
        bottomRightLayout = QtWidgets.QHBoxLayout()
        bottomLayout = QtWidgets.QGridLayout()

        self.setWindowTitle(_('Calculator'))
        self.input = QtWidgets.QLineEdit(self)
        self.input.textEdited.connect(self.Calculate)

        #BUTTONS---

        self.equals = QtWidgets.QPushButton('=', self)
        self.discount = QtWidgets.QPushButton('Discount', self)
        self.save = QtWidgets.QPushButton('&Save', self)
        self.cancel = QtWidgets.QPushButton('Cancel', self)

        self.zero = QtWidgets.QPushButton('0', self)
        self.one = QtWidgets.QPushButton('1', self)
        self.two = QtWidgets.QPushButton('2', self)
        self.three = QtWidgets.QPushButton('3', self)
        self.four = QtWidgets.QPushButton('4', self)
        self.five = QtWidgets.QPushButton('5', self)
        self.six = QtWidgets.QPushButton('6', self)
        self.seven = QtWidgets.QPushButton('7', self)
        self.eight = QtWidgets.QPushButton('8', self)
        self.nine = QtWidgets.QPushButton('9', self)

        self.clear = QtWidgets.QPushButton('&Clear', self)

        self.backspace = QtWidgets.QToolButton()
        icon = FontIcon('backspace').getQIcon() # 'tango/16x16/actions/go-previous.png'
        self.backspace.setIcon(icon)
        self.backspace.setAutoRaise(True)

        self.plus = QtWidgets.QPushButton('+', self)
        self.min = QtWidgets.QPushButton('-', self)
        self.multiply = QtWidgets.QPushButton('x', self)
        self.devide = QtWidgets.QPushButton('/', self)
        self.comma = QtWidgets.QPushButton(',', self)

        #Button-Connects---
        self.equals.clicked.connect(self.ShowCalculate)
        self.zero.clicked.connect(lambda:self.buttonClick(0))
        self.one.clicked.connect(lambda:self.buttonClick(1))
        self.two.clicked.connect(lambda:self.buttonClick(2))
        self.three.clicked.connect(lambda:self.buttonClick(3))
        self.four.clicked.connect(lambda:self.buttonClick(4))
        self.five.clicked.connect(lambda:self.buttonClick(5))
        self.six.clicked.connect(lambda:self.buttonClick(6))
        self.seven.clicked.connect(lambda:self.buttonClick(7))
        self.eight.clicked.connect(lambda:self.buttonClick(8))
        self.nine.clicked.connect(lambda:self.buttonClick(9))
        self.plus.clicked.connect(lambda:self.buttonClick('+'))
        self.min.clicked.connect(lambda:self.buttonClick('-'))
        self.multiply.clicked.connect(lambda:self.buttonClick('*'))
        self.devide.clicked.connect(lambda:self.buttonClick('/'))
        self.clear.clicked.connect(self.clearInput)
        self.backspace.clicked.connect(lambda:self.input.backspace())
        self.comma.clicked.connect(lambda:self.buttonClick('.'))
        self.cancel.clicked.connect(lambda:self.close())
        self.save.clicked.connect(self.SaveValue)
        self.discount.clicked.connect(self.discountClick)

        self.output = QtWidgets.QLabel(self)
        #self.output.move(3, 8)

        mainLayout.addLayout(topLeftLayout)
        topLeftLayout.addLayout(topRightLayout)
        topRightLayout.addWidget(self.input)
        topRightLayout.addWidget(self.backspace)
        topLeftLayout.addWidget(self.output)
        topLeftLayout.addLayout(bottomRightLayout)
        bottomRightLayout.addWidget(self.equals)
        bottomRightLayout.addWidget(self.discount)
        bottomRightLayout.addWidget(self.save)
        bottomRightLayout.addWidget(self.cancel)
        mainLayout.addLayout(bottomLayout)
        bottomLayout.addWidget(self.one, 0,0)
        bottomLayout.addWidget(self.two, 0,1)
        bottomLayout.addWidget(self.three, 0,2)
        bottomLayout.addWidget(self.plus, 0,3)
        bottomLayout.addWidget(self.four, 1,0)
        bottomLayout.addWidget(self.five, 1,1)
        bottomLayout.addWidget(self.six, 1,2)
        bottomLayout.addWidget(self.min, 1,3)
        bottomLayout.addWidget(self.seven, 2,0)
        bottomLayout.addWidget(self.eight, 2,1)
        bottomLayout.addWidget(self.nine, 2,2)
        bottomLayout.addWidget(self.multiply, 2,3)
        bottomLayout.addWidget(self.clear, 3,0)
        bottomLayout.addWidget(self.zero, 3,1)
        bottomLayout.addWidget(self.comma, 3,2)
        bottomLayout.addWidget(self.devide, 3,3)
        self.setLayout(mainLayout)

    def keyPressEvent(self, event):
        #QtWidgets.QWidget.keyPressEvent(self, event)

        key = event.key()
        if key == QtCore.Qt.Key.Key_S:
            self.SaveValue()
            return
        else:
            QtWidgets.QDialog.keyPressEvent(self, event)

    def SaveValue(self):
        self.calculation_finished_signal.emit( self.output.text() )
        self.close()
        return

    def setValue(self, value):
        value = str(value).replace(',', '.')
        self.input.setText(str(value))
        self.Calculate()

    def Calculate(self):
        input = str(self.input.text())
        if not input:
            self.output.setText('')
            return

        try:
            self.output.setText(str(eval(input)))
        except SyntaxError:
            pass
        except NameError:
            self.output.setText('Please input numeric characters')
            pass

    def ShowCalculate(self):
        input = str(self.input.text())
        if not input:
            self.output.setText('')
            return

        if input == str(self.output.text()):
            reply = QtWidgets.QMessageBox.question(
                self,
                'Message',
                'Do you want to Save and Quit?',
                QtWidgets.QMessageBox.StandardButton.Yes,
                QtWidgets.QMessageBox.StandardButton.No
            )

            if reply == QtWidgets.QMessageBox.StandardButton.Yes:
                self.SaveValue()

        try:
            self.input.setText(str(eval(input)))
        except SyntaxError:
            self.output.setText('Invalid input')
            pass
        except NameError:
            self.output.setText('Please input numeric characters')
            pass

    def buttonClick(self, event):
        self.input.setText(str(self.input.text()) + str(event))
        self.Calculate()
        self.input.setFocus()

    def discountClick(self):
        input = str(self.input.text())
        if not input:
            return

        #self.input.setText(str(eval(self.output.text())))

        text, ok = QtWidgets.QInputDialog.getText(
            self, 'Input Dialog', 'Enter percentage'
        )

        if ok:
            percentage = 1.00 + ((eval(str(text)) / 100.00))
            newInput = eval(str(self.input.text())) * percentage
            self.input.setText(str(newInput))
            self.Calculate()
            self.input.setFocus()
            return

    def clearInput(self):
        self.input.setText('')
        self.Calculate()
        self.input.setFocus()





