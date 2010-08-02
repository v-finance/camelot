#  ==================================================================================
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
#  ==================================================================================

import os.path
import re

from PyQt4 import QtGui
from PyQt4 import QtCore
from PyQt4.QtGui import QDesktopServices

from camelot.core.utils import ugettext_lazy as _
from camelot.core.utils import ugettext
from camelot.view.art import Icon
import logging

logger = logging.getLogger('camelot.view.wizard.pages.backup_page')

def getBackupRootAndFilenameTemplate():
    import settings
    if hasattr(settings, 'CAMELOT_BACKUP_ROOT'):
        root = settings.CAMELOT_BACKUP_ROOT
    else:
        root = '.'
    if hasattr(settings, 'CAMELOT_BACKUP_FILENAME_TEMPLATE'):
        template = settings.CAMELOT_BACKUP_FILENAME_TEMPLATE
    else:
        template = 'default-backup-%(text)s.sqlite'
    return (root, template)

class LabelLineEdit(QtGui.QLineEdit):
    _file_name = ''

    def __init__(self, parent=None):
        super(LabelLineEdit, self).__init__(parent)
        self.textChanged.connect(self._onTextChanged)
        self._backup_root, self._file_name_template = getBackupRootAndFilenameTemplate()

    def _onTextChanged(self, text):
        if text == '':
            self._file_name = ''
        else:
            file_name = os.path.join(self._backup_root, self._file_name_template % {'text' : text})
            if os.path.exists(file_name):
                self._file_name = ''
            else:
                self._file_name = file_name

    def filename(self):
        return self._file_name

class LabelComboBox(QtGui.QComboBox):
    _file_name = ''

    def __init__(self, parent=None):
        super(LabelComboBox, self).__init__(parent)
        self._setDefaultLabels()
        self.currentIndexChanged[int].connect(self._onCurrentIndexChanged)

    def _setDefaultLabels(self):
        root, template = getBackupRootAndFilenameTemplate()
        regex = re.compile('^%s$' % (template % {'text' : '(.+)'}))
        for name in os.listdir(root):
            result = regex.match(name)
            if result:
                self.addItem(result.group(1), os.path.join(root, name))
        if self.count():
            self._file_name = self.itemData(0).toString()

    def _onCurrentIndexChanged(self, index):
        self._file_name = self.itemData(index).toString()

    def filename(self):
        return self._file_name

class Page(QtGui.QWizardPage):
    title = _('Select backup file')
    sub_title = _(
            "Please select a backup file.  "
            "All data in this file will be overwritten."
        )
    icon = Icon('tango/32x32/actions/document-save.png')
    caption = _('Select file')
    extension = '.sqlite'

    def __init__(self, backup_mechanism=None, parent=None):
        super(Page,  self).__init__(parent)
        
        self.backup_mechanism = backup_mechanism
        self.setTitle( unicode(self.title) )
        self.setSubTitle( unicode(self.sub_title) )
        self.setPixmap(QtGui.QWizard.LogoPixmap, self.icon.getQPixmap())
        
        self._setupUi()

        # final touches - select the default radio button
        self._default_radio.setChecked(True)
        self._showWidgets(self._default_radio)

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
        dir = settings.value('custom_filename').toString()
        path = self._setPath(dir)
        if path:
            self._custom_edit.setText(QtCore.QDir.toNativeSeparators(path))
        
class SelectRestoreFilePage(Page):
    title = _('Select restore file')
    sub_title = _( "Please select a backup file from which to restore the database."
                   "All data in the database will be overwritten with data from this file" )
    icon = Icon('tango/32x32/devices/drive-harddisk.png')

    def __init__(self, parent=None):
        super(SelectRestoreFilePage, self).__init__(parent)
        if self._default_combo.count() == 0:
            self._default_radio.setEnabled(False)
            self._custom_radio.setChecked(True)
            self._showWidgets(self._custom_radio)

    def _setupUi(self):
        super(SelectRestoreFilePage, self)._setupUi()
        self._default_combo = LabelComboBox()
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
            return self._default_combo.filename() != ''
        else:
            self.wizard().filename = self._custom_edit.text()
            return self._custom_edit.text() != ''

    def _setPath(self, dir):
        path = QtGui.QFileDialog.getOpenFileName(
                self, unicode(self.caption), dir, ugettext('Database files (*%s);;All files (*.*)' % self.extension),
            )
        return path

class SelectBackupFilePage(Page):
    def _setupUi(self):
        self._default_label = QtGui.QLabel(ugettext('Label:'))
        self._default_edit = LabelLineEdit()
        self._default_label.setBuddy(self._default_edit)
        self._default_edit.setText(self._makeDefaultLabel())

        super(SelectBackupFilePage, self)._setupUi()

        self._hlayout.addWidget(self._default_label)
        self._hlayout.addWidget(self._default_edit)
        self._default_edit.textChanged.connect(self._onDefaultEditChanged)
        self._default_edit.textChanged.connect(self.completeChanged)

    def _onDefaultEditChanged(self, text):
        if self._default_radio.isChecked():
            self.wizard().filename = self._default_edit.filename()
    
    def _get_filename_prefix(self):
        try:
            self.filename_prefix = unicode(self.bm.get_filename_prefix())
        except Exception, e:
            logger.warn('No get_filename_prefix defined in backup_mechanism: %s' % e)
    
    def _makeDefaultLabel(self):
        from camelot.view.model_thread.signal_slot_model_thread import SignalSlotModelThread
        from camelot.view.controls.progress_dialog import ProgressDialog
                
        locale = QtCore.QLocale()
        format = locale.dateTimeFormat(locale.ShortFormat)
        formatted_date_time = QtCore.QDateTime.currentDateTime().toString(format)
        # replace all non-ascii chars with underscores
        import string
        formatted_date_time_str = unicode(formatted_date_time)
        for c in formatted_date_time_str:
            if c not in string.ascii_letters and c not in string.digits:
                formatted_date_time_str = formatted_date_time_str.replace(c, '_')                
        self.filename_prefix = None
        try:
            # get filename prefix from model to use for the backup file name label
            progress = ProgressDialog(_('Getting filename prefix'))
            logger.info('Getting filename prefix')
            mt = SignalSlotModelThread(lambda:None)
            mt.start()
            self.bm = self.backup_mechanism(None)
            mt.post(lambda:self._get_filename_prefix(), progress.finished, progress.exception)
            progress.exec_()
            if self.filename_prefix:
                formatted_date_time_str = '-'.join([self.filename_prefix, formatted_date_time_str])
        except Exception, e:
            logger.warn('No backup filename prefix defined: %s' % e)
        return formatted_date_time_str

    def _showWidgets(self, selection):
        default_selected = self._isDefaultSelected(selection)
        self._default_label.setVisible(default_selected)
        self._default_edit.setVisible(default_selected)
        super(SelectBackupFilePage, self)._showWidgets(selection)

    def isComplete(self):
        default_selected = self._default_radio.isChecked()
        if default_selected:
            self.wizard().filename = self._default_edit.filename()
            return self._default_edit.filename() != ''
        else:
            self.wizard().filename = self._custom_edit.text()
            return self._custom_edit.text() != ''

    def _setPath(self, dir):
        path = QtGui.QFileDialog.getSaveFileName(
                self, unicode(self.caption), dir, ugettext('Database files (*%s);;All files (*.*)' % self.extension),
            )
        return path
