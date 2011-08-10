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

from PyQt4 import QtGui
from PyQt4 import QtCore

from camelot.core.utils import ugettext_lazy as _
from camelot.core.utils import ugettext, variant_to_pyobject
from camelot.view.art import Icon
import logging

logger = logging.getLogger('camelot.view.wizard.pages.backup_page')

class LabelLineEdit(QtGui.QLineEdit):
    _file_name = ''

    def __init__(self, storage, parent=None):
        super(LabelLineEdit, self).__init__(parent)
        self.textChanged.connect(self._onTextChanged)
        self._storage = storage

    def _onTextChanged(self, text):
        if text == '':
            self._file_name = ''
        else:
            file_name = '%s.db'%text
            if self._storage.exists(file_name):
                self._file_name = ''
            else:
                self._file_name = file_name

    def filename(self):
        return self._file_name

class LabelComboBox(QtGui.QComboBox):
    _file_name = ''

    def __init__(self, storage, parent=None):
        super(LabelComboBox, self).__init__(parent)
        self._storage = storage
        self._setDefaultLabels()
        self.currentIndexChanged[int].connect(self._onCurrentIndexChanged)

    def _setDefaultLabels(self):
        for i, stored_file in enumerate(self._storage.list()):
            if i == 0:
                self._file_name = stored_file.name
            self.addItem( unicode(stored_file.verbose_name), QtCore.QVariant(stored_file))            

    def _onCurrentIndexChanged(self, index):
        self._file_name = variant_to_pyobject( self.itemData(index) ).name

    def filename(self):
        return self._file_name

class Page(QtGui.QWizardPage):
    """Abstract class for the select file page of a backup and a restore file.
    """
    title = _('Select backup file')
    sub_title = _('Please select a backup file. All data in this file will be overwritten.')
    icon = Icon('tango/32x32/actions/document-save.png')
    caption = _('Select file')
    extension = '.db'
    settings_key = 'custom_backup_filename'

    def __init__(self, backup_mechanism=None, parent=None):
        self.backup_mechanism = backup_mechanism
        super(Page,  self).__init__(parent)
        self.setTitle( unicode(self.title) )
        self.setSubTitle( unicode(self.sub_title) )
        self.setPixmap(QtGui.QWizard.LogoPixmap, self.icon.getQPixmap())
        
        self._storage = backup_mechanism.get_default_storage()
        self._setupUi()

        # final touches - select the default radio button
        self._default_radio.setChecked(True)
        self._showWidgets(self._default_radio)

    def _setPath(self, dir):
        """Override this method in a subclass, to make the page do something"""
        raise NotImplementedError()
    
    def _setupUi(self):
        # controls
        self._default_radio = QtGui.QRadioButton(ugettext('Default Location'))
        self._custom_radio = QtGui.QRadioButton(ugettext('Custom Location'))
        self._custom_edit = QtGui.QLineEdit()
        self._custom_button = QtGui.QPushButton(ugettext('Browse...'))
        button_group = QtGui.QButtonGroup(self)
        button_group.addButton(self._default_radio)
        button_group.addButton(self._custom_radio)

        # layout
        layout = QtGui.QVBoxLayout()
        layout.addWidget(self._default_radio)
        self._hlayout = QtGui.QHBoxLayout()
        layout.addLayout(self._hlayout)
        layout.addWidget(self._custom_radio)
        hlayout2 = QtGui.QHBoxLayout()
        hlayout2.addWidget(self._custom_edit)
        hlayout2.addWidget(self._custom_button)
        layout.addLayout(hlayout2)
        
        self.setLayout(layout)

        # connect signals to slots
        button_group.buttonClicked[QtGui.QAbstractButton].connect(self._showWidgets)
        button_group.buttonClicked[QtGui.QAbstractButton].connect(self.completeChanged)
        self._custom_button.clicked.connect(self._customButtonClicked)
        self._custom_edit.textChanged.connect(self.completeChanged)

    def _showWidgets(self, selection):
        default_selected = self._isDefaultSelected(selection)
        self._custom_edit.setVisible(not default_selected)
        self._custom_button.setVisible(not default_selected)

    def _isDefaultSelected(self, selection):
        return (selection == self._default_radio)

    def _customButtonClicked(self):
        settings = QtCore.QSettings()
        previous_location = settings.value( self.settings_key ).toString()
        path = self._setPath( previous_location )
        if path:
            self._custom_edit.setText(QtCore.QDir.toNativeSeparators(path))
            settings.setValue( self.settings_key, path )
            
        
