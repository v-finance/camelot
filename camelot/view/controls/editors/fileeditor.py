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



from ....core.qt import QtWidgets, Qt
from .customeditor import CustomEditor, set_background_color_palette

from camelot.view.art import FontIcon

from camelot.view.controls.decorated_line_edit import DecoratedLineEdit

class FileEditor(CustomEditor):
    """Widget for editing File fields"""

    document_pixmap = FontIcon('edit', 16) # 'tango/16x16/mimetypes/x-office-document.png'
        
    def __init__(self,
                 parent=None,
                 action_routes=[],
                 field_name='file'):
        CustomEditor.__init__(self, parent)
        self.setSizePolicy( QtWidgets.QSizePolicy.Policy.Preferred,
                            QtWidgets.QSizePolicy.Policy.Fixed )
        self.setObjectName( field_name )
        self.filename = None # the widget containing the filename
        self.value = None
        self.file_name = None
        self.setup_widget()
        self.add_actions(action_routes, self.layout())

    def setup_widget(self):
        """Called inside init, overwrite this method for custom
        file edit widgets"""
        layout = QtWidgets.QHBoxLayout()
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)

        # Filename
        self.filename = DecoratedLineEdit( self )
        self.filename.set_minimum_width( 20 )
        self.filename.setFocusPolicy( Qt.FocusPolicy.ClickFocus )

        # Setup layout
        self.document_label = QtWidgets.QLabel(self)
        self.document_label.setPixmap(self.document_pixmap.getQPixmap())
        layout.addWidget(self.document_label)
        layout.addWidget(self.filename)
        self.setLayout(layout)

    def set_value(self, value):
        self.value = value
        if value is not None:
            self.filename.setText(value)
        else:
            self.filename.setText('')
        return value

    def get_value(self):
        return self.value

    def set_tooltip(self, tooltip):
        super().set_tooltip(tooltip)
        if self.filename:
            self.filename.setToolTip(str(tooltip or ''))

    def set_background_color(self, background_color):
        super().set_background_color(background_color)
        if self.filename:
            set_background_color_palette(self.filename, background_color)

    def set_editable(self, editable):
        self.set_enabled(editable)

    def set_enabled(self, editable=True):
        self.filename.setEnabled(editable)
        self.filename.setReadOnly(not editable)
        self.document_label.setEnabled(editable)
        self.setAcceptDrops(editable)