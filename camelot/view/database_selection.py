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
import logging
import pkgutil

import sqlalchemy.dialects
from sqlalchemy import create_engine

from PyQt4 import QtCore
from PyQt4.QtCore import Qt
from PyQt4.QtGui import QBoxLayout
from PyQt4.QtGui import QDialog
from PyQt4.QtGui import QFont
from PyQt4.QtGui import QGridLayout
from PyQt4.QtGui import QHBoxLayout
from PyQt4.QtGui import QLabel
from PyQt4.QtGui import QLineEdit
from PyQt4.QtGui import QPushButton
from PyQt4.QtGui import QFileDialog

from camelot.view import art
from camelot.view.controls.progress_dialog import ProgressDialog
from camelot.view.controls.editors import ChoicesEditor, TextLineEditor, LanguageEditor
from camelot.view.controls.standalone_wizard_page import HSeparator
from camelot.view.controls.standalone_wizard_page import StandaloneWizardPage
from camelot.view.controls.combobox_input_dialog import ComboBoxInputDialog

from camelot.core.utils import ugettext as _
from camelot.view.model_thread.signal_slot_model_thread import SignalSlotModelThread

from camelot.core.dbprofiles import fetch_profiles, use_chosen_profile, store_profiles

logger = logging.getLogger('camelot.view.database_selection')

dialects = [name for _importer, name, is_package in \
        pkgutil.iter_modules(sqlalchemy.dialects.__path__ ) if is_package]

NEW_PROFILE_LABEL = _('new profile')

def select_database(app_admin):
    profiles_dict = fetch_profiles()
    if not profiles_dict:
        create_new_profile(app_admin, profiles_dict)

    selected = select_profile(profiles_dict)
    if selected in profiles_dict:
        use_chosen_profile(selected, profiles_dict[selected])
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
        return str(input_dialog.get_text())

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
        self.set_banner_title(_('Create New Profile'))
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
        self.proxy_address_label = QLabel(_('Proxy Address:'))
        self.proxy_username_label = QLabel(_('Proxy Username:'))
        self.proxy_password_label = QLabel(_('Proxy Password:'))

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
        layout.addWidget(self.proxy_address_label,  9, 0, Qt.AlignRight)
        layout.addWidget(self.proxy_username_label, 10, 0, Qt.AlignRight)
        layout.addWidget(self.proxy_password_label, 11, 0, Qt.AlignRight)

        self.profile_editor = QLineEdit()

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
        
        self.proxy_address_editor = TextLineEditor(self, length=32767)
        self.proxy_username_editor = TextLineEditor(self)
        self.proxy_password_editor = TextLineEditor(self)
        self.proxy_password_editor.setEchoMode(QLineEdit.Password)

        layout.addWidget(self.profile_editor, 0, 1, 1, 4)
        layout.addWidget(self.dialect_editor, 1, 1, 1, 1)
        layout.addWidget(self.host_editor, 2, 1, 1, 1)
        layout.addWidget(self.port_editor, 2, 4, 1, 1)
        layout.addWidget(self.database_name_editor, 3, 1, 1, 1)
        layout.addWidget(self.username_editor, 4, 1, 1, 1)
        layout.addWidget(self.password_editor, 5, 1, 1, 1)
        layout.addWidget(HSeparator(), 6, 0, 1, 5)
        layout.addWidget(self.media_location_editor, 7, 1, 1, 1)
        layout.addWidget(self.language_editor, 8, 1, 1, 1)
        layout.addWidget(self.proxy_address_editor, 9, 1, 1, 1)
        layout.addWidget(self.proxy_username_editor, 10, 1, 1, 1)
        layout.addWidget(self.proxy_password_editor, 11, 1, 1, 1)

        self.main_widget().setLayout(layout)

    def set_widgets_values(self):
        self.dialect_editor.set_choices([(dialect, dialect.capitalize()) for dialect in dialects])
        self.profile_editor.setFocus()
        self.update_profile()

    def connect_widgets(self):
        self.profile_editor.textChanged.connect(self.update_profile)

    def create_buttons(self):
        self.cancel_button = QPushButton(_('Cancel'))
        #self.clear_button = QPushButton(_('Clear'))
        self.ok_button = QPushButton(_('OK'))

        layout = QHBoxLayout()
        layout.setDirection(QBoxLayout.RightToLeft)

        layout.addWidget(self.cancel_button)
        #layout.addWidget(self.clear_button)
        layout.addWidget(self.ok_button)
        layout.addStretch()

        self.buttons_widget().setLayout(layout)

        self.browse_button = QPushButton(_('Browse'))
        self.main_widget().layout().addWidget(self.browse_button, 7, 2, 1, 3)

    def set_tab_order(self):
        all_widgets = [self.profile_editor, self.dialect_editor,
            self.host_editor, self.port_editor,  self.database_name_editor,
            self.username_editor, self.password_editor,
            self.media_location_editor, self.browse_button,
            self.language_editor,
            self.proxy_address_editor, self.proxy_username_editor,
            self.proxy_password_editor, self.ok_button, self.cancel_button]

        i = 1
        while i != len(all_widgets):
            self.setTabOrder(all_widgets[i-1], all_widgets[i])
            i += 1

    def connect_buttons(self):
        self.cancel_button.pressed.connect(self.reject)
        self.ok_button.pressed.connect(self.proceed)
        #self.clear_button.pressed.connect(self.clear_fields)
        self.browse_button.pressed.connect(self.fill_media_location)

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
            use_chosen_profile(profilename, info)
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
        text = str(self.profile_editor.text())
        self.toggle_ok_button(bool(text))
        return text

    def update_profile(self):
        from camelot.view.proxy import ValueLoading
        self.dialect_editor.set_value(self.get_profile_value('dialect') or 'mysql')
        self.host_editor.setText(self.get_profile_value('host') or '127.0.0.1')
        self.port_editor.setText(self.get_profile_value('port') or '3306')
        self.database_name_editor.setText(self.get_profile_value('database') or self.database_name_editor.text())
        self.username_editor.setText(self.get_profile_value('user') or self.username_editor.text())
        self.password_editor.setText(self.get_profile_value('pass') or self.password_editor.text())
        self.media_location_editor.setText(self.get_profile_value('media_location') or self.media_location_editor.text())
        self.language_editor.set_value(self.get_profile_value('locale_language') or self.language_editor.get_value())
        self.proxy_address_editor.setText(self.get_profile_value('proxy_host') or self.proxy_address_editor.text())
        self.proxy_username_editor.setText(self.get_profile_value('proxy_username') or self.proxy_username_editor.text())
        self.proxy_password_editor.setText(self.get_profile_value('proxy_password') or self.proxy_password_editor.text())

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
        info['proxy_host'] = self.proxy_address_editor.text()
        info['proxy_username'] = self.proxy_username_editor.text()
        info['proxy_password'] = self.proxy_password_editor.text()
        return profilename, info

    def fill_media_location(self):
        caption = _('Select media location')
        selected = str(QFileDialog.getExistingDirectory(self, caption))
        if selected:
            self.media_location_editor.setText(selected)
