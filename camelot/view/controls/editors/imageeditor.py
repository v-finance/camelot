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

from .fileeditor import FileEditor

from camelot.view.art import Icon
from camelot.view.model_thread import post
from camelot.view.action import ActionFactory

import six

from ....core.qt import QtGui, QtWidgets, QtCore, Qt
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
        layout = QtWidgets.QHBoxLayout()
        #
        # Setup label
        #
        self.label = QtWidgets.QLabel(self)
        self.label.installEventFilter(self)
        self.label.setAlignment( Qt.AlignHCenter|Qt.AlignVCenter )
        layout.addWidget(self.label)
        
        self.filename = DecoratedLineEdit( self )
        self.filename.setVisible( False )
        #
        # Setup buttons
        #
        button_layout = QtWidgets.QVBoxLayout()
        button_layout.setSpacing( 0 )
        button_layout.setContentsMargins( 0, 0, 0, 0)
        
        copy_button = QtWidgets.QToolButton()
        copy_button.setDefaultAction( ActionFactory.copy(self, self.copy_to_clipboard ) )
        copy_button.setAutoRaise(True)
        copy_button.setFocusPolicy(Qt.ClickFocus)

        paste_button = QtWidgets.QToolButton()
        paste_button.setDefaultAction( ActionFactory.paste(self, self.paste_from_clipboard ) )
        paste_button.setAutoRaise(True)
        paste_button.setObjectName('paste')
        paste_button.setFocusPolicy(Qt.ClickFocus)
        
        self.add_actions(self.actions, button_layout)
        button_layout.addWidget(copy_button)
        button_layout.addWidget(paste_button)
        button_layout.addStretch()

        layout.addLayout(button_layout)
        #label_button_layout.addStretch()
        self.setLayout( layout )
        self.clear_image()
        QtWidgets.QApplication.clipboard().dataChanged.connect( self.clipboard_data_changed )
        self.clipboard_data_changed()

        # horizontal policy is always expanding, to fill the width of a column
        # in a form
        vertical_size_policy = QtWidgets.QSizePolicy.Expanding

        if self.preview_width != 0:
            self.label.setMinimumWidth(self.preview_width)
        if self.preview_height != 0:
            self.label.setFixedHeight(self.preview_height)
            vertical_size_policy = QtWidgets.QSizePolicy.Fixed
        self.setSizePolicy(QtWidgets.QSizePolicy.Expanding, vertical_size_policy)
        self.label.setSizePolicy(QtWidgets.QSizePolicy.Expanding, vertical_size_policy)
        
    @QtCore.qt_slot()
    def clipboard_data_changed(self):
        paste_button = self.findChild(QtWidgets.QWidget, 'paste')
        if paste_button:
            mime_data = QtWidgets.QApplication.clipboard().mimeData()
            paste_button.setVisible( mime_data.hasImage() )
            
    @QtCore.qt_slot()
    def paste_from_clipboard(self):
        """Paste an image from the clipboard into the editor"""
        mime_data = QtWidgets.QApplication.clipboard().mimeData()
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
        self.setAcceptDrops(editable)

    def set_pixmap(self, pixmap):
        self.label.setPixmap(pixmap)
        self.draw_border()

    def set_image(self, image):
        self.set_pixmap(QtGui.QPixmap.fromImage(image))
        
    @QtCore.qt_slot()
    def copy_to_clipboard(self):
        """Copy the image to the clipboard"""
        if self.value:
            post( self.value.checkout_image, self.set_image_to_clipboard )
        
    def set_image_to_clipboard(self, image):
        clipboard = QtWidgets.QApplication.clipboard()
        clipboard.setImage( image )

    def clear_image(self):
        dummy_image = Icon('tango/32x32/mimetypes/image-x-generic.png')
        self.set_pixmap(dummy_image.getQPixmap())

    def set_value(self, value):
        value = super( ImageEditor, self ).set_value( value )
        if value is not None:
            if value.name != self.file_name:
                if self.preview_height and self.preview_width:
                    post(
                        lambda:value.checkout_thumbnail(
                            self.preview_width,
                            self.preview_height
                        ),
                        self.set_image
                    )
                else:
                    post(
                        lambda:value.checkout_image(),
                        self.set_image
                    )
                # store the file name of which a previous is shown in the editor,
                # to ensure the preview is updated when this changes
                self.file_name = value.name
        else:
            self.clear_image()
        return value

    def draw_border(self):
        self.label.setFrameShape(QtWidgets.QFrame.Box)
        self.label.setFrameShadow(QtWidgets.QFrame.Plain)
        self.label.setLineWidth(1)
