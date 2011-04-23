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

import os
import sys
import logging
import pkgutil

from sqlalchemy import create_engine

from PyQt4 import QtCore
from PyQt4.QtCore import Qt
from PyQt4.QtCore import QFileInfo
from PyQt4.QtGui import QBoxLayout, QDialog, QFont, QGridLayout, QHBoxLayout, \
    QLabel, QLineEdit, QPushButton, QFileDialog, QComboBox, QWidget, QVBoxLayout
from camelot.view import art
from camelot.view.controls.progress_dialog import ProgressDialog
from camelot.view.controls.editors import ChoicesEditor, TextLineEditor, LanguageEditor
from camelot.view.controls.standalone_wizard_page import HSeparator, StandaloneWizardPage
from camelot.view.controls.combobox_input_dialog import ComboBoxInputDialog

from camelot.core.utils import ugettext as _
from camelot.view.model_thread.signal_slot_model_thread import SignalSlotModelThread

from camelot.core.dbprofiles import fetch_profiles, use_chosen_profile, \
    store_profiles, get_network_proxy, check_connection

logger = logging.getLogger('camelot.view.database_selection')


NEW_PROFILE_LABEL = _('new/edit profile')

def select_database(app_admin):
    profiles_dict = fetch_profiles()
    if not profiles_dict:
        create_new_profile(app_admin, profiles_dict)

    selected = select_profile(profiles_dict)
    if selected in profiles_dict:
        use_chosen_profile(selected)
    elif selected == NEW_PROFILE_LABEL:
        create_new_profile(app_admin, profiles_dict)
    else:
        sys.exit(0)

def select_profile(profiles_dict):
    title = _('Profile Selection')
    input_label = _('Select a stored profile:')
    ok_label = _('OK')
    cancel_label = _('Quit')

    input_dialog = ComboBoxInputDialog(autoaccept=True)
    input_dialog.set_window_title(title)
    input_dialog.set_label_text(input_label)
    input_dialog.set_ok_button_text(ok_label)
    input_dialog.set_cancel_button_text(cancel_label)
    input_dialog.set_items(sorted(profiles_dict.keys()) + [NEW_PROFILE_LABEL])
    input_dialog.set_ok_button_default()

    last_index = input_dialog.count()-1
    custom_font = QFont()
    custom_font.setItalic(True)
    icon = art.Icon('tango/16x16/actions/document-new.png').getQIcon()
    input_dialog.set_data(last_index, custom_font, Qt.FontRole)
    input_dialog.set_data(last_index, icon, Qt.DecorationRole)

    dialog_code = input_dialog.exec_()
    if dialog_code == QDialog.Accepted:
        return unicode(input_dialog.get_text())

    return None

def new_profile_item_selected(input_dialog):
    input_dialog.accept()

def create_new_profile(app_admin, profiles):
    wizard = app_admin.database_profile_wizard(profiles)
    dialog_code = wizard.exec_()
    if dialog_code == QDialog.Rejected:
        # no profiles? exit
        if not profiles:
            sys.exit(0)
        # one more time
        select_database(app_admin)

