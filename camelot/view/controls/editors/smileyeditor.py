from PyQt4 import QtCore, QtGui
from PyQt4.QtCore import Qt

from customeditor import CustomEditor
from camelot.view.art import Icon

class SmileyEditor(CustomEditor):

    def __init__(self, parent, img='face-plain', editable=True, **kwargs):
        CustomEditor.__init__(self, parent)
        
        
    
        
        self.box = QtGui.QComboBox()
        
        self.box.setFrame(True)
        self.box.setEditable(False)
        
        
        self.allSmileys = []
        
        self.allSmileys.append('face-angel')
        self.allSmileys.append('face-crying')
        self.allSmileys.append('face-devil-grin')
        self.allSmileys.append('face-glasses')
        self.allSmileys.append('face-grin')
        self.allSmileys.append('face-kiss')
        self.allSmileys.append('face-monkey')
        self.allSmileys.append('face-plain')
        self.allSmileys.append('face-sad')
        self.allSmileys.append('face-smile')
        self.allSmileys.append('face-smile-big')
        self.allSmileys.append('face-surprise')
        self.allSmileys.append('face-wink')
        
        for i, value in enumerate(self.allSmileys):
            imgPath = 'tango/16x16/emotes/' + value + '.png'        
            icon = Icon(imgPath).getQIcon()
            
            self.box.addItem(icon, '')
            self.box.setFixedHeight(self.get_height())
            
            if value == 'face-plain':
                self.box.setCurrentIndex(i)
        
        
        self.setFocusPolicy(Qt.StrongFocus)
        layout = QtGui.QHBoxLayout(self)
        layout.setMargin(0)
        layout.setSpacing(0)
        self.img = img
        self.imgPath = 'tango/16x16/emotes/' + img + '.png'
        self.Icon = Icon(self.imgPath).getQIcon()
        self.setAutoFillBackground(True)
        #self.starCount = maximum
        if not editable:
            self.box.setEnabled(False)
        else:
            self.box.setEnabled(True)
      
      
        self.connect(self.box,
                     QtCore.SIGNAL('currentIndexChanged()'),
                     self.smileyChanged)
    
    
        layout.addWidget(self.box)
        layout.addStretch()
        self.setLayout(layout)
    
    def get_value(self):
        imgIndex = self.box.currentIndex() 
        
        for i, emot in enumerate(self.allSmileys):
            if imgIndex == i:
                imgName = emot
                
        return CustomEditor.get_value(self) or imgName
      
      
    def set_enabled(self, editable=True):
        self.box.setEnabled(editable)
    
    def smileyChanged(self):
      
        value = self.box.currentIndex()  
        
        for i, emot in enumerate(self.allSmileys):
            if value == i:
                imgName = emot
                
        self.emit(QtCore.SIGNAL('editingFinished()'), imgName)
    
    def set_value(self, value):
        value = CustomEditor.set_value(self, value) or 'face-plain'
        self.img = value
        #self.imgPath = 'tango/16x16/emotes/' + self.img + '.png'
        
        for i, smiley in enumerate(self.allSmileys):
            if smiley == self.img:
                self.box.setCurrentIndex(i)
                
        
        
