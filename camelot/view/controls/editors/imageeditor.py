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

from .fileeditor import FileEditor

from camelot.view.art import Icon
from camelot.view.controls.liteboxview import LiteBoxView
from camelot.view.model_thread import post
from camelot.view.action import ActionFactory

import six

from ....core.qt import QtGui, QtCore, Qt
from camelot.view.controls.decorated_line_edit import DecoratedLineEdit

class ImageEditor( FileEditor ):
    """Editor to view and edit image files, this is a customized
    implementation of a FileEditor"""

    filter = """Image files (*.bmp *.jpg *.jpeg *.mng *.png *.pbm *.pgm *.ppm *.tiff *.xbm *.xpm)
All files (*)"""

    def __init__( self,
                  parent=None,
                  storage=None,
                  preview_width=100,
                  preview_height=100,
                  field_name = 'image',
                  **kwargs ):
        self.preview_width = preview_width
        self.preview_height = preview_height
        FileEditor.__init__(
            self, parent=parent, storage=storage,
            **kwargs
        )
        self.setObjectName( field_name )        

    def setup_widget(self):
        layout = QtGui.QVBoxLayout()
        layout.setSpacing( 0 )
        label_button_layout = QtGui.QHBoxLayout()
        #
        # Setup label
        #
        self.label = QtGui.QLabel(self)
        self.label.installEventFilter(self)
        self.label.setAlignment( Qt.AlignHCenter|Qt.AlignVCenter )
        label_button_layout.addWidget(self.label)
        
        self.filename = DecoratedLineEdit( self )
        self.filename.setVisible( False )
        #
        # Setup buttons
        #
        button_layout = QtGui.QVBoxLayout()
        button_layout.setSpacing( 0 )
        button_layout.setContentsMargins( 0, 0, 0, 0)
        
        copy_button = QtGui.QToolButton()
        copy_button.setDefaultAction( ActionFactory.copy(self, self.copy_to_clipboard ) )
        copy_button.setAutoRaise(True)
        copy_button.setFocusPolicy(Qt.ClickFocus)

        paste_button = QtGui.QToolButton()
        paste_button.setDefaultAction( ActionFactory.paste(self, self.paste_from_clipboard ) )
        paste_button.setAutoRaise(True)
        paste_button.setObjectName('paste')
        paste_button.setFocusPolicy(Qt.ClickFocus)
        
        #button_layout.addStretch()
        self.add_actions(self.actions, button_layout)
        button_layout.addWidget(copy_button)
        button_layout.addWidget(paste_button)

        label_button_layout.addLayout(button_layout)
        label_button_layout.addStretch()
        layout.addLayout( label_button_layout )
        #layout.addStretch()
        self.setLayout( layout )
        self.clear_image()
        QtGui.QApplication.clipboard().dataChanged.connect( self.clipboard_data_changed )
        self.clipboard_data_changed()
        
    @QtCore.pyqtSlot()
    def clipboard_data_changed(self):
        paste_button = self.findChild(QtGui.QWidget, 'paste')
        if paste_button:
            mime_data = QtGui.QApplication.clipboard().mimeData()
            paste_button.setVisible( mime_data.hasImage() )
            
    @QtCore.pyqtSlot()
    def paste_from_clipboard(self):
        """Paste an image from the clipboard into the editor"""
        mime_data = QtGui.QApplication.clipboard().mimeData()
        if mime_data.hasImage():
            byte_array = QtCore.QByteArray()
            buffer = QtCore.QBuffer( byte_array )
            image = QtGui.QImage( mime_data.imageData() )
            image.save( buffer, 'PNG' )
            
            def create_checkin( byte_array ):
                return lambda:self.checkin_byte_array(byte_array, '.png')
            
            post( create_checkin( byte_array ), self.stored_file_ready )
        
    def checkin_byte_array(self, byte_array, suffix):
        """Check a byte_array into the storage"""
        stream = six.StringIO( byte_array.data() )
        return self.storage.checkin_stream( 'clipboard', suffix, stream)
        
    def set_enabled(self, editable=True):
        self.label.setEnabled(editable)

    def set_pixmap(self, pixmap):
        self.label.setPixmap(pixmap)
        self.draw_border()

    def set_image(self, image):
        self.set_pixmap(QtGui.QPixmap.fromImage(image))
        
    @QtCore.pyqtSlot()
    def copy_to_clipboard(self):
        """Copy the image to the clipboard"""
        if self.value:
            post( self.value.checkout_image, self.set_image_to_clipboard )
        
    def set_image_to_clipboard(self, image):
        clipboard = QtGui.QApplication.clipboard()
        clipboard.setImage( image )

    def clear_image(self):
        dummy_image = Icon('tango/32x32/mimetypes/image-x-generic.png')
        self.set_pixmap(dummy_image.getQPixmap())

    def set_value(self, value):
        old_value = self.value
        value = super( ImageEditor, self ).set_value( value )
        if value is not None:
            if value != old_value:
                post(
                    lambda:value.checkout_thumbnail(
                        self.preview_width,
                        self.preview_height
                    ),
                    self.set_image
                )
        else:
            self.clear_image()
        return value

    def draw_border(self):
        self.label.setFrameShape(QtGui.QFrame.Box)
        self.label.setFrameShadow(QtGui.QFrame.Plain)
        self.label.setLineWidth(1)
        self.label.setFixedSize(self.preview_width, self.preview_height)

    def show_fullscreen(self, image):
        lite_box = LiteBoxView(self)
        lite_box.show_fullscreen_image(image)

    def eventFilter(self, object, event):
        if not object.isWidgetType():
            return False
        if event.type() != QtCore.QEvent.MouseButtonPress:
            return False
        if event.modifiers() != QtCore.Qt.NoModifier:
            return False
        if event.buttons() == QtCore.Qt.LeftButton:
            if self.value:
                post(
                    lambda:self.value.checkout_thumbnail(640,480),
                    self.show_fullscreen
                )
            return True
        return False