class SelectRestoreFilePage(Page):
    title = _('Select restore file')
    sub_title = _( "Please select a backup file from which to restore the database. All data in the database will be overwritten with data from this file" )
    icon = Icon('tango/32x32/devices/drive-harddisk.png')

    def __init__(self, parent=None):
        super(SelectRestoreFilePage, self).__init__(parent)
        self.setCommitPage(True)
        if self._default_combo.count() == 0:
            self._default_radio.setEnabled(False)
            self._custom_radio.setChecked(True)
            self._showWidgets(self._custom_radio)

    def _setupUi(self):
        super(SelectRestoreFilePage, self)._setupUi()
        self._default_combo = LabelComboBox(self._storage)
        self._default_combo.currentIndexChanged[int].connect(self.completeChanged)
        self._hlayout.addWidget(self._default_combo)

    def _showWidgets(self, selection):
        default_selected = self._isDefaultSelected(selection)
        self._default_combo.setVisible(default_selected)
        super(SelectRestoreFilePage, self)._showWidgets(selection)

    def isComplete(self):
        default_selected = self._default_radio.isChecked()
        if default_selected:
            self.wizard().filename = self._default_combo.filename()
            self.wizard().storage = self._storage
            return self._default_combo.filename() != ''
        else:
            self.wizard().filename = self._custom_edit.text()
            self.wizard().storage = None
            return self._custom_edit.text() != ''

    def _setPath(self, dir):
        path = QtGui.QFileDialog.getOpenFileName(
            self, unicode(self.caption), dir, ugettext('Database files (*%s);;All files (*.*)' % self.extension),
        )
        return path

class SelectBackupFilePage(Page):
    
    def __init__(self, backup_mechanism):
        super(SelectBackupFilePage, self).__init__(backup_mechanism)
        self.setCommitPage(True)

    def _setupUi(self):
        from camelot.view.model_thread import post
        self._default_label = QtGui.QLabel(ugettext('Label:'))
        self._default_edit = LabelLineEdit(self._storage)
        self._default_label.setBuddy(self._default_edit)
        super(SelectBackupFilePage, self)._setupUi()
        self._hlayout.addWidget(self._default_label)
        self._hlayout.addWidget(self._default_edit)
        self._default_edit.textChanged.connect(self._onDefaultEditChanged)
        self._default_edit.textChanged.connect(self.completeChanged)
        post(self._get_default_label, self._set_default_label)

    def _set_default_label(self, label):
        self._default_edit.setText(label)
        
    def _onDefaultEditChanged(self, text):
        if self._default_radio.isChecked():
            self.wizard().filename = self._default_edit.filename()
    
    def _get_default_label(self):
        locale = QtCore.QLocale()
        format = locale.dateTimeFormat(locale.ShortFormat)
        formatted_date_time = QtCore.QDateTime.currentDateTime().toString(format)
        # replace all non-ascii chars with underscores
        import string
        formatted_date_time_str = unicode(formatted_date_time)
        for c in formatted_date_time_str:
            if c not in string.ascii_letters and c not in string.digits:
                formatted_date_time_str = formatted_date_time_str.replace(c, '_')                
        filename_prefix = self.backup_mechanism.get_filename_prefix()
        formatted_date_time_str = '-'.join([filename_prefix, formatted_date_time_str])
        return formatted_date_time_str

    def _showWidgets(self, selection):
        default_selected = self._isDefaultSelected(selection)
        self._default_label.setVisible(default_selected)
        self._default_edit.setVisible(default_selected)
        super(SelectBackupFilePage, self)._showWidgets(selection)

    def isComplete(self):
        default_selected = self._default_radio.isChecked()
        if default_selected:
            self.wizard().storage = self._storage
            self.wizard().filename = self._default_edit.filename()
            return self._default_edit.filename() != ''
        else:
            self.wizard().storage = None
            self.wizard().filename = self._custom_edit.text()
            return self._custom_edit.text() != ''

    def _setPath(self, dir):
        path = QtGui.QFileDialog.getSaveFileName(
                self, unicode(self.caption), dir, ugettext('Database files (*%s);;All files (*.*)' % self.extension),
            )
        return path


