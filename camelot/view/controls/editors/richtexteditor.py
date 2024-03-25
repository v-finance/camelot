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



from ....core.qt import QtGui, QtCore, QtWidgets, Qt
from .wideeditor import WideEditor
from .customeditor import CustomEditor
from camelot.view.art import FontIcon

class CustomTextEdit(QtWidgets.QTextEdit):
    """
    A TextEdit editor that sends editingFinished events
    when the text was changed and focus is lost.
    """

    editingFinished = QtCore.qt_signal()
    receivedFocus = QtCore.qt_signal()

    def __init__(self, parent):
        super(CustomTextEdit, self).__init__(parent)
        self._changed = False
        self.setTabChangesFocus( True )
        self.textChanged.connect( self._handle_text_changed )

    def focusInEvent(self, event):
        super(CustomTextEdit, self).focusInEvent( event )
        self.receivedFocus.emit()

    def focusOutEvent(self, event):
        if self._changed:
            self.editingFinished.emit()
        super(CustomTextEdit, self).focusOutEvent( event )

    def _handle_text_changed(self):
        self._changed = True

    def setTextChanged(self, state=True):
        self._changed = state

    def setHtml(self, html):
        QtWidgets.QTextEdit.setHtml(self, html)
        self._changed = False

class RichTextEditor(CustomEditor, WideEditor):

    def __init__(self,
                 parent = None,
                 field_name = 'richtext'):
        CustomEditor.__init__(self, parent)
        self.setObjectName( field_name )
        self.layout = QtWidgets.QVBoxLayout(self)
        self.layout.setSpacing(0)
        self.layout.setContentsMargins( 0, 0, 0, 0)
        self.setSizePolicy( QtWidgets.QSizePolicy.Policy.Expanding,
                            QtWidgets.QSizePolicy.Policy.Expanding )

        self.textedit = CustomTextEdit(self)

        toolbar = self.initToolbar() # Has to be invoked before the connect's below.
        toolbar.hide() # Should only be visible when textedit is focused.

        self.textedit.editingFinished.connect(self.emit_editing_finished)
        self.textedit.receivedFocus.connect(toolbar.show)
        self.textedit.setAcceptRichText(True)

        # Layout
        self.layout.addWidget(toolbar)
        self.layout.addWidget(self.textedit)
        self.setLayout(self.layout)

        # Format
        self.textedit.setFontWeight(QtGui.QFont.Weight.Normal)
        self.textedit.setFontItalic(False)
        self.textedit.setFontUnderline(False)


    @QtCore.qt_slot()
    def emit_editing_finished(self):
        if self.textedit._changed:
            self.editingFinished.emit()

    def set_editable(self, editable):
        toolbar = self.findChild( QtWidgets.QToolBar )
        if toolbar:
            toolbar.setEnabled(editable)
        self.textedit.setEnabled(editable)
        self.textedit.setReadOnly( not editable )

    def set_toolbar_hidden( self, hidden ):
        """Show or hide the toolbar, by default the toolbar is hidden until
        the user starts editing.
        :param hidden: `True` or `False`
        """
        toolbar = self.findChild( QtWidgets.QToolBar )
        if toolbar:
            toolbar.setHidden( hidden )

    def initToolbar(self):
        toolbar = QtWidgets.QToolBar(self)
        toolbar.setObjectName( 'toolbar' )
        toolbar.setOrientation(Qt.Orientation.Horizontal)
        toolbar.setContentsMargins(0, 0, 0, 0)

        bold_button = QtWidgets.QToolButton(self)
        icon = FontIcon('bold').getQIcon() # 'tango/16x16/actions/format-text-bold.png'
        bold_button.setIcon(icon)
        bold_button.setMaximumSize(QtCore.QSize(20, 20))
        bold_button.setShortcut(QtGui.QKeySequence('Ctrl+B'))
        bold_button.setToolTip('Bold')
        bold_button.clicked.connect(self.set_bold)

        italic_button = QtWidgets.QToolButton(self)
        icon = FontIcon('italic').getQIcon()  #'tango/16x16/actions/format-text-italic.png'
        italic_button.setIcon(icon)
        italic_button.setMaximumSize(QtCore.QSize(20, 20))
        italic_button.setShortcut(QtGui.QKeySequence('Ctrl+I'))
        italic_button.setToolTip('Italic')
        italic_button.clicked.connect(self.set_italic)

        underline_button = QtWidgets.QToolButton(self)
        icon = FontIcon('underline').getQIcon() # 'tango/16x16/actions/format-text-underline.png'
        underline_button.setIcon(icon)
        underline_button.setMaximumSize(QtCore.QSize(20, 20))
        underline_button.setShortcut(QtGui.QKeySequence('Ctrl+U'))
        underline_button.setToolTip('Underline')
        underline_button.clicked.connect(self.set_underline)

        copy_button = QtWidgets.QToolButton(self)
        icon = FontIcon('copy').getQIcon() # 'tango/16x16/actions/edit-copy.png'
        copy_button.setIcon(icon)
        copy_button.setMaximumSize(QtCore.QSize(20, 20))
        copy_button.setToolTip('Copy')
        copy_button.clicked.connect(self.textedit.copy)

        cut_button = QtWidgets.QToolButton(self)
        icon = FontIcon('cut').getQIcon() # 'tango/16x16/actions/edit-cut.png'
        cut_button.setIcon(icon)
        cut_button.setMaximumSize(QtCore.QSize(20, 20))
        cut_button.setToolTip('Cut')
        cut_button.clicked.connect(self.textedit.cut)

        paste_button = QtWidgets.QToolButton(self)
        icon = FontIcon('paste').getQIcon() # 'tango/16x16/actions/edit-paste.png'
        paste_button.setIcon(icon)
        paste_button.setMaximumSize(QtCore.QSize(20, 20))
        paste_button.setToolTip('Paste')
        paste_button.clicked.connect(self.textedit.paste)

        alignleft_button = QtWidgets.QToolButton(self)
        icon = FontIcon('align-left').getQIcon() # 'tango/16x16/actions/format-justify-left.png'
        alignleft_button.setIcon(icon)
        alignleft_button.setMaximumSize(QtCore.QSize(20, 20))
        alignleft_button.setToolTip('Align left')
        alignleft_button.clicked.connect(self.set_alignleft)

        aligncenter_button = QtWidgets.QToolButton(self)
        icon = FontIcon('align-center').getQIcon() # 'tango/16x16/actions/format-justify-center.png'
        aligncenter_button.setIcon(icon)
        aligncenter_button.setMaximumSize(QtCore.QSize(20, 20))
        aligncenter_button.setToolTip('Align Center')
        aligncenter_button.clicked.connect(self.set_aligncenter)

        alignright_button = QtWidgets.QToolButton(self)
        icon = FontIcon('align-right').getQIcon() # 'tango/16x16/actions/format-justify-right.png'
        alignright_button.setIcon(icon)
        alignright_button.setMaximumSize(QtCore.QSize(20, 20))
        alignright_button.setToolTip('Align Right')
        alignright_button.clicked.connect(self.set_alignright)

        zoomin_button = QtWidgets.QToolButton(self)
        icon = FontIcon('search-plus').getQIcon() # 'tango/16x16/actions/list-add.png'
        zoomin_button.setIcon(icon)
        zoomin_button.setMaximumSize(QtCore.QSize(20, 20))
        zoomin_button.setToolTip('Zoom in')
        zoomin_button.clicked.connect(self.zoomin)

        zoomout_button = QtWidgets.QToolButton(self)
        icon = FontIcon('search-minus').getQIcon() # 'tango/16x16/actions/list-remove.png'
        zoomout_button.setIcon(icon)
        zoomout_button.setMaximumSize(QtCore.QSize(20, 20))
        zoomout_button.setToolTip('Zoom out')
        zoomout_button.clicked.connect(self.zoomout)

        color_button = QtWidgets.QToolButton(self)
        color_button.setMaximumSize(QtCore.QSize(20, 20))
        color_button.setToolTip('Color')
        pixmap = QtGui.QPixmap(16, 16)
        pixmap.fill(QtGui.QColor('black'))
        color_button.setIcon(QtGui.QIcon(pixmap))
        color_button.clicked.connect(self.set_color)

        toolbar.addWidget(copy_button)
        toolbar.addWidget(cut_button)
        toolbar.addWidget(paste_button)
        toolbar.addSeparator()
        toolbar.addWidget(bold_button)
        toolbar.addWidget(italic_button)
        toolbar.addWidget(underline_button)
        toolbar.addSeparator()
        toolbar.addWidget(alignleft_button)
        toolbar.addWidget(aligncenter_button)
        toolbar.addWidget(alignright_button)
        toolbar.addSeparator()
        toolbar.addWidget(color_button)
        toolbar.addSeparator()
        toolbar.addWidget(zoomin_button)
        toolbar.addWidget(zoomout_button)
        return toolbar

    #
    # Button methods
    #
    def set_bold(self):
        font = self.textedit.currentFont()
        if not font.bold():
            self.textedit.setFontWeight(QtGui.QFont.Weight.Bold)
        else:
            self.textedit.setFontWeight(QtGui.QFont.Weight.Normal)

    def set_italic(self, bool):
        font = self.textedit.currentFont()
        self.textedit.setFontItalic(not font.italic())

    def set_underline(self, bool):
        font = self.textedit.currentFont()
        self.textedit.setFontUnderline(not font.underline())

    def zoomin( self ):
        self.textedit.zoomIn()

    def zoomout( self ):
        self.textedit.zoomOut()

    def set_alignleft(self, bool):
        self.textedit.setAlignment(Qt.AlignmentFlag.AlignLeft)

    def set_aligncenter(self, bool):
        self.textedit.setAlignment(Qt.AlignmentFlag.AlignCenter)

    def set_alignright(self, bool):
        self.textedit.setAlignment(Qt.AlignmentFlag.AlignRight)

    def set_color(self):
        color = QtWidgets.QColorDialog.getColor(self.textedit.textColor())
        if color.isValid():
            self.textedit.setTextColor(color)

    def get_value(self):
        if self.textedit.toPlainText()=='':
            return None
        from xml.dom import minidom
        tree = minidom.parseString(str(self.textedit.toHtml()).encode('utf-8'))
        value = u''.join([node.toxml() for node in tree.getElementsByTagName('html')[0].getElementsByTagName('body')[0].childNodes])
        return value

    def set_document( self, document ):
        """
        :param document: a :class:`QtGui.QTextDocument` object.
        """
        self.textedit.setDocument( document )

    def set_value( self, value ):
        if value is not None:
            if str(self.textedit.toHtml())!=value:
                self.textedit.setHtml(value)
        else:
            self.textedit.clear()


