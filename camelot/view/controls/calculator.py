from camelot.view.art import Icon
from PyQt4 import QtGui
from PyQt4 import QtCore


class Calculator(QtGui.QDialog):
    def __init__(self, parent=None):
        QtGui.QDialog.__init__(self, parent)
        mainLayout = QtGui.QVBoxLayout()
        topLeftLayout = QtGui.QVBoxLayout()
        topRightLayout = QtGui.QHBoxLayout()
        bottomRightLayout = QtGui.QHBoxLayout()
        bottomLayout = QtGui.QGridLayout()
    
        self.setWindowTitle('Live Calculator')
    
    
        self.input = QtGui.QLineEdit(self)
      
  
    
        self.connect(self.input, QtCore.SIGNAL('textEdited(const QString&)'), self.Calculate)
        #self.connect(self.input, QtCore.SIGNAL('returnPressed()'), self.ShowCalculate)
  
        
        
        #BUTTONS---
        
        self.equals = QtGui.QPushButton('=', self)
        self.discount = QtGui.QPushButton('Discount', self)
        self.save = QtGui.QPushButton('&Save', self)
        self.cancel = QtGui.QPushButton('Cancel', self)
        
        
        
        self.zero = QtGui.QPushButton('0', self)
        self.one = QtGui.QPushButton('1', self)
        self.two = QtGui.QPushButton('2', self)
        self.three = QtGui.QPushButton('3', self)
        self.four = QtGui.QPushButton('4', self)
        self.five = QtGui.QPushButton('5', self)
        self.six = QtGui.QPushButton('6', self)
        self.seven = QtGui.QPushButton('7', self)
        self.eight = QtGui.QPushButton('8', self)
        self.nine = QtGui.QPushButton('9', self)
        
        self.clear = QtGui.QPushButton('&Clear', self)
        
        self.backspace = QtGui.QToolButton()
        icon = Icon('tango/16x16/actions/go-previous.png').getQIcon()
        self.backspace.setIcon(icon)
        self.backspace.setAutoRaise(True)
        
        self.plus = QtGui.QPushButton('+', self)
        self.min = QtGui.QPushButton('-', self)
        self.multiply = QtGui.QPushButton('x', self)
        self.devide = QtGui.QPushButton('/', self)
        self.comma = QtGui.QPushButton(',', self)
        
        
        #Button-Connects---
        
        self.connect(self.equals, QtCore.SIGNAL('clicked()'), self.ShowCalculate)
        self.connect(self.zero, QtCore.SIGNAL('clicked()'), lambda:self.buttonClick(0))
        self.connect(self.one, QtCore.SIGNAL('clicked()'), lambda:self.buttonClick(1))
        self.connect(self.two, QtCore.SIGNAL('clicked()'), lambda:self.buttonClick(2))
        self.connect(self.three, QtCore.SIGNAL('clicked()'), lambda:self.buttonClick(3))
        self.connect(self.four, QtCore.SIGNAL('clicked()'), lambda:self.buttonClick(4))
        self.connect(self.five, QtCore.SIGNAL('clicked()'), lambda:self.buttonClick(5))
        self.connect(self.six, QtCore.SIGNAL('clicked()'), lambda:self.buttonClick(6))
        self.connect(self.seven, QtCore.SIGNAL('clicked()'), lambda:self.buttonClick(7))
        self.connect(self.eight, QtCore.SIGNAL('clicked()'), lambda:self.buttonClick(8))
        self.connect(self.nine, QtCore.SIGNAL('clicked()'), lambda:self.buttonClick(9))
        self.connect(self.plus, QtCore.SIGNAL('clicked()'), lambda:self.buttonClick('+'))
        self.connect(self.min, QtCore.SIGNAL('clicked()'), lambda:self.buttonClick('-'))
        self.connect(self.multiply, QtCore.SIGNAL('clicked()'), lambda:self.buttonClick('*'))
        self.connect(self.devide, QtCore.SIGNAL('clicked()'), lambda:self.buttonClick('/'))
        self.connect(self.clear, QtCore.SIGNAL('clicked()'), self.clearInput)
        self.connect(self.backspace, QtCore.SIGNAL('clicked()'), lambda:self.input.backspace())
        self.connect(self.comma, QtCore.SIGNAL('clicked()'), lambda:self.buttonClick('.'))
        self.connect(self.cancel, QtCore.SIGNAL('clicked()'), lambda:self.close())
        self.connect(self.save, QtCore.SIGNAL('clicked()'), self.SaveValue)
        self.connect(self.discount, QtCore.SIGNAL('clicked()'), self.discountClick)
        
        
        
        
        
        self.output = QtGui.QLabel(self)
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
        #QtGui.QWidget.keyPressEvent(self, event)

        key = event.key()
        if key == QtCore.Qt.Key_S:
            self.SaveValue()
            return
        else:
            QtGui.QDialog.keyPressEvent(self, event)
        
      
  
    def SaveValue(self):
        self.emit(QtCore.SIGNAL('calculationFinished'), str(self.output.text()))
        
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
        except SyntaxError, _e:
            pass
        except NameError, _e:
            self.output.setText('Please input numeric characters')
            pass
        
    def ShowCalculate(self):
        input = str(self.input.text())
        if not input:
            self.output.setText('')
            return
        
        
        if input == str(self.output.text()):
            reply = QtGui.QMessageBox.question(self, 'Message',
                                               "Do you want to Save and Quit?", QtGui.QMessageBox.Yes, QtGui.QMessageBox.No)
            
            if reply == QtGui.QMessageBox.Yes:
                self.SaveValue()
              
          
        try:
            self.input.setText(str(eval(input)))
        except SyntaxError, _e:
            self.output.setText('Invalid input')
            pass
        except NameError, _e:
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
  
        text, ok = QtGui.QInputDialog.getText(self, 'Input Dialog', 'Enter percentage')
  
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
