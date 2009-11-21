
from PyQt4 import QtGui, QtCore
from PyQt4.QtCore import Qt

from customeditor import CustomEditor, editingFinished
from camelot.view.art import Icon
from camelot.core.utils import ugettext as _

class FileEditor(CustomEditor):
    """Widget for editing File fields"""
  
    filter = """All files (*)"""
    
    def __init__(self, parent=None, storage=None, editable=True, **kwargs):
        CustomEditor.__init__(self, parent)
        self.storage = storage
        self.editable = editable
        self.document_pixmap = Icon('tango/16x16/mimetypes/x-office-document.png').getQPixmap()
        self.clear_icon = Icon('tango/16x16/actions/edit-delete.png').getQIcon()
        self.new_icon = Icon('tango/16x16/actions/list-add.png').getQIcon()
        self.open_icon = Icon('tango/16x16/actions/document-open.png').getQIcon()
        self.saveas_icon = Icon('tango/16x16/actions/document-save-as.png').getQIcon()
        self.value = None
        self.setup_widget()
        if self.editable:
            self.setAcceptDrops(True)
    
    def setup_widget(self):
        """Called inside init, overwrite this method for custom
        file edit widgets"""
        self.layout = QtGui.QHBoxLayout()
        self.layout.setSpacing(0)
        self.layout.setMargin(0)
        
        # Clear button
        self.clear_button = QtGui.QToolButton()
        self.clear_button.setFocusPolicy(Qt.ClickFocus)
        self.clear_button.setIcon(self.clear_icon)
        self.clear_button.setToolTip(_('delete file'))
        self.clear_button.setAutoRaise(True)
        self.clear_button.setEnabled(self.editable)
        self.connect(self.clear_button,
                     QtCore.SIGNAL('clicked()'),
                     self.clear_button_clicked)
        
        # Open button
        self.open_button = QtGui.QToolButton()
        self.open_button.setFocusPolicy(Qt.ClickFocus)
        self.open_button.setIcon(self.new_icon)
        self.open_button.setToolTip(_('add file'))
        self.open_button.setEnabled(self.editable)
        self.connect(self.open_button,
                     QtCore.SIGNAL('clicked()'),
                     self.open_button_clicked)
        self.open_button.setAutoRaise(True)
        
        # Filename
        self.filename = QtGui.QLineEdit(self)
        self.filename.setEnabled(self.editable  )
        self.filename.setReadOnly(not self.editable)
        
        # Setup layout
        self.document_label = QtGui.QLabel(self)
        self.document_label.setPixmap(self.document_pixmap)
        self.document_label.setEnabled(self.editable)
        self.layout.addWidget(self.document_label)
        self.layout.addWidget(self.filename)
        self.layout.addWidget(self.clear_button)
        self.layout.addWidget(self.open_button)
        self.setLayout(self.layout)      
    
    def set_value(self, value):
        value = CustomEditor.set_value(self, value)
        self.value = value
        if value:
            self.filename.setText(value.verbose_name)
            self.open_button.setIcon(self.open_icon)
            self.open_button.setToolTip(_('open file'))
        else:
            self.filename.setText('')
            self.open_button.setIcon(self.new_icon)
            self.open_button.setToolTip(_('add file'))
        return value
        
    def get_value(self):
        return CustomEditor.get_value(self) or self.value
    
    def set_enabled(self, editable=True):
        self.clear_button.setEnabled(editable)
        self.open_button.setEnabled(editable)
        self.filename.setEnabled(editable)
        self.document_label.setEnabled(editable)
    
    def stored_file_ready(self, stored_file):
        """Slot to be called when a new stored_file has been created by
        the storeage"""
        self.set_value(stored_file)
        self.emit(editingFinished)        
        
    def open_button_clicked(self):
        from camelot.view.storage import open_stored_file, create_stored_file
        if not self.value:
            create_stored_file(self, self.storage, self.stored_file_ready, filter=self.filter)
        else:
            open_stored_file(self, self.value)
    
    def clear_button_clicked(self):
        self.value = None
        self.emit(editingFinished)

    #
    # Drag & Drop
    #
    def dragEnterEvent(self, event):
        event.acceptProposedAction()
    
    def dragMoveEvent(self, event):
        event.acceptProposedAction()
    
    def dropEvent(self, event):
        if event.mimeData().hasUrls():
            url = event.mimeData().urls()[0]
            filename = url.toLocalFile()
            if filename != '':
                from camelot.view.storage import SaveFileProgressDialog
                from camelot.view.model_thread import post
                progress = SaveFileProgressDialog()
                
                def checkin():
                    stored_file = self.storage.checkin(str(filename))
                    return lambda:self.stored_file_ready(stored_file)

                post(checkin, progress.finish)
                progress.exec_()
