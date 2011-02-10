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

import sys
import base64
import logging
import pkgutil

import sqlalchemy.dialects
from sqlalchemy import create_engine

from PyQt4.QtCore import QSettings
from PyQt4.QtCore import QVariant
from PyQt4.QtCore import Qt
from PyQt4.QtGui import QBoxLayout
from PyQt4.QtGui import QDialog
from PyQt4.QtGui import QGridLayout
from PyQt4.QtGui import QHBoxLayout
from PyQt4.QtGui import QInputDialog
from PyQt4.QtGui import QLabel
from PyQt4.QtGui import QLineEdit
from PyQt4.QtGui import QPushButton

from camelot.view import art
from camelot.view.controls.editors import ChoicesEditor, TextLineEditor
from camelot.view.controls.progress_dialog import ProgressDialog
from camelot.core.utils import ugettext as _
from camelot.view.model_thread.signal_slot_model_thread import \
    SignalSlotModelThread

from camelot.view.controls.standalone_wizard_page import StandaloneWizardPage


logger = logging.getLogger('camelot.view.database_selection')

dialects = [name for _importer, name, is_package in \
        pkgutil.iter_modules(sqlalchemy.dialects.__path__ ) if is_package]


def encode_setting(value):
    result = base64.b64encode(str(value))
    return result


def decode_setting(value):
    result = base64.b64decode(str(value))
    return result


def select_database():
    return
    wizard = ProfileSelection(None)
    dialog_code = wizard.exec_()
    if dialog_code == QDialog.Rejected:
        # the user chooses to exit
        sys.exit(0)


def fetch_profiles():
    profiles = []
    settings = QSettings()
    size = settings.beginReadArray('database_profiles')

    if size == 0:
        return profiles

    for index in range(size):
        settings.setArrayIndex(index)
        info = {}
        profilename = decode_setting(settings.value('profilename', QVariant('')).toString())
        if not profilename:
            continue  # well we should not really be doing anything
        info['profilename'] = profilename
        info['dialect'] = decode_setting(settings.value('dialect', QVariant('')).toString())
        info['host'] = decode_setting(settings.value('host', QVariant('')).toString())
        info['port'] = decode_setting(settings.value('port', QVariant('')).toString())
        info['database'] = decode_setting(settings.value('database', QVariant('')).toString())
        info['user'] = decode_setting(settings.value('user', QVariant('')).toString())
        info['pass'] = decode_setting(settings.value('pass', QVariant('')).toString())
        profiles.append(info)
    settings.endArray()

    return profiles


def store_profiles(profiles):
    settings = QSettings()
    settings.beginWriteArray('database_profiles')

    for index, info in enumerate(profiles):
        settings.setArrayIndex(index)
        settings.setValue('profilename', QVariant(encode_setting(info['profilename'])))
        settings.setValue('dialect', QVariant(encode_setting(info['dialect'])))
        settings.setValue('host', QVariant(encode_setting(info['host'])))
        settings.setValue('port', QVariant(encode_setting(info['port'])))
        settings.setValue('database', QVariant(encode_setting(info['database'])))
        settings.setValue('user', QVariant(encode_setting(info['user'])))
        settings.setValue('pass', QVariant(encode_setting(info['pass'])))
    settings.endArray()


def use_chosen_profile(info):
    settings = QSettings()
    settings.setValue('last_used_database_profile', QVariant(encode_setting(
        info['profilename'])))
    settings.setValue('database/driver', QVariant(encode_setting('mysql')))
    settings.setValue('database/dialect', QVariant(encode_setting(
        info['dialect'])))
    settings.setValue('database/host', QVariant(encode_setting(info['host'])))
    settings.setValue('database/user', QVariant(encode_setting(info['user'])))
    settings.setValue('database/password',
            QVariant(encode_setting(info['pass'])))
    settings.setValue('database/name',
            QVariant(encode_setting(info['database'])))


def last_used_profile():
    settings = QSettings()
    return str(decode_setting(settings.value('last_used_database_profile',
        QVariant('')).toString()))


