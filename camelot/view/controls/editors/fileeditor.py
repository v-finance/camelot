#  ============================================================================
#
#  Copyright (C) 2007-2010 Conceptive Engineering bvba. All rights reserved.
#  www.conceptive.be / project-camelot@conceptive.be
#
#  This file is part of the Camelot Library.
#
#  This file may be used under the terms of the GNU General Public
#  License version 2.0 as published by the Free Software Foundation
#  and appearing in the file LICENSE.GPL included in the packaging of
#  this file.  Please review the following information to ensure GNU
#  General Public Licensing requirements will be met:
#  http://www.trolltech.com/products/qt/opensource.html
#
#  If you are unsure which license is appropriate for your use, please
#  review the following information:
#  http://www.trolltech.com/products/qt/licensing.html or contact
#  project-camelot@conceptive.be.
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

from customeditor import CustomEditor

from camelot.view.art import Icon
from camelot.core.utils import ugettext as _


class FileEditor(CustomEditor):
    """Widget for editing File fields"""

    filter = 'All files (*)'

    def __init__(self, parent=None, storage=None, **kwargs):
        CustomEditor.__init__(self, parent)
        self.storage = storage

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
        self.setup_widget()

    def setup_widget(self):
        """Called inside init, overwrite this method for custom
        file edit widgets"""
        self.layout = QtGui.QHBoxLayout()
        self.layout.setSpacing(0)
        self.layout.setMargin(0)

        # Save As button
        self.save_as_button = QtGui.QToolButton()
        self.save_as_button.setFocusPolicy(Qt.ClickFocus)
        self.save_as_button.setIcon(self.save_as_icon)
        self.save_as_button.setToolTip(_('Save file as'))
        self.save_as_button.setAutoRaise(True)
        self.save_as_button.clicked.connect(self.save_as_button_clicked)

        # Clear button
        self.clear_button = QtGui.QToolButton()
        self.clear_button.setFocusPolicy(Qt.ClickFocus)
        self.clear_button.setIcon(self.clear_icon)
        self.clear_button.setToolTip(_('delete file'))
        self.clear_button.setAutoRaise(True)
        self.clear_button.clicked.connect(self.clear_button_clicked)

        # Open button
        self.open_button = QtGui.QToolButton()
        self.open_button.setFocusPolicy(Qt.ClickFocus)
        self.open_button.setIcon(self.new_icon)
        self.open_button.setToolTip(_('add file'))
        self.open_button.clicked.connect(self.open_button_clicked)
        self.open_button.setAutoRaise(True)

        # Filename
        self.filename = QtGui.QLineEdit(self)

        # Setup layout
        self.document_label = QtGui.QLabel(self)
        self.document_label.setPixmap(self.document_pixmap)
        self.layout.addWidget(self.document_label)
        self.layout.addWidget(self.filename)
        self.layout.addWidget(self.clear_button)
        self.layout.addWidget(self.open_button)
        self.layout.addWidget(self.save_as_button)
        self.setLayout(self.layout)

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
        return value

    def get_value(self):
        return CustomEditor.get_value(self) or self.value

    def set_field_attributes(self, editable=True, background_color=None, **kwargs):
        self.set_enabled(editable)
        self.set_background_color(background_color)

    def set_enabled(self, editable=True):
        self.clear_button.setEnabled(editable)
        self.open_button.setEnabled(editable)
        self.filename.setEnabled(editable)
        self.filename.setReadOnly(not editable)
        self.document_label.setEnabled(editable)
        self.setAcceptDrops(editable)

    def stored_file_ready(self, stored_file):
        """Slot to be called when a new stored_file has been created by
        the storeage"""
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
                filter=self.filter
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
        if event.mimeData().hasUrls():
            url = event.mimeData().urls()[0]
            filename = url.toLocalFile()
            if filename != '':
                from camelot.view.storage import SaveFileProgressDialog
                from camelot.view.model_thread import post
                progress = SaveFileProgressDialog()

                def checkin():
                    stored_file = self.storage.checkin(unicode(filename))
                    return lambda:self.stored_file_ready(stored_file)

                post(checkin, progress.finish)
                progress.exec_()
