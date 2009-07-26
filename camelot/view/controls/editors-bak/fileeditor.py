
from customeditor import *
from camelot.view.art import Icon

class FileEditor(CustomEditor):
  """Widget for editing File fields"""
  
  def __init__(self, parent=None, storage=None, **kwargs):
    CustomEditor.__init__(self, parent)
    self.storage = storage
    self.document_pixmap = Icon('tango/16x16/mimetypes/x-office-document.png').getQPixmap()
    self.clear_icon = Icon('tango/16x16/actions/edit-delete.png').getQIcon()
    self.new_icon = Icon('tango/16x16/actions/list-add.png').getQIcon()
    self.open_icon = Icon('tango/16x16/actions/document-open.png').getQIcon()
    self.saveas_icon = Icon('tango/16x16/actions/document-save-as.png').getQIcon()
  
    self.value = None
    self.layout = QtGui.QHBoxLayout()
    self.layout.setSpacing(0)
    self.layout.setMargin(0)

    # Clear button
    self.clear_button = QtGui.QToolButton()
    self.clear_button.setFocusPolicy(Qt.ClickFocus)
    self.clear_button.setIcon(self.clear_icon)
    self.clear_button.setToolTip('Delete file')
    self.clear_button.setAutoRaise(True)
    self.connect(self.clear_button,
                 QtCore.SIGNAL('clicked()'),
                 self.clearButtonClicked)

    # Open button
    self.open_button = QtGui.QToolButton()
    self.open_button.setFocusPolicy(Qt.ClickFocus)
    self.open_button.setIcon(self.new_icon)
    self.open_button.setToolTip('Add file')
    self.connect(self.open_button,
                 QtCore.SIGNAL('clicked()'),
                 self.openButtonClicked)
    self.open_button.setAutoRaise(True)
    
#    self.saveas_button = QtGui.QToolButton()
#    self.saveas_button = QtGui.QToolButton()
#    self.saveas_button.setFocusPolicy(Qt.ClickFocus)
#    self.saveas_button.setIcon(self.saveas_icon)
#    self.connect(self.saveas_button,
#                 QtCore.SIGNAL('clicked()'),
#                 self.saveasButtonClicked)
#    self.saveas_button.setAutoRaise(True)
    
    # Filename
    self.filename = QtGui.QLineEdit(self)
    self.filename.setEnabled(False)
    self.filename.setReadOnly(True)
    
    # Setup layout
    document_label = QtGui.QLabel(self)
    document_label.setPixmap(self.document_pixmap)
    self.layout.addWidget(document_label)
    self.layout.addWidget(self.filename)
    self.layout.addWidget(self.clear_button)
    self.layout.addWidget(self.open_button)
    self.setLayout(self.layout)
    self.setAutoFillBackground(True)
    
  def set_value(self, value):
    value = CustomEditor.set_value(self, value)
    self.value = value
    if value:
      self.filename.setText(value.verbose_name)
      self.open_button.setIcon(self.open_icon)
      self.open_button.setToolTip('Open file')
    else:
      self.filename.setText('')
      self.open_button.setIcon(self.new_icon)
      self.open_button.setToolTip('Add file')
      
  def get_value(self):
    return CustomEditor.get_value(self) or self.value
  
  def openButtonClicked(self):
    from camelot.view.storage import open_stored_file, create_stored_file
    if not self.value:
      
      def on_finish(stored_file):
        self.set_value(stored_file)
        self.emit(editingFinished)
        
      create_stored_file(self, self.storage, on_finish)
    else:
      open_stored_file(self, self.value)
  
  def clearButtonClicked(self):
    self.value = None
    self.emit(editingFinished)