class ProfileWizard(StandaloneWizardPage):
    """Wizard for the creation of a new database
profile.

.. attribute:: languages

A list of languages allowed in the profile selection, an empty list will
allow all languages
    """

    languages = []

    def __init__(self, profiles, parent=None):
        super(ProfileWizard, self).__init__(parent)

        self._connection_valid = False
        self.profiles = profiles

        self.setWindowTitle(_('Profile Wizard'))
        self.set_banner_logo_pixmap(art.Icon('tango/22x22/categories/preferences-system.png').getQPixmap())
        self.set_banner_title(_('Create New/Edit Profile'))
        self.set_banner_subtitle(_('Please enter the database settings'))
        self.banner_widget().setStyleSheet('background-color: white;')

        self.create_labels_and_widgets()
        self.create_buttons()

        self.set_tab_order()

        self.set_widgets_values()

        # note: connections come after labels and widgets are created
        # and have default values
        self.connect_widgets()
        self.connect_buttons()

    def create_labels_and_widgets(self):
        self.profile_label = QLabel(_('Profile Name:'))
        self.dialect_label = QLabel(_('Driver:'))
        self.host_label = QLabel(_('Server Host:'))
        self.port_label = QLabel(_('Port:'))
        self.database_name_label = QLabel(_('Database Name:'))
        self.username_label = QLabel(_('Username:'))
        self.password_label = QLabel(_('Password:'))
        self.media_location_label = QLabel(_('Media Location:'))
        self.language_label = QLabel(_('Language:'))
        self.proxy_host_label = QLabel(_('Proxy Host:'))
        self.proxy_port_label = QLabel(_('Port:'))
        self.proxy_username_label = QLabel(_('Proxy Username:'))
        self.proxy_password_label = QLabel(_('Proxy Password:'))

        self.working_proxy_label = QLabel(_('Internet available.'))
        self.working_proxy_label.setStyleSheet('color: green')

        self.not_working_proxy_label = QLabel(_('Internet not available.'))
        self.not_working_proxy_label.setStyleSheet('color: red')

        self.not_accessible_media_path_label = QLabel(_('Media location path '\
            'is not accessible.'))
        self.not_accessible_media_path_label.setStyleSheet('color: red')
        self.not_writable_media_path_label = QLabel(_('Media location path '\
            'is not writable.'))
        self.not_writable_media_path_label.setStyleSheet('color: red')

        layout = QGridLayout()

        layout.addWidget(self.profile_label, 0, 0, Qt.AlignRight)
        layout.addWidget(self.dialect_label, 1, 0, Qt.AlignRight)
        layout.addWidget(self.host_label, 2, 0, Qt.AlignRight)
        layout.addWidget(self.port_label, 2, 3, Qt.AlignRight)
        layout.addWidget(self.database_name_label, 3, 0, Qt.AlignRight)
        layout.addWidget(self.username_label, 4, 0, Qt.AlignRight)
        layout.addWidget(self.password_label, 5, 0, Qt.AlignRight)
        layout.addWidget(self.media_location_label, 7, 0, Qt.AlignRight)
        layout.addWidget(self.language_label, 8, 0, Qt.AlignRight)
        layout.addWidget(self.proxy_host_label,  10, 0, Qt.AlignRight)
        layout.addWidget(self.proxy_port_label,  10, 3, Qt.AlignRight)
        layout.addWidget(self.proxy_username_label, 11, 0, Qt.AlignRight)
        layout.addWidget(self.proxy_password_label, 12, 0, Qt.AlignRight)

        self.profile_editor = QComboBox(self)
        self.profile_editor.setEditable(True)

        # 32767 is Qt max length for string
        # should be more than enough for folders
        # http://doc.qt.nokia.com/latest/qlineedit.html#maxLength-prop
        self.dialect_editor = ChoicesEditor(parent=self)
        self.host_editor = TextLineEditor(self, length=32767)
        self.port_editor = TextLineEditor(self)
        self.port_editor.setFixedWidth(60)
        self.database_name_editor = TextLineEditor(self, length=32767)
        self.username_editor = TextLineEditor(self)
        self.password_editor = TextLineEditor(self)
        self.password_editor.setEchoMode(QLineEdit.Password)
        self.media_location_editor = TextLineEditor(self, length=32767)
        self.language_editor = LanguageEditor(languages=self.languages,
                                              parent=self)
        #
        # try to find a default language
        #
        system_language = QtCore.QLocale.system().name()
        if self.languages:
            if system_language in self.languages:
                self.language_editor.set_value( system_language )
            else:
                self.language_editor.set_value( self.languages[0] )
        else:
            self.language_editor.set_value( system_language )

        self.proxy_host_editor = TextLineEditor(self, length=32767)
        self.proxy_port_editor = TextLineEditor(self)
        self.proxy_port_editor.setFixedWidth(60)
        self.proxy_username_editor = TextLineEditor(self)
        self.proxy_password_editor = TextLineEditor(self)
        self.proxy_password_editor.setEchoMode(QLineEdit.Password)

        layout.addWidget(self.profile_editor, 0, 1, 1, 1)
        layout.addWidget(self.dialect_editor, 1, 1, 1, 1)
        layout.addWidget(self.host_editor, 2, 1, 1, 1)
        layout.addWidget(self.port_editor, 2, 4, 1, 1)
        layout.addWidget(self.database_name_editor, 3, 1, 1, 1)
        layout.addWidget(self.username_editor, 4, 1, 1, 1)
        layout.addWidget(self.password_editor, 5, 1, 1, 1)
        layout.addWidget(HSeparator(), 6, 0, 1, 5)
        layout.addWidget(self.media_location_editor, 7, 1, 1, 1)
        layout.addWidget(self.language_editor, 8, 1, 1, 1)
        layout.addWidget(HSeparator(), 9, 0, 1, 5)
        layout.addWidget(self.proxy_host_editor, 10, 1, 1, 1)
        layout.addWidget(self.proxy_port_editor, 10, 4, 1, 1)
        layout.addWidget(self.proxy_username_editor, 11, 1, 1, 1)
        layout.addWidget(self.proxy_password_editor, 12, 1, 1, 1)

        self.main_widget().setLayout(layout)

    def set_widgets_values(self):
        self.dialect_editor.clear()
        self.profile_editor.clear()

        import sqlalchemy.dialects
        dialects = [name for _importer, name, is_package in \
            pkgutil.iter_modules(sqlalchemy.dialects.__path__) if is_package]
        self.dialect_editor.set_choices([(dialect, dialect.capitalize()) \
            for dialect in dialects])

        self.profile_editor.insertItems(1, [''] + \
            [item for item in fetch_profiles()])
        self.profile_editor.setFocus()
        self.update_wizard_values()

    def connect_widgets(self):
        self.profile_editor.editTextChanged.connect(self.update_wizard_values)

        #self.proxy_host_editor.textChanged.connect(lambda text: \
        #    self.update_proxy_values())
        #self.proxy_port_editor.textChanged.connect(lambda text: \
        #    self.update_proxy_values())
        #self.proxy_username_editor.textChanged.connect(lambda text: \
        #    self.update_proxy_values())
        #self.proxy_password_editor.textChanged.connect(lambda text: \
        #    self.update_proxy_values())

    def create_buttons(self):
        self.more_button = QPushButton(_('More'))
        self.more_button.setCheckable(True)
        self.more_button.setAutoDefault(False)
        self.cancel_button = QPushButton(_('Cancel'))
        #self.clear_button = QPushButton(_('Clear'))
        self.ok_button = QPushButton(_('OK'))

        layout = QHBoxLayout()
        layout.setDirection(QBoxLayout.RightToLeft)

        layout.addWidget(self.cancel_button)
        #layout.addWidget(self.clear_button)
        layout.addWidget(self.ok_button)
        layout.addStretch()
        layout.addWidget(self.more_button)

        self.buttons_widget().setLayout(layout)

        self.browse_button = QPushButton(_('Browse'))
        self.main_widget().layout().addWidget(self.browse_button, 7, 2, 1, 3)

        self.setup_extension()

    def setup_extension(self):
        self.extension = QWidget()

        self.load_button = QPushButton(_('Load profiles'))
        self.save_button = QPushButton(_('Save profiles'))

        extension_buttons_layout = QHBoxLayout()
        extension_buttons_layout.setMargin(0)
        extension_buttons_layout.addWidget(self.load_button)
        extension_buttons_layout.addWidget(self.save_button)
        extension_buttons_layout.addStretch()

        extension_layout = QVBoxLayout()
        extension_layout.setMargin(0)
        extension_layout.addWidget(HSeparator())
        extension_layout.addLayout(extension_buttons_layout)

        self.extension.setLayout(extension_layout)
        self.main_widget().layout().addWidget(self.extension, 15, 0, 1, 5)
        self.extension.hide()

    def set_tab_order(self):
        all_widgets = [self.profile_editor, self.dialect_editor,
            self.host_editor, self.port_editor,  self.database_name_editor,
            self.username_editor, self.password_editor,
            self.media_location_editor, self.browse_button,
            self.language_editor,
            self.proxy_host_editor, self.proxy_port_editor,
            self.proxy_username_editor, self.proxy_password_editor,
            self.ok_button, self.cancel_button]

        i = 1
        while i != len(all_widgets):
            self.setTabOrder(all_widgets[i-1], all_widgets[i])
            i += 1

    def connect_buttons(self):
        self.cancel_button.pressed.connect(self.reject)
        self.ok_button.pressed.connect(self.proceed)
        #self.clear_button.pressed.connect(self.clear_fields)

        self.browse_button.pressed.connect(self.fill_media_location)

        self.more_button.toggled.connect(self.extension.setVisible)

        self.save_button.pressed.connect(self.save_profiles_to_file)
        self.load_button.pressed.connect(self.load_profiles_from_file)

    #def clear_fields(self):
    #    self.host_editor.clear()
    #    self.port_editor.clear()
    #    self.database_name_editor.clear()
    #    self.username_editor.clear()
    #    self.password_editor.clear()

    def proceed(self):
        if self.is_connection_valid():
            profilename, info = self.collect_info()
            if profilename in self.profiles:
                self.profiles[profilename].update(info)
            else:
                self.profiles[profilename] = info
            store_profiles(self.profiles)
            use_chosen_profile(profilename)
            self.accept()

    def is_connection_valid(self):
        profilename, info = self.collect_info()
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
        connection_string = '%s://%s:%s@%s/%s' % (dialect, user, passwd, host, db)
        engine = create_engine(connection_string, pool_recycle=True)
        connection = engine.raw_connection()
        cursor = connection.cursor()
        cursor.close()
        connection.close()
        self._connection_valid = True

    def toggle_ok_button(self, enabled):
        self.ok_button.setEnabled(enabled)

    def current_profile(self):
        text = unicode(self.profile_editor.currentText())
        self.toggle_ok_button(bool(text))
        return text

    def update_wizard_values(self):
        self.dialect_editor.set_value(self.get_profile_value('dialect') or 'mysql')
        self.host_editor.setText(self.get_profile_value('host') or '127.0.0.1')
        self.port_editor.setText(self.get_profile_value('port') or '3306')
        self.database_name_editor.setText(self.get_profile_value('database') or self.database_name_editor.text())
        self.username_editor.setText(self.get_profile_value('user') or self.username_editor.text())
        self.password_editor.setText(self.get_profile_value('pass') or self.password_editor.text())
        self.media_location_editor.setText(self.get_profile_value('media_location') or self.media_location_editor.text())
        self.language_editor.set_value(self.get_profile_value('locale_language') or self.language_editor.get_value())

        self.update_proxy_values()

    def update_proxy_values(self):
        network_proxy = get_network_proxy()
        self.proxy_host_editor.setText(self.get_profile_value('proxy_host') or str(network_proxy.hostName()))
        self.proxy_port_editor.setText(self.get_profile_value('proxy_port') or str(network_proxy.port()))
        self.proxy_username_editor.setText(self.get_profile_value('proxy_username') or str(network_proxy.user()))
        self.proxy_password_editor.setText(self.get_profile_value('proxy_password') or str(network_proxy.password()))

        if check_connection(proxy=network_proxy):
            self.main_widget().layout().addWidget(
                self.working_proxy_label, 13, 1, 1, 4)
        else:
            self.main_widget().layout().addWidget(
                self.not_working_proxy_label, 13, 1, 1, 4)

    def get_profile_value(self, key):
        current = self.current_profile()
        if current in self.profiles:
            return self.profiles[current][key]
        return ''

    def collect_info(self):
        logger.info('collecting new database profile info')
        info = {}
        profilename = self.current_profile()
        info['dialect'] = self.dialect_editor.get_value()
        info['host'] = self.host_editor.text()
        info['port'] = self.port_editor.text()
        info['database'] = self.database_name_editor.text()
        info['user'] = self.username_editor.text()
        info['pass'] = self.password_editor.text()
        info['media_location'] = self.media_location_editor.text()
        info['locale_language'] = self.language_editor.get_value()
        info['proxy_host'] = self.proxy_host_editor.text()
        info['proxy_port'] = self.proxy_port_editor.text()
        info['proxy_username'] = self.proxy_username_editor.text()
        info['proxy_password'] = self.proxy_password_editor.text()
        return profilename, info

    def fill_media_location(self):
        caption = _('Select media location')
        selected = unicode(QFileDialog.getExistingDirectory(self, caption))

        if not selected:
            return

        info = QFileInfo(selected)
        if not info.isReadable():
            self.main_widget().layout().addWidget(
                self.not_accessible_media_path_label, 13, 1, 1, 4)
            return
        if not info.isWritable():
            self.main_widget().layout().addWidget(
                self.not_writable_media_path_label, 13, 1, 1, 4)
            return

        self.media_location_editor.setText(selected)


    def save_profiles_to_file(self):
        caption = _('Save Profiles To a File')
        filters = _('Profiles file (*.ini)')
        path = QFileDialog.getSaveFileName(self, caption, 'profiles', filters)

        if not path:
            return

        store_profiles(self.profiles, to_file=path)

        #mt = SignalSlotModelThread(lambda:None)
        #mt.start()
        #progress = ProgressDialog(_('Saving progiles to file'))
        #mt.post(lambda:store_profiles(self.profiles, to_file=path),
        #    progress.finished, progress.exception)
        #progress.exec_()

    def load_profiles_from_file(self):
        caption = _('Load Profiles From a File')
        filters = _('Profiles file (*.ini)')
        path = QFileDialog.getOpenFileName(self, caption, 'profiles', filters)

        if not path:
            return

        self.profiles = fetch_profiles(from_file=path)

        #mt = SignalSlotModelThread(lambda:None)
        #mt.start()
        #progress = ProgressDialog(_('Loading profiles from file'))
        #mt.post(lambda:setattr(self, 'profiles',
        #    fetch_profiles(from_file=path)), progress.finished,
        #    progress.exception)
        #progress.exec_()

        if self.profiles:
            store_profiles(self.profiles)
            os.execv(sys.executable, [sys.executable] + sys.argv)
