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
from PyQt4.QtCore import Qt

from customeditor import CustomEditor, set_background_color_palette

from camelot.view.art import Icon
from camelot.core.utils import ugettext as _

from camelot.view.controls.decorated_line_edit import DecoratedLineEdit

class FileEditor(CustomEditor):
    """Widget for editing File fields"""

    filter = 'All files (*)'
    add_icon = Icon( 'tango/16x16/actions/list-add.png' )
    open_icon = Icon( 'tango/16x16/actions/document-open.png' )
    clear_icon = Icon( 'tango/16x16/actions/edit-delete.png' )
    save_as_icon = Icon( 'tango/16x16/actions/document-save-as.png' )
    document_pixmap = Icon( 'tango/16x16/mimetypes/x-office-document.png' )
        
    def __init__(self, parent=None, 
                 storage=None, 
                 field_name='file', 
                 remove_original=False, 
                 **kwargs):
        CustomEditor.__init__(self, parent)
        self.setObjectName( field_name )
        self.storage = storage
        self.filename = None # the widget containing the filename
        self.value = None
        self.remove_original = remove_original
        self.setup_widget()

    def setup_widget(self):
        """Called inside init, overwrite this method for custom
        file edit widgets"""
        self.layout = QtGui.QHBoxLayout()
        self.layout.setSpacing(0)
        self.layout.setContentsMargins(0, 0, 0, 0)

        # Save As button
        self.save_as_button = QtGui.QToolButton()
        self.save_as_button.setFocusPolicy( Qt.ClickFocus )
        self.save_as_button.setIcon(self.save_as_icon.getQIcon())
        self.save_as_button.setToolTip(_('Save file as'))
        self.save_as_button.setAutoRaise(True)
        self.save_as_button.clicked.connect(self.save_as_button_clicked)

        # Clear button
        self.clear_button = QtGui.QToolButton()
        self.clear_button.setFocusPolicy( Qt.ClickFocus )
        self.clear_button.setIcon(self.clear_icon.getQIcon())
        self.clear_button.setToolTip(_('Delete file'))
        self.clear_button.setAutoRaise(True)
        self.clear_button.clicked.connect(self.clear_button_clicked)

        # Open button
        self.open_button = QtGui.QToolButton()
        self.open_button.setFocusPolicy( Qt.ClickFocus )
        self.open_button.setIcon(self.open_icon.getQIcon())
        self.open_button.setToolTip(_('Open file'))
        self.open_button.clicked.connect(self.open_button_clicked)
        self.open_button.setAutoRaise(True)
        
        # Add button
        self.add_button = QtGui.QToolButton()
        self.add_button.setFocusPolicy( Qt.StrongFocus )
        self.add_button.setIcon(self.add_icon.getQIcon())
        self.add_button.setToolTip(_('Attach file'))
        self.add_button.clicked.connect(self.add_button_clicked)
        self.add_button.setAutoRaise(True)

        # Filename
        self.filename = DecoratedLineEdit( self )
        self.filename.set_minimum_width( 20 )
        self.filename.setFocusPolicy( Qt.ClickFocus )

        # Search Completer
        #
        # Turn completion off, since it creates a thread per field on a form
        #
        # self.completer = QtGui.QCompleter()
        # self.completions_model = QtGui.QFileSystemModel()
        # self.completer.setCompletionMode(
        #    QtGui.QCompleter.UnfilteredPopupCompletion
        # )        
        # self.completer.setModel( self.completions_model )
        # self.completer.activated[QtCore.QModelIndex].connect(self.file_completion_activated)
        # self.filename.setCompleter( self.completer )
        # settings = QtCore.QSettings()
        # last_path = settings.value('lastpath').toString()
        
        # # This setting of a rootPath causes a major delay on Windows, since 
        # # the QFileSystemModel starts to fetch file information in a non-
        # # blocking way (although the documentation state the opposite).
        # # On Linux, there is no such delay, so it's safe to set such a root
        # # path and let the underlaying system start indexing.
        # import sys
        # if sys.platform != "win32":
        #    self.completions_model.setRootPath( last_path )

        # Setup layout
        self.document_label = QtGui.QLabel(self)
        self.document_label.setPixmap(self.document_pixmap.getQPixmap())
        self.layout.addWidget(self.document_label)
        self.layout.addWidget(self.filename)
        self.layout.addWidget(self.clear_button)
        self.layout.addWidget(self.open_button)
        self.layout.addWidget(self.add_button)
        self.layout.addWidget(self.save_as_button)
        self.setLayout(self.layout)

    def file_completion_activated(self, index):
        from camelot.view.storage import create_stored_file
        source_index = index.model().mapToSource( index )
        if not self.completions_model.isDir( source_index ):
            path = self.completions_model.filePath( source_index )
            create_stored_file(
                self,
                self.storage,
                self.stored_file_ready,
                filter=self.filter,
                remove_original=self.remove_original,
                filename = path,
            )

    def set_value(self, value):
        value = CustomEditor.set_value(self, value)
        self.value = value
        if value:
            self.clear_button.setVisible(True)
            self.save_as_button.setVisible(True)
            self.open_button.setVisible(True)
            self.add_button.setVisible(False)
            self.filename.setText(value.verbose_name)
        else:
            self.clear_button.setVisible(False)
            self.save_as_button.setVisible(False)
            self.open_button.setVisible(False)
            self.add_button.setVisible(True)
            self.filename.setText('')
        return value

    def get_value(self):
        return CustomEditor.get_value(self) or self.value

    def set_field_attributes(self, editable = True,
                                   background_color = None,
                                   tooltip = None,
                                   remove_original = False, **kwargs):
        self.set_enabled(editable)
        if self.filename:
            set_background_color_palette( self.filename, background_color )
            self.filename.setToolTip(unicode(tooltip or ''))
        self.remove_original = remove_original

    def set_enabled(self, editable=True):
        self.clear_button.setEnabled(editable)
        self.add_button.setEnabled(editable)
        self.filename.setEnabled(editable)
        self.filename.setReadOnly(not editable)
        self.document_label.setEnabled(editable)
        self.setAcceptDrops(editable)

    def stored_file_ready(self, stored_file):
        """Slot to be called when a new stored_file has been created by
        the storage"""
        self.set_value(stored_file)
        self.editingFinished.emit()

    def save_as_button_clicked(self):
        from camelot.view.storage import save_stored_file
        value = self.get_value()
        if value:
            save_stored_file(self, value)

    def add_button_clicked(self):
        from camelot.view.storage import create_stored_file
        create_stored_file(
            self,
            self.storage,
            self.stored_file_ready,
            filter=self.filter,
            remove_original=self.remove_original,
        )
        
    def open_button_clicked(self):
        from camelot.view.storage import open_stored_file
        open_stored_file(self, self.value)

    def clear_button_clicked(self):
        answer = QtGui.QMessageBox.question( self, 
                                             _('Remove this file ?'), 
                                             _('If you continue, you will no longer be able to open this file.'), 
                                             QtGui.QMessageBox.Yes,
                                             QtGui.QMessageBox.No )
        if answer == QtGui.QMessageBox.Yes:
            self.value = None
            self.editingFinished.emit()

    #
    # Drag & Drop
    #
    def dragEnterEvent(self, event):
        event.acceptProposedAction()

    def dragMoveEvent(self, event):
        event.acceptProposedAction()

    def dropEvent(self, event):
        from camelot.view.storage import create_stored_file
        if event.mimeData().hasUrls():
            url = event.mimeData().urls()[0]
            filename = url.toLocalFile()
            if filename:
                create_stored_file(
                    self,
                    self.storage,
                    self.stored_file_ready,
                    filter=self.filter,
                    remove_original=self.remove_original,
                    filename = filename,
                )