class ProfileSelection(StandaloneWizardPage):

    def __init__(self, parent=None):
        super(ProfileSelection, self).__init__(parent)

        self._connection_valid = False

        self.profiles = fetch_profiles()
        logger.debug('original profiles fetched:\n%s' % self.profiles)
        self.profiles_choices = set()
        for profile in self.profiles:
            if 'profilename' in profile and profile['profilename']:
                self.profiles_choices.add((profile['profilename'],
                    profile['profilename']))
        logger.debug('original profiles choices:\n%s' % self.profiles_choices)

        self.setWindowTitle(_('Profile Selection'))
        self.set_banner_logo_pixmap(art.Icon(
            'tango/22x22/categories/preferences-system.png').getQPixmap())
        self.set_banner_title(_('Database Settings'))
        self.set_banner_subtitle(_('Connect with an existing profile'))
        self.banner_widget().setStyleSheet('background-color: white;')

        self.create_labels_and_widgets()
        self.set_widgets_values()
        self.connect_widgets()

        self.create_buttons()
        self.connect_buttons()


    def create_labels_and_widgets(self):
        self.profile_label = QLabel(_('Profile Name:'))
        self.dialect_label = QLabel(_('Driver:'))
        self.host_label = QLabel(_('Server Host:'))
        self.port_label = QLabel(_('Port:'))
        self.database_name_label = QLabel(_('Database Name:'))
        self.username_label = QLabel(_('Username:'))
        self.password_label = QLabel(_('Password:'))

        layout = QGridLayout()

        layout.addWidget(self.profile_label, 0, 0, Qt.AlignRight)
        layout.addWidget(self.dialect_label, 1, 0, Qt.AlignRight)
        layout.addWidget(self.host_label, 2, 0, Qt.AlignRight)
        layout.addWidget(self.port_label, 2, 3, Qt.AlignRight)
        layout.addWidget(self.database_name_label, 3, 0, Qt.AlignRight)
        layout.addWidget(self.username_label, 4, 0, Qt.AlignRight)
        layout.addWidget(self.password_label, 5, 0, Qt.AlignRight)

        self.profile_editor = ChoicesEditor(parent=self)
        self.dialect_editor = ChoicesEditor(parent=self)
        self.host_editor = TextLineEditor(self)
        self.port_editor = TextLineEditor(self)
        self.port_editor.setFixedWidth(60)
        self.database_name_editor = TextLineEditor(self)
        self.username_editor = TextLineEditor(self)
        self.password_editor = TextLineEditor(self)
        self.password_editor.setEchoMode(QLineEdit.Password)

        layout.addWidget(self.profile_editor, 0, 1, 1, 4)
        layout.addWidget(self.dialect_editor, 1, 1, 1, 1)
        layout.addWidget(self.host_editor, 2, 1, 1, 1)
        layout.addWidget(self.port_editor, 2, 4, 1, 1)
        layout.addWidget(self.database_name_editor, 3, 1, 1, 1)
        layout.addWidget(self.username_editor, 4, 1, 1, 1)
        layout.addWidget(self.password_editor, 5, 1, 1, 1)

        self.main_widget().setLayout(layout)

    def set_widgets_values(self):
        if self.profiles_choices:
            self.profile_editor.set_choices(self.profiles_choices)

        last_used = last_used_profile()
        if last_used:
            self.profile_editor.set_value(last_used)

        self.dialect_editor.set_choices([(dialect, dialect.capitalize())
            for dialect in dialects])
        self.dialect_editor.set_value(self.get_profile_value('dialect') or
            'mysql')

        self.host_editor.setText(self.get_profile_value('host') or 'localhost')
        self.port_editor.setText(self.get_profile_value('port') or '3306')
        self.database_name_editor.setText(self.get_profile_value('database'))
        self.username_editor.setText(self.get_profile_value('user'))
        self.password_editor.setText(self.get_profile_value('pass'))

    def connect_widgets(self):
        self.profile_editor.valueChanged.connect(self.update_profile)

    def create_buttons(self):
        self.cancel_button = QPushButton(_('Cancel'))
        #self.clear_button = QPushButton(_('Clear'))
        self.ok_button = QPushButton(_('OK'))
        self.new_button = QPushButton(art.Icon(
            'tango/16x16/actions/list-add.png').getQIcon(), '')
        self.new_button.setToolTip(_('Add a new profile name'))

        layout = QHBoxLayout()
        layout.setDirection(QBoxLayout.RightToLeft)

        layout.addWidget(self.cancel_button)
        #layout.addWidget(self.clear_button)
        layout.addWidget(self.ok_button)
        layout.addStretch()

        self.main_widget().layout().addWidget(self.new_button, 0, 5, 1, 1)
        self.buttons_widget().setLayout(layout)

    def connect_buttons(self):
        self.cancel_button.pressed.connect(self.reject)
        self.ok_button.pressed.connect(self.proceed)
        #self.clear_button.pressed.connect(self.clear_fields)
        self.new_button.pressed.connect(self.add_new_profile_name)

    #def clear_fields(self):
    #    self.host_editor.clear()
    #    self.port_editor.clear()
    #    self.database_name_editor.clear()
    #    self.username_editor.clear()
    #    self.password_editor.clear()

    def proceed(self):
        if self.is_connection_valid():
            info = self.collect_info()
            self.add_new_profile(info)
            logger.debug('storing new profile:\n%s' % self.profiles)
            store_profiles(self.profiles)
            use_chosen_profile(info)
            self.accept()

    def is_connection_valid(self):
        info = self.collect_info()
        mt = SignalSlotModelThread(lambda:None)
        mt.start()
        progress = ProgressDialog(_('Verifying database settings'))
        mt.post(lambda:self.test_connection(info['dialect'], info['host'],
            info['user'], info['pass'], info['database']),
            progress.finished, progress.exception)
        progress.exec_()
        return self._connection_valid

    def test_connection(self, dialect, host, user, passwd, db):
        self._connection_valid = False
        connection_string = '%s://%s:%s@%s/%s' % (dialect, user,
            passwd, host, db)
        engine = create_engine(connection_string, pool_recycle=True)
        connection = engine.raw_connection()
        cursor = connection.cursor()
        cursor.close()
        connection.close()
        self._connection_valid = True

    def add_new_profile(self, info):
        logger.info('adding a new profile')
        for profile in self.profiles:
            if info['profilename'] == profile['profilename']:
                profile.update(info)
                return
        self.profiles.append(info)

    def add_new_profile_name(self):
        logger.info('adding a new profile name')
        name, ok = QInputDialog.getText(self, _('New Profile Name'),
            _('Enter a value:'))
        if ok and name:
            name = str(name)
            self.profiles_choices.add((name, name))
            self.profile_editor.set_choices(self.profiles_choices)
            self.profile_editor.set_value(name)

    def current_profile(self):
        return self.profile_editor.get_value()

    def get_profile_value(self, key):
        current = self.current_profile()
        for profile in self.profiles:
            if profile['profilename'] == current:
                return profile[key]
        return ''

    def collect_info(self):
        logger.info('collecting new database profile info')
        info = {}
        info['profilename'] = self.current_profile()
        info['dialect'] = self.dialect_editor.get_value()
        info['host'] = self.host_editor.text()
        info['port'] = self.port_editor.text()
        info['database'] = self.database_name_editor.text()
        info['user'] = self.username_editor.text()
        info['pass'] = self.password_editor.text()
        return info
