#  ============================================================================
#
#  Copyright (C) 2007-2012 Conceptive Engineering bvba. All rights reserved.
#  www.conceptive.be / project-camelot@conceptive.be
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
#  visit www.python-camelot.com or contact project-camelot@conceptive.be
#
#  This file is provided AS IS with NO WARRANTY OF ANY KIND, INCLUDING THE
#  WARRANTY OF DESIGN, MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE.
#
#  For use of this library in commercial applications, please contact
#  project-camelot@conceptive.be
#
#  ============================================================================

from PyQt4 import QtGui
from PyQt4 import QtCore
from PyQt4.QtCore import Qt
from wideeditor import WideEditor
from customeditor import CustomEditor
from camelot.view.art import Icon

class CustomTextEdit(QtGui.QTextEdit):
    """
    A TextEdit editor that sends editingFinished events 
    when the text was changed and focus is lost.
    """

    editingFinished = QtCore.pyqtSignal()
    receivedFocus = QtCore.pyqtSignal()
    
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
        QtGui.QTextEdit.setHtml(self, html)
        self._changed = False
                
class RichTextEditor(CustomEditor, WideEditor):

    def __init__(self, 
                 parent = None, 
                 field_name = 'richtext',
                 **kwargs):
        CustomEditor.__init__(self, parent)
        self.setObjectName( field_name )
        self.layout = QtGui.QVBoxLayout(self)
        self.layout.setSpacing(0)
        self.layout.setContentsMargins( 0, 0, 0, 0)
        self.setSizePolicy( QtGui.QSizePolicy.Expanding,
                            QtGui.QSizePolicy.Expanding )

        self.textedit = CustomTextEdit(self)

        self.initToolbar() # Has to be invoked before the connect's below.
        self.toolbar.hide() # Should only be visible when textedit is focused.
        
        self.textedit.editingFinished.connect(self.emit_editing_finished)
        self.textedit.receivedFocus.connect(self.toolbar.show)
        self.textedit.setAcceptRichText(True)
        
        # Layout
        self.layout.addWidget(self.toolbar)
        self.layout.addWidget(self.textedit)
        self.setLayout(self.layout)

        # Format
        self.textedit.setFontWeight(QtGui.QFont.Normal)
        self.textedit.setFontItalic(False)
        self.textedit.setFontUnderline(False)
        #self.textedit.setFocus(Qt.OtherFocusReason)
        self.update_alignment()
        self.textedit.currentCharFormatChanged.connect(self.update_format)
        self.textedit.cursorPositionChanged.connect(self.update_text)

    @QtCore.pyqtSlot()
    def emit_editing_finished(self):
        if self.textedit._changed:
            self.editingFinished.emit()

    def set_editable(self, editable):
        self.textedit.setReadOnly(not editable)

    def set_field_attributes(self, editable=True, background_color=None, **kwargs):
        self.set_editable(editable)
        self.set_background_color(background_color)

    def initToolbar(self):
        self.toolbar = QtGui.QToolBar(self)
        self.toolbar.setOrientation(Qt.Horizontal)
        self.toolbar.setContentsMargins(0, 0, 0, 0)

        self.bold_button = QtGui.QToolButton(self)
        icon = Icon('tango/16x16/actions/format-text-bold.png').getQIcon()
        self.bold_button.setIcon(icon)
        self.bold_button.setAutoRaise(True)
        self.bold_button.setCheckable(True)
        self.bold_button.setFocusPolicy( Qt.ClickFocus )
        self.bold_button.setMaximumSize(QtCore.QSize(20, 20))
        self.bold_button.setShortcut(QtGui.QKeySequence('Ctrl+B'))
        self.bold_button.setToolTip('Bold')
        self.bold_button.clicked.connect(self.set_bold)

        self.italic_button = QtGui.QToolButton(self)
        icon = Icon('tango/16x16/actions/format-text-italic.png').getQIcon()
        self.italic_button.setIcon(icon)
        self.italic_button.setAutoRaise(True)
        self.italic_button.setCheckable(True)
        self.italic_button.setFocusPolicy( Qt.ClickFocus )
        self.italic_button.setMaximumSize(QtCore.QSize(20, 20))
        self.italic_button.setShortcut(QtGui.QKeySequence('Ctrl+I'))
        self.italic_button.setToolTip('Italic')
        self.italic_button.clicked.connect(self.set_italic)

        self.underline_button = QtGui.QToolButton(self)
        icon = Icon('tango/16x16/actions/format-text-underline.png').getQIcon()
        self.underline_button.setIcon(icon)
        self.underline_button.setAutoRaise(True)
        self.underline_button.setCheckable(True)
        self.underline_button.setFocusPolicy( Qt.ClickFocus )
        self.underline_button.setMaximumSize(QtCore.QSize(20, 20))
        self.underline_button.setShortcut(QtGui.QKeySequence('Ctrl+U'))
        self.underline_button.setToolTip('Underline')
        self.underline_button.clicked.connect(self.set_underline)

        self.copy_button = QtGui.QToolButton(self)
        icon = Icon('tango/16x16/actions/edit-copy.png').getQIcon()
        self.copy_button.setIcon(icon)
        self.copy_button.setAutoRaise(True)
        self.copy_button.setMaximumSize(QtCore.QSize(20, 20))
        self.copy_button.setFocusPolicy( Qt.ClickFocus )
        self.copy_button.setToolTip('Copy')
        self.copy_button.clicked.connect(self.textedit.copy)

        self.cut_button = QtGui.QToolButton(self)
        icon = Icon('tango/16x16/actions/edit-cut.png').getQIcon()
        self.cut_button.setIcon(icon)
        self.cut_button.setAutoRaise(True)
        self.cut_button.setMaximumSize(QtCore.QSize(20, 20))
        self.cut_button.setToolTip('Cut')
        self.cut_button.clicked.connect(self.textedit.cut)
        self.cut_button.setFocusPolicy( Qt.ClickFocus )

        self.paste_button = QtGui.QToolButton(self)
        icon = Icon('tango/16x16/actions/edit-paste.png').getQIcon()
        self.paste_button.setIcon(icon)
        self.paste_button.setAutoRaise(True)
        self.paste_button.setMaximumSize(QtCore.QSize(20, 20))
        self.paste_button.setFocusPolicy( Qt.ClickFocus )
        self.paste_button.setToolTip('Paste')
        self.paste_button.clicked.connect(self.textedit.paste)

        self.alignleft_button = QtGui.QToolButton(self)
        icon = Icon('tango/16x16/actions/format-justify-left.png').getQIcon()
        self.alignleft_button.setIcon(icon)
        self.alignleft_button.setAutoRaise(True)
        self.alignleft_button.setCheckable(True)
        self.alignleft_button.setMaximumSize(QtCore.QSize(20, 20))
        self.alignleft_button.setFocusPolicy( Qt.ClickFocus )
        self.alignleft_button.setToolTip('Align left')
        self.alignleft_button.clicked.connect(self.set_alignleft)

        self.aligncenter_button = QtGui.QToolButton(self)
        icon = Icon('tango/16x16/actions/format-justify-center.png').getQIcon()
        self.aligncenter_button.setIcon(icon)
        self.aligncenter_button.setAutoRaise(True)
        self.aligncenter_button.setCheckable(True)
        self.aligncenter_button.setMaximumSize(QtCore.QSize(20, 20))
        self.aligncenter_button.setFocusPolicy( Qt.ClickFocus )
        self.aligncenter_button.setToolTip('Align Center')
        self.aligncenter_button.clicked.connect(self.set_aligncenter)

        self.alignright_button = QtGui.QToolButton(self)
        icon = Icon('tango/16x16/actions/format-justify-right.png').getQIcon()
        self.alignright_button.setIcon(icon)
        self.alignright_button.setAutoRaise(True)
        self.alignright_button.setCheckable(True)
        self.alignright_button.setMaximumSize(QtCore.QSize(20, 20))
        self.alignright_button.setFocusPolicy( Qt.ClickFocus )
        self.alignright_button.setToolTip('Align Right')
        self.alignright_button.clicked.connect(self.set_alignright)

        self.color_button = QtGui.QToolButton(self)
        self.color_button.setAutoRaise(True)
        self.color_button.setMaximumSize(QtCore.QSize(20, 20))
        self.color_button.setFocusPolicy( Qt.ClickFocus )
        self.color_button.setToolTip('Color')
        self.color_button.clicked.connect(self.set_color)

        self.toolbar.addWidget(self.copy_button)
        self.toolbar.addWidget(self.cut_button)
        self.toolbar.addWidget(self.paste_button)
        self.toolbar.addSeparator()
        self.toolbar.addWidget(self.bold_button)
        self.toolbar.addWidget(self.italic_button)
        self.toolbar.addWidget(self.underline_button)
        self.toolbar.addSeparator()
        self.toolbar.addWidget(self.alignleft_button)
        self.toolbar.addWidget(self.aligncenter_button)
        self.toolbar.addWidget(self.alignright_button)
        self.toolbar.addSeparator()
        self.toolbar.addWidget(self.color_button)

    #
    # Button methods
    #
    def set_bold(self):
        if self.bold_button.isChecked():
            self.textedit.setFocus(Qt.OtherFocusReason)
            self.textedit.setFontWeight(QtGui.QFont.Bold)
        else:
            self.textedit.setFocus(Qt.OtherFocusReason)
            self.textedit.setFontWeight(QtGui.QFont.Normal)

    def set_italic(self, bool):
        if bool:
            self.textedit.setFocus(Qt.OtherFocusReason)
            self.textedit.setFontItalic(True)
        else:
            self.textedit.setFocus(Qt.OtherFocusReason)
            self.textedit.setFontItalic(False)

    def set_underline(self, bool):
        if bool:
            self.textedit.setFocus(Qt.OtherFocusReason)
            self.textedit.setFontUnderline(True)
        else:
            self.textedit.setFocus(Qt.OtherFocusReason)
            self.textedit.setFontUnderline(False)


    def set_alignleft(self, bool):
        if bool:
            self.textedit.setFocus(Qt.OtherFocusReason)
            self.textedit.setAlignment(Qt.AlignLeft)
        self.update_alignment(Qt.AlignLeft)

    def set_aligncenter(self, bool):
        if bool:
            self.textedit.setFocus(Qt.OtherFocusReason)
            self.textedit.setAlignment(Qt.AlignCenter)
        self.update_alignment(Qt.AlignCenter)

    def set_alignright(self, bool):
        if bool:
            self.textedit.setFocus(Qt.OtherFocusReason)
            self.textedit.setAlignment(Qt.AlignRight)
        self.update_alignment(Qt.AlignRight)

    def update_alignment(self, al=None):
        if al is None:
            al = self.textedit.alignment()
        if al == Qt.AlignLeft:
            self.alignleft_button.setChecked(True)
            self.aligncenter_button.setChecked(False)
            self.alignright_button.setChecked(False)
        elif al == Qt.AlignCenter:
            self.aligncenter_button.setChecked(True)
            self.alignleft_button.setChecked(False)
            self.alignright_button.setChecked(False)
        elif al == Qt.AlignRight:
            self.alignright_button.setChecked(True)
            self.alignleft_button.setChecked(False)
            self.aligncenter_button.setChecked(False)

    def set_color(self):
        color = QtGui.QColorDialog.getColor(self.textedit.textColor())
        if color.isValid():
            self.textedit.setFocus(Qt.OtherFocusReason)
            self.textedit.setTextColor(color)
            pixmap = QtGui.QPixmap(16, 16)
            pixmap.fill(color)
            self.color_button.setIcon(QtGui.QIcon(pixmap))

    def update_color(self):
        color = self.textedit.textColor()
        pixmap = QtGui.QPixmap(16, 16)
        pixmap.fill(color)
        self.color_button.setIcon(QtGui.QIcon(pixmap))

    def update_format(self, format):
        font = format.font()
        self.bold_button.setChecked(font.bold())
        self.italic_button.setChecked(font.italic())
        self.underline_button.setChecked(font.underline())
        self.update_alignment(self.textedit.alignment())

    def update_text(self):
        self.update_alignment()
        self.update_color()

    def get_value(self):
        from xml.dom import minidom
        tree = minidom.parseString(unicode(self.textedit.toHtml()).encode('utf-8'))
        value = u''.join([node.toxml() for node in tree.getElementsByTagName('html')[0].getElementsByTagName('body')[0].childNodes])
        return CustomEditor.get_value(self) or value

    def set_value(self, value):
        value = CustomEditor.set_value(self, value)
        if value!=None:
            if unicode(self.textedit.toHtml())!=value:
                self.update_alignment()
                self.textedit.setHtml(value)
                self.update_color()
        else:
            self.textedit.clear()



