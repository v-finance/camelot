from customeditor import CustomEditor, QtCore, QtGui, Qt
from wideeditor import WideEditor
from camelot.view.art import Icon

class RichTextEditor(CustomEditor, WideEditor):
  
    def __init__(self, parent=None, editable=True, **kwargs):
        CustomEditor.__init__(self, parent)
        self.layout = QtGui.QVBoxLayout(self)
        self.layout.setSpacing(0)
        self.layout.setMargin(0)
        self.editable = editable
    
        class CustomTextEdit(QtGui.QTextEdit):
            """A TextEdit editor that sends editingFinished events when the text was changed
            and focus is lost
            """
            
            def __init__(self, parent):
                super(CustomTextEdit, self).__init__(parent)
                self._changed = False
                self.connect(self, QtCore.SIGNAL('textChanged()'), self.setTextChanged)
        
            def focusOutEvent(self, event):
                if self._changed:
                    self.emit(QtCore.SIGNAL('editingFinished()'))
              
            def textChanged(self):
                return self._changed
              
            def setTextChanged(self, state=True):
                self._changed = state
                
            def setHtml(self, html):
                QtGui.QTextEdit.setHtml(self, html)
                self._changed = False
                
        self.textedit = CustomTextEdit(self)
        
        self.connect(self.textedit,
                     QtCore.SIGNAL('editingFinished()'),
                     self.editingFinished)
        self.textedit.setAcceptRichText(True)
    
        if not self.editable:
            self.textedit.setReadOnly(True)
        else:
            self.initButtons(editable)
            
            
