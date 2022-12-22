import os

from ....admin.icon import Icon
from ....view.art import FontIcon
from ....view.action import ActionFactory
from ....core.qt import QtCore, QtWidgets, Qt, QtGui
from ....core.utils import ugettext as _

from .customeditor import CustomEditor

class DbImageEditor(CustomEditor):   
    """
    :param max_size: Size of allowed images in bytes, defaults to 50Kb
    """

    image_filter = "Images (*.bmp *.jpg *.jpeg *.mng *.png *.pbm *.pgm *.ppm *.tiff *.xbm *.xpm);; All files (*.*)"

    def __init__(self,
                 parent,
                 preview_width=100,
                 preview_height=100,
                 max_size=50000,
                 field_name='db_image'):
        self.preview_width = preview_width
        self.preview_height = preview_height
        self.max_size = max_size
        CustomEditor.__init__(self, parent)
        
        layout = QtWidgets.QHBoxLayout()
        
        #
        # Setup label
        #
        self.label = QtWidgets.QLabel(self)
        self.label.installEventFilter(self)
        self.label.setAlignment( Qt.AlignmentFlag.AlignHCenter|Qt.AlignmentFlag.AlignVCenter )
        layout.addWidget(self.label) 
                
        # Setup buttons
        button_layout = QtWidgets.QVBoxLayout()
        button_layout.setSpacing( 0 )
        button_layout.setContentsMargins( 0, 0, 0, 0)
    
        open_button = QtWidgets.QToolButton()
        open_button.setAutoRaise(True)
        open_button.setFocusPolicy(Qt.FocusPolicy.ClickFocus)
        open_button.setDefaultAction( ActionFactory.create_action(text=_('Open'),
                                                                      slot=self.open,
                                                                      parent=self,
                                                                      actionicon=Icon('plus'), # 'tango/16x16/actions/list-add.png'
                                                                      tip=_('Attach file')))        
    
        clear_button = QtWidgets.QToolButton()
        clear_button.setAutoRaise(True)
        clear_button.setObjectName('clear')
        clear_button.setFocusPolicy(Qt.FocusPolicy.ClickFocus)
        clear_button.setDefaultAction( ActionFactory.create_action(text=_('Clear'),
                                                                   slot=self.clear,
                                                                   parent=self,
                                                                   actionicon=Icon('trash'), # 'tango/16x16/actions/edit-clear.png'
                                                                   tip=_('clear')))
    
        copy_button = QtWidgets.QToolButton()
        copy_button.setDefaultAction( ActionFactory.copy(self, self.copy_to_clipboard ) )
        copy_button.setAutoRaise(True)
        copy_button.setObjectName('copy')
        copy_button.setFocusPolicy(Qt.FocusPolicy.ClickFocus)
    
        paste_button = QtWidgets.QToolButton()
        paste_button.setDefaultAction( ActionFactory.paste(self, self.paste_from_clipboard ) )
        paste_button.setAutoRaise(True)
        paste_button.setObjectName('paste')
        paste_button.setFocusPolicy(Qt.FocusPolicy.ClickFocus)
    
        button_layout.addWidget(open_button)
        button_layout.addWidget(clear_button)
        button_layout.addWidget(copy_button)
        button_layout.addWidget(paste_button)
        button_layout.addStretch()
    
        layout.addLayout(button_layout)
        
        self.setObjectName(field_name)
        self.setLayout( layout )
        self.clear_image()
        QtWidgets.QApplication.clipboard().dataChanged.connect( self.clipboard_data_changed )
        self.clipboard_data_changed()        
        
        if self.preview_width != 0:
            self.label.setMinimumWidth(self.preview_width)
        if self.preview_height != 0:
            self.label.setFixedHeight(self.preview_height)
            vertical_size_policy = QtWidgets.QSizePolicy.Policy.Fixed
        self.setSizePolicy(QtWidgets.QSizePolicy.Policy.Expanding, vertical_size_policy)
        self.label.setSizePolicy(QtWidgets.QSizePolicy.Policy.Expanding, vertical_size_policy)
   
    def set_value(self, value):
        value = CustomEditor.set_value(self, value)
        self.value = value
        clear_button = self.findChild(QtWidgets.QWidget, 'clear')
        copy_button = self.findChild(QtWidgets.QWidget, 'copy')
        clear_button.setVisible(value is not None)
        copy_button.setVisible(value is not None)
        if value is not None:
            image = QtGui.QImage()
            byte_array = QtCore.QByteArray.fromBase64( value.encode() )
            image.loadFromData( byte_array )
            thumbnail = image.scaled(self.preview_width, self.preview_height, Qt.AspectRatioMode.KeepAspectRatio)
            self.set_image(thumbnail)
        else:
            self.clear_image()               
        return value
    
    def get_value(self):
        return CustomEditor.get_value(self) or self.value
    
    @QtCore.qt_slot()
    def clear(self): 
        self.set_value(None)
        self.editingFinished.emit()
    
    @QtCore.qt_slot()
    def paste_from_clipboard(self):
        """Paste an image from the clipboard into the editor"""
        mime_data = QtWidgets.QApplication.clipboard().mimeData()
        if mime_data.hasImage():
            image = QtGui.QImage( mime_data.imageData())
            ba = QtCore.QByteArray()
            buffer = QtCore.QBuffer(ba)
            buffer.open(QtCore.QIODevice.OpenModeFlag.WriteOnly)
            image.save(buffer, 'PNG')
            image_data = ba.toBase64().data().decode()
            self.set_value(image_data)
            self.editingFinished.emit()
    
    @QtCore.qt_slot()
    def clipboard_data_changed(self):
        paste_button = self.findChild(QtWidgets.QWidget, 'paste')
        if paste_button:
            mime_data = QtWidgets.QApplication.clipboard().mimeData()
            if mime_data is not None:
                paste_button.setVisible( mime_data.hasImage() )    
    
    @QtCore.qt_slot()
    def copy_to_clipboard(self):
        """Copy the image to the clipboard"""
        if self.value:
            image = QtGui.QImage()
            byte_array = QtCore.QByteArray.fromBase64( self.value.encode() )
            image.loadFromData( byte_array )            
            self.set_image_to_clipboard(image)
    
    @QtCore.qt_slot()
    def open(self):
        file_name, _filter = QtWidgets.QFileDialog.getOpenFileName(self,_('New image'), "", self.image_filter)
        if file_name:
            statinfo = os.stat(file_name)
            image_size = statinfo.st_size         
            
            if image_size <= self.max_size:
                image_reader = QtGui.QImageReader()
                image_reader.setDecideFormatFromContent(True)
                image_reader.setFileName(file_name)
                image = image_reader.read()
                if not image.isNull():
                    ba = QtCore.QByteArray()
                    buffer = QtCore.QBuffer(ba)
                    buffer.open(QtCore.QIODevice.OpenModeFlag.WriteOnly)
                    image.save(buffer, 'PNG')
                    image_data = ba.toBase64().data().decode()
                    self.set_value(image_data)
                    self.editingFinished.emit()
                else:
                    QtWidgets.QMessageBox.warning(self, _('Uploading failed'), _('Chosen file was not recognized as a valid image'))
            else: 
                QtWidgets.QMessageBox.warning(self, _('Uploading failed'), _('Image is too big! Maximum allowed file size: {0}kb').format(self.max_size/1000))
    
    def set_image_to_clipboard(self, image):
        clipboard = QtWidgets.QApplication.clipboard()
        clipboard.setImage( image )

    def clear_image(self):
        dummy_image = FontIcon('image') # 'tango/32x32/mimetypes/image-x-generic.png'
        self.set_pixmap(dummy_image.getQPixmap())
        
    def set_pixmap(self, pixmap):
        self.label.setPixmap(pixmap)
        self.draw_border()
    
    def draw_border(self):
        self.label.setFrameShape(QtWidgets.QFrame.Shape.Box)
        self.label.setFrameShadow(QtWidgets.QFrame.Shadow.Plain)
        self.label.setLineWidth(1)   
    
    def set_image(self, image):
        self.set_pixmap(QtGui.QPixmap.fromImage(image))   
        
    def eventFilter(self, object, event):
        if not object.isWidgetType():
            return False
        if event.type() != QtCore.QEvent.Type.MouseButtonPress:
            return False
        if event.modifiers() != QtCore.Qt.KeyboardModifier.NoModifier:
            return False
        return False    
