from PyQt4 import QtCore, QtGui
from PyQt4.QtCore import Qt

from customeditor import CustomEditor
from camelot.view.art import Icon

class StarEditor(CustomEditor):

    def __init__(self, parent, maximum=5, editable=True, **kwargs):
        CustomEditor.__init__(self, parent)
        self.setFocusPolicy(Qt.StrongFocus)
        layout = QtGui.QHBoxLayout(self)
        layout.setMargin(0)
        layout.setSpacing(0)
        self.starIcon = Icon('tango/16x16/status/weather-clear.png').getQIcon()
        self.noStarIcon = Icon('tango/16x16/status/weather-clear-noStar.png').getQIcon()
        self.setAutoFillBackground(True)
        #self.starCount = maximum
        self.starCount = 5
        self.buttons = []
        for i in range(self.starCount):
            button = QtGui.QToolButton(self)
            button.setIcon(self.noStarIcon)
            if editable:
                button.setAutoRaise(True)
            else:
                button.setAutoRaise(True)
                button.setDisabled(True)
            button.setFixedHeight(self.get_height())
            self.buttons.append(button)
      
        def createStarClick(i):
            return lambda:self.starClick(i+1)
      
        for i in range(self.starCount):
            self.connect(self.buttons[i],
                         QtCore.SIGNAL('clicked()'),
                         createStarClick(i))
        for i in range(self.starCount):
            layout.addWidget(self.buttons[i])
        layout.addStretch()
        self.setLayout(layout)
    
    def get_value(self):
        return CustomEditor.get_value(self) or self.stars
      
      
    def set_enabled(self, editable=True):
        for button in self.buttons:
            button.setEnabled(editable)
            button.update()
        self.set_value(self.stars)
    
    def starClick(self, value):
        if self.stars == value:
            self.stars -= 1
        else:
            self.stars = int(value)
        for i in range(self.starCount):
            if i+1 <= self.stars:
                self.buttons[i].setIcon(self.starIcon)
            else:
                self.buttons[i].setIcon(self.noStarIcon)
        self.emit(QtCore.SIGNAL('editingFinished()'))
    
    def set_value(self, value):
        value = CustomEditor.set_value(self, value) or 0
        self.stars = int(value)
        for i in range(self.starCount):
            if i+1 <= self.stars:
                self.buttons[i].setIcon(self.starIcon)
            else:
                self.buttons[i].setIcon(self.noStarIcon)