#      #
#      # Buttons setup
#      #
#      self.toolbar = QtGui.QToolBar(self)
#      self.toolbar.setContentsMargins(0, 0, 0, 0)
#      self.toolbar.setEnabled(editable)
#      
#      self.bold_button = QtGui.QToolButton(self)
#      icon = Icon('tango/16x16/actions/format-text-bold.png').getQIcon()
#      self.bold_button.setIcon(icon)
#      self.bold_button.setAutoRaise(True)
#      self.bold_button.setCheckable(True)
#      self.bold_button.setEnabled(editable)
#      self.bold_button.setMaximumSize(QtCore.QSize(20, 20))
#      self.bold_button.setShortcut(QtGui.QKeySequence('Ctrl+B'))
#      self.connect(self.bold_button, QtCore.SIGNAL('clicked()'), self.set_bold)
#
#      self.italic_button = QtGui.QToolButton(self)
#      icon = Icon('tango/16x16/actions/format-text-italic.png').getQIcon()
#      self.italic_button.setIcon(icon)
#      self.italic_button.setAutoRaise(True)
#      self.italic_button.setCheckable(True)
#      self.italic_button.setEnabled(editable)
#      self.italic_button.setMaximumSize(QtCore.QSize(20, 20))
#      self.italic_button.setShortcut(QtGui.QKeySequence('Ctrl+I'))
#      self.connect(self.italic_button,
#                   QtCore.SIGNAL('clicked(bool)'),
#                   self.set_italic)
#  
#      self.underline_button = QtGui.QToolButton(self)
#      icon = Icon('tango/16x16/actions/format-text-underline.png').getQIcon()
#      self.underline_button.setIcon(icon)
#      self.underline_button.setAutoRaise(True)
#      self.underline_button.setCheckable(True)
#      self.underline_button.setEnabled(editable)
#      self.underline_button.setMaximumSize(QtCore.QSize(20, 20))
#      self.underline_button.setShortcut(QtGui.QKeySequence('Ctrl+U'))
#      self.connect(self.underline_button,
#                   QtCore.SIGNAL('clicked(bool)'),
#                   self.set_underline)
#  
#      self.copy_button = QtGui.QToolButton(self)
#      icon = Icon('tango/16x16/actions/edit-copy.png').getQIcon()
#      self.copy_button.setIcon(icon)
#      self.copy_button.setAutoRaise(True)
#      self.copy_button.setEnabled(editable)
#      self.copy_button.setMaximumSize(QtCore.QSize(20, 20))
#      self.connect(self.copy_button,
#                   QtCore.SIGNAL('clicked(bool)'),
#                   self.textedit.copy)
#  
#      self.cut_button = QtGui.QToolButton(self)
#      icon = Icon('tango/16x16/actions/edit-cut.png').getQIcon()
#      self.cut_button.setIcon(icon)
#      self.cut_button.setAutoRaise(True)
#      self.cut_button.setEnabled(editable)
#      self.cut_button.setMaximumSize(QtCore.QSize(20, 20))
#      self.connect(self.cut_button,
#                   QtCore.SIGNAL('clicked(bool)'),
#                   self.textedit.cut)
#  
#      self.paste_button = QtGui.QToolButton(self)
#      icon = Icon('tango/16x16/actions/edit-paste.png').getQIcon()
#      self.paste_button.setIcon(icon)
#      self.paste_button.setAutoRaise(True)
#      self.paste_button.setEnabled(editable)
#      self.paste_button.setMaximumSize(QtCore.QSize(20, 20))
#      self.connect(self.paste_button,
#                   QtCore.SIGNAL('clicked(bool)'),
#                   self.textedit.paste)
#  
#      self.alignleft_button = QtGui.QToolButton(self)
#      icon = Icon('tango/16x16/actions/format-justify-left.png').getQIcon()
#      self.alignleft_button.setIcon(icon)
#      self.alignleft_button.setAutoRaise(True)
#      self.alignleft_button.setCheckable(True)
#      self.alignleft_button.setEnabled(editable)
#      self.alignleft_button.setMaximumSize(QtCore.QSize(20, 20))
#      self.connect(self.alignleft_button,
#                   QtCore.SIGNAL('clicked(bool)'),
#                   self.set_alignleft)   
#  
#      self.aligncenter_button = QtGui.QToolButton(self)
#      icon = Icon('tango/16x16/actions/format-justify-center.png').getQIcon()
#      self.aligncenter_button.setIcon(icon)
#      self.aligncenter_button.setAutoRaise(True)
#      self.aligncenter_button.setCheckable(True)
#      self.aligncenter_button.setEnabled(editable)
#      self.aligncenter_button.setMaximumSize(QtCore.QSize(20, 20))
#      self.connect(self.aligncenter_button,
#                   QtCore.SIGNAL('clicked(bool)'),
#                   self.set_aligncenter)
#  
#      self.alignright_button = QtGui.QToolButton(self)
#      icon = Icon('tango/16x16/actions/format-justify-right.png').getQIcon()
#      self.alignright_button.setIcon(icon)
#      self.alignright_button.setAutoRaise(True)
#      self.alignright_button.setCheckable(True)
#      self.alignright_button.setEnabled(editable)
#      self.alignright_button.setMaximumSize(QtCore.QSize(20, 20))
#      self.connect(self.alignright_button,
#                   QtCore.SIGNAL('clicked(bool)'),
#                   self.set_alignright)
#  
#      self.color_button = QtGui.QToolButton(self)
#      self.color_button.setAutoRaise(True)
#      self.color_button.setEnabled(editable)
#      self.color_button.setMaximumSize(QtCore.QSize(20, 20))
#      self.connect(self.color_button,
#                   QtCore.SIGNAL('clicked(bool)'),
#                   self.set_color)
# 
#      self.toolbar.addWidget(self.copy_button)
#      self.toolbar.addWidget(self.cut_button)
#      self.toolbar.addWidget(self.paste_button)
#      self.toolbar.addSeparator()
#      self.toolbar.addWidget(self.bold_button)
#      self.toolbar.addWidget(self.italic_button)      
#      self.toolbar.addWidget(self.underline_button) 
#      self.toolbar.addSeparator()
#      self.toolbar.addWidget(self.alignleft_button)
#      self.toolbar.addWidget(self.aligncenter_button)      
#      self.toolbar.addWidget(self.alignright_button)   
#      self.toolbar.addSeparator()
#      self.toolbar.addWidget(self.color_button)   
#      
#      #
#      # Layout
#      #
#      self.layout.addWidget(self.toolbar)
        self.layout.addWidget(self.textedit)
       
        self.setLayout(self.layout)
        
        #
        # Format
        #
        self.textedit.setFontWeight(QtGui.QFont.Normal)
        self.textedit.setFontItalic(False)
        self.textedit.setFontUnderline(False)
        self.textedit.setFocus(Qt.OtherFocusReason)
        self.textedit.setEnabled(editable)
        self.update_alignment()
    
        if self.editable:
            self.connect(self.textedit,
                         QtCore.SIGNAL('currentCharFormatChanged(const QTextCharFormat&)'),
                         self.update_format)
            self.connect(self.textedit,
                         QtCore.SIGNAL('cursorPositionChanged()'),
                         self.update_text)
                
    def editingFinished(self):
        if self.textedit.textChanged():
            self.emit(QtCore.SIGNAL('editingFinished()'))
            
        
        
        
        
        
    def initButtons(self, editable=True):
        self.toolbar = QtGui.QToolBar(self)
        self.toolbar.setContentsMargins(0, 0, 0, 0)
        self.toolbar.setEnabled(editable)
        
        self.bold_button = QtGui.QToolButton(self)
        icon = Icon('tango/16x16/actions/format-text-bold.png').getQIcon()
        self.bold_button.setIcon(icon)
        self.bold_button.setAutoRaise(True)
        self.bold_button.setCheckable(True)
        self.bold_button.setEnabled(editable)
        self.bold_button.setMaximumSize(QtCore.QSize(20, 20))
        self.bold_button.setShortcut(QtGui.QKeySequence('Ctrl+B'))
        self.connect(self.bold_button, QtCore.SIGNAL('clicked()'), self.set_bold)
    
        self.italic_button = QtGui.QToolButton(self)
        icon = Icon('tango/16x16/actions/format-text-italic.png').getQIcon()
        self.italic_button.setIcon(icon)
        self.italic_button.setAutoRaise(True)
        self.italic_button.setCheckable(True)
        self.italic_button.setEnabled(editable)
        self.italic_button.setMaximumSize(QtCore.QSize(20, 20))
        self.italic_button.setShortcut(QtGui.QKeySequence('Ctrl+I'))
        self.connect(self.italic_button,
                     QtCore.SIGNAL('clicked(bool)'),
                     self.set_italic)
    
        self.underline_button = QtGui.QToolButton(self)
        icon = Icon('tango/16x16/actions/format-text-underline.png').getQIcon()
        self.underline_button.setIcon(icon)
        self.underline_button.setAutoRaise(True)
        self.underline_button.setCheckable(True)
        self.underline_button.setEnabled(editable)
        self.underline_button.setMaximumSize(QtCore.QSize(20, 20))
        self.underline_button.setShortcut(QtGui.QKeySequence('Ctrl+U'))
        self.connect(self.underline_button,
                     QtCore.SIGNAL('clicked(bool)'),
                     self.set_underline)
    
        self.copy_button = QtGui.QToolButton(self)
        icon = Icon('tango/16x16/actions/edit-copy.png').getQIcon()
        self.copy_button.setIcon(icon)
        self.copy_button.setAutoRaise(True)
        self.copy_button.setEnabled(editable)
        self.copy_button.setMaximumSize(QtCore.QSize(20, 20))
        self.connect(self.copy_button,
                     QtCore.SIGNAL('clicked(bool)'),
                     self.textedit.copy)
    
        self.cut_button = QtGui.QToolButton(self)
        icon = Icon('tango/16x16/actions/edit-cut.png').getQIcon()
        self.cut_button.setIcon(icon)
        self.cut_button.setAutoRaise(True)
        self.cut_button.setEnabled(editable)
        self.cut_button.setMaximumSize(QtCore.QSize(20, 20))
        self.connect(self.cut_button,
                     QtCore.SIGNAL('clicked(bool)'),
                     self.textedit.cut)
    
        self.paste_button = QtGui.QToolButton(self)
        icon = Icon('tango/16x16/actions/edit-paste.png').getQIcon()
        self.paste_button.setIcon(icon)
        self.paste_button.setAutoRaise(True)
        self.paste_button.setEnabled(editable)
        self.paste_button.setMaximumSize(QtCore.QSize(20, 20))
        self.connect(self.paste_button,
                     QtCore.SIGNAL('clicked(bool)'),
                     self.textedit.paste)
    
        self.alignleft_button = QtGui.QToolButton(self)
        icon = Icon('tango/16x16/actions/format-justify-left.png').getQIcon()
        self.alignleft_button.setIcon(icon)
        self.alignleft_button.setAutoRaise(True)
        self.alignleft_button.setCheckable(True)
        self.alignleft_button.setEnabled(editable)
        self.alignleft_button.setMaximumSize(QtCore.QSize(20, 20))
        self.connect(self.alignleft_button,
                     QtCore.SIGNAL('clicked(bool)'),
                     self.set_alignleft)   
    
        self.aligncenter_button = QtGui.QToolButton(self)
        icon = Icon('tango/16x16/actions/format-justify-center.png').getQIcon()
        self.aligncenter_button.setIcon(icon)
        self.aligncenter_button.setAutoRaise(True)
        self.aligncenter_button.setCheckable(True)
        self.aligncenter_button.setEnabled(editable)
        self.aligncenter_button.setMaximumSize(QtCore.QSize(20, 20))
        self.connect(self.aligncenter_button,
                     QtCore.SIGNAL('clicked(bool)'),
                     self.set_aligncenter)
    
        self.alignright_button = QtGui.QToolButton(self)
        icon = Icon('tango/16x16/actions/format-justify-right.png').getQIcon()
        self.alignright_button.setIcon(icon)
        self.alignright_button.setAutoRaise(True)
        self.alignright_button.setCheckable(True)
        self.alignright_button.setEnabled(editable)
        self.alignright_button.setMaximumSize(QtCore.QSize(20, 20))
        self.connect(self.alignright_button,
                     QtCore.SIGNAL('clicked(bool)'),
                     self.set_alignright)
    
        self.color_button = QtGui.QToolButton(self)
        self.color_button.setAutoRaise(True)
        self.color_button.setEnabled(editable)
        self.color_button.setMaximumSize(QtCore.QSize(20, 20))
        self.connect(self.color_button,
                     QtCore.SIGNAL('clicked(bool)'),
                     self.set_color)
    
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
        # Layout
        #
        self.layout.addWidget(self.toolbar)
    
      
      
      
    def set_enabled(self, editable=True):
        if self.textedit.isEnabled() != editable:
            if not editable:
                self.layout().removeWidget(self.bold_button)
                self.layout().removeWidget(self.italic_button)
                self.layout().removeWidget(self.underline_button)
                self.layout().removeWidget(self.toolbar)
                self.layout().removeWidget(self.color_button)
                self.layout().removeWidget(self.aligncenter_button)
                self.layout().removeWidget(self.alignleft_button)
                self.layout().removeWidget(self.alignright_button)
                self.layout().removeWidget(self.copy_button)
                self.layout().removeWidget(self.cut_button)
                self.layout().removeWidget(self.paste_button)
            else:
                value = self.get_value()
                self.layout.removeWidget(self.textedit)
                self.initButtons(editable)
                self.layout.addWidget(self.textedit)
                self.set_value(value)
            self.textedit.setEnabled(editable)
          
        
      
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
        if self.editable:
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
        if self.editable:
            color = self.textedit.textColor()
            pixmap = QtGui.QPixmap(16, 16)
            pixmap.fill(color)
            self.color_button.setIcon(QtGui.QIcon(pixmap))
      
    def update_format(self, format):
        if self.editable:
            font = format.font()
            self.bold_button.setChecked(font.bold())
            self.italic_button.setChecked(font.italic())
            self.underline_button.setChecked(font.underline())
            self.update_alignment(self.textedit.alignment())
      
    def update_text(self):
        if self.editable:
            self.update_alignment()
            self.update_color()
      
    def get_value(self):
        from xml.dom import minidom
        tree = minidom.parseString(unicode(self.textedit.toHtml()))
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
