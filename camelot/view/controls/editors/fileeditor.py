#  ============================================================================
#
#  Copyright (C) 2007-2011 Conceptive Engineering bvba. All rights reserved.
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

from PyQt4 import QtGui, QtCore
from PyQt4.QtCore import Qt

from customeditor import CustomEditor, set_background_color_palette

from camelot.view.art import Icon
from camelot.core.utils import ugettext as _

from camelot.view.controls.decorated_line_edit import DecoratedLineEdit

class FileEditor(CustomEditor):
    """Widget for editing File fields"""

    filter = 'All files (*)'

    def __init__(self, parent=None, storage=None, remove_original=False, 
                 **kwargs):
        CustomEditor.__init__(self, parent)
        self.storage = storage
        self.filename = None # the widget containing the filename

        # i'm a < 80 characters fanatic, i know :)
        self.new_icon = Icon(
            'tango/16x16/actions/list-add.png'
        ).getQIcon()
        self.open_icon = Icon(
            'tango/16x16/actions/document-open.png'
        ).getQIcon()
        self.clear_icon = Icon(
            'tango/16x16/actions/edit-delete.png'
        ).getQIcon()
        self.save_as_icon = Icon(
            'tango/16x16/actions/document-save-as.png'
        ).getQIcon()
        self.document_pixmap = Icon(
            'tango/16x16/mimetypes/x-office-document.png'
        ).getQPixmap()

        self.value = None
        self.remove_original = remove_original
        self.setup_widget()

    def setup_widget(self):
        """Called inside init, overwrite this method for custom
        file edit widgets"""
        self.layout = QtGui.QHBoxLayout()
        self.layout.setSpacing(0)
        self.layout.setMargin(0)

        # Save As button
        self.save_as_button = QtGui.QToolButton()
        self.save_as_button.setFocusPolicy(Qt.StrongFocus)
        self.save_as_button.setIcon(self.save_as_icon)
        self.save_as_button.setToolTip(_('Save file as'))
        self.save_as_button.setAutoRaise(True)
        self.save_as_button.clicked.connect(self.save_as_button_clicked)

        # Clear button
        self.clear_button = QtGui.QToolButton()
        self.clear_button.setFocusPolicy(Qt.StrongFocus)
        self.clear_button.setIcon(self.clear_icon)
        self.clear_button.setToolTip(_('delete file'))
        self.clear_button.setAutoRaise(True)
        self.clear_button.clicked.connect(self.clear_button_clicked)

        # Open button
        self.open_button = QtGui.QToolButton()
        self.open_button.setFocusPolicy(Qt.StrongFocus)
        self.open_button.setIcon(self.new_icon)
        self.open_button.setToolTip(_('add file'))
        self.open_button.clicked.connect(self.open_button_clicked)
        self.open_button.setAutoRaise(True)

        # Filename
        self.filename = DecoratedLineEdit(self)
        
        # Search Completer
        self.completer = QtGui.QCompleter()
        self.completions_model = QtGui.QFileSystemModel()
        self.completer.setCompletionMode(
            QtGui.QCompleter.UnfilteredPopupCompletion
        )        
        self.completer.setModel( self.completions_model )
        self.completer.activated[QtCore.QModelIndex].connect(self.file_completion_activated)
        self.filename.setCompleter( self.completer )
        settings = QtCore.QSettings()
        last_path = settings.value('lastpath').toString()
        self.completions_model.setRootPath( last_path )

        # Setup layout
        self.document_label = QtGui.QLabel(self)
        self.document_label.setPixmap(self.document_pixmap)
        self.layout.addWidget(self.document_label)
        self.layout.addWidget(self.filename)
        self.layout.addWidget(self.clear_button)
        self.layout.addWidget(self.open_button)
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
            
    def set_tab_order(self):
        if self.filename.text() != '':
            self.setTabOrder(self.clear_button, self.filename)
        else:
            self.setTabOrder(self.clear_button, self.filename)
            self.setTabOrder(self.open_button, self.clear_button)

    def set_value(self, value):
        value = CustomEditor.set_value(self, value)
        self.value = value
        if value:
            self.save_as_button.setVisible(True)
            self.filename.setText(value.verbose_name)
            self.open_button.setIcon(self.open_icon)
            self.open_button.setToolTip(_('open file'))
        else:
            self.save_as_button.setVisible(False)
            self.filename.setText('')
            self.open_button.setIcon(self.new_icon)
            self.open_button.setToolTip(_('add file'))
        self.set_tab_order()
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
        self.open_button.setEnabled(editable)
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

    def open_button_clicked(self):
        from camelot.view.storage import open_stored_file
        from camelot.view.storage import create_stored_file
        if not self.value:
            create_stored_file(
                self,
                self.storage,
                self.stored_file_ready,
                filter=self.filter,
                remove_original=self.remove_original,
            )
        else:
            open_stored_file(self, self.value)

    def clear_button_clicked(self):
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
                    filename = path,
                )
