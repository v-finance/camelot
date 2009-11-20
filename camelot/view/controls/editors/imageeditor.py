from fileeditor import FileEditor, CustomEditor
from wideeditor import WideEditor
from camelot.view.art import Icon

from PyQt4 import QtGui, QtCore
from PyQt4.QtCore import Qt
from camelot.core.utils import ugettext_lazy as _

class ImageEditor(FileEditor, WideEditor):
    """Editor to view and edit image files, this is a customized implementation
    of a FileEditor"""
    
    filter = """Image files (*.bmp *.jpg *.jpeg *.mng *.png *.pbm *.pgm *.ppm *.tiff *.xbm *.xpm)
All files (*)"""
    
    def __init__(self, 
                 parent=None, 
                 editable=True, 
                 storage=None,
                 preview_width=100,
                 preview_height=100, 
                 **kwargs):
        self.preview_width = preview_width
        self.preview_height = preview_height
        FileEditor.__init__(self, parent=parent, storage=storage, editable=editable, **kwargs)
      
    def setup_widget(self):
        self.layout = QtGui.QHBoxLayout()
        self.layout.setContentsMargins( 0, 0, 0, 0 )
        #
        # Setup label
        #
        self.label = QtGui.QLabel(self)
        self.label.setEnabled(self.editable)
        self.layout.addWidget(self.label)
        self.label.setAlignment(Qt.AlignHCenter|Qt.AlignVCenter)
        #
        # Setup buttons
        #
        button_layout = QtGui.QVBoxLayout()
        button_layout.setSpacing(0)
        button_layout.setMargin(0)
        
        self.open_button = QtGui.QToolButton()
        self.open_button.setIcon(self.open_icon)
        self.open_button.setEnabled(self.editable)
        self.open_button.setAutoRaise(True)
        self.open_button.setToolTip(unicode(_('open image')))
        self.connect(self.open_button, QtCore.SIGNAL('clicked()'), self.open_button_clicked)
        
        self.clear_button = QtGui.QToolButton()
        self.clear_button.setIcon(self.clear_icon)
        self.clear_button.setEnabled(self.editable)
        self.clear_button.setToolTip(unicode(_('delete image')))
        self.clear_button.setAutoRaise(True)
        self.connect(self.clear_button, QtCore.SIGNAL('clicked()'), self.clear_button_clicked)

        button_layout.addStretch() 
        button_layout.addWidget(self.open_button)
        button_layout.addWidget(self.clear_button)    
        
        self.layout.addLayout(button_layout)
        self.layout.addStretch()                
        self.setLayout(self.layout)
        self.clear_image()
      
    def set_enabled(self, editable=True):
        self.clear_button.setEnabled(editable)
        self.open_button.setEnabled(editable)
              
    def set_pixmap(self, pixmap):
        self.label.setPixmap(pixmap)      
        self.draw_border()
        
    def set_image(self, image):
        self.set_pixmap(QtGui.QPixmap.fromImage(image))
    
    def clear_image(self):
        dummy_image = Icon('tango/32x32/mimetypes/image-x-generic.png')
        self.set_pixmap(dummy_image.getQPixmap())
              
    def set_value(self, value):
        value = CustomEditor.set_value(self, value)
        if value:
            self.open_button.setIcon(self.open_icon)
            self.open_button.setToolTip(unicode(_('open file')))
            if value!=self.value:
                from camelot.view.model_thread import post
                post(lambda:value.checkout_thumbnail(self.preview_width,self.preview_height), self.set_image)            
        else:
            self.clear_image()
            self.open_button.setIcon(self.new_icon)
            self.open_button.setToolTip(unicode(_('add file')))
        self.value = value
        return value
    
    def draw_border(self):
        self.label.setFrameShape(QtGui.QFrame.Box)
        self.label.setFrameShadow(QtGui.QFrame.Plain)
        self.label.setLineWidth(1)
        self.label.setFixedSize(self.preview_width, self.preview_height)
