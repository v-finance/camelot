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

import base64
import logging
import pkgutil

import sqlalchemy.dialects
from sqlalchemy import create_engine

from PyQt4 import QtCore
from PyQt4.QtGui import QWizard, QWizardPage, QGridLayout, QLabel, QLineEdit, \
    QPushButton, QDialog, QVBoxLayout, QHBoxLayout, QPalette, QFrame, \
    QWidget, QBoxLayout
from PyQt4.QtCore import QSettings, QVariant, SIGNAL, Qt

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
    wizard.exec_()


def fetch_profiles():
    profiles = []
    settings = QSettings()
    size = settings.beginReadArray('databaseprofiles')

    if size == 0:
        return profiles

    for index in range(size):
        settings.setArrayIndex(index)
        info = {}
        info['profilename'] = decode_setting(settings.value('profilename', QVariant('')).toString())
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
    settings.beginWriteArray('databaseprofiles')

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


class ProfileSelection(StandaloneWizardPage):

    def __init__(self, parent=None):
        super(ProfileSelection, self).__init__(parent)

        self.profiles = fetch_profiles()
        self.profiles_choices = [
            (profile['profilename'], profile['profilename'].capitalize())
            for profile in self.profiles if 'profilename' in profile
        ]

        self.setWindowTitle(_('Profile Selection'))
        self.set_banner_logo_pixmap(art.Icon(
            'tango/22x22/categories/preferences-system.png').getQPixmap())
        self.set_banner_title(_('Database Settings'))
        self.set_banner_subtitle(_('Connect with an existing profile'))
        self.banner_widget().setStyleSheet('background-color: white;')

        self.create_labels_and_widgets()
        self.set_widgets_values()
        #self.connect_widgets()

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
        self.profile_editor.setEditable(True)
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
        self.profile_editor.set_choices(self.profiles_choices)
        self.dialect_editor.set_choices([(dialect, dialect.capitalize())
            for dialect in dialects])
        self.dialect_editor.set_value(self.get_profile_value('dialect') or
            'mysql')
        self.host_editor.setText(self.get_profile_value('host') or 'localhost')
        self.port_editor.setText(self.get_profile_value('port') or '3306')
        self.database_name_editor.setText(self.get_profile_value('database'))
        self.username_editor.setText(self.get_profile_value('user'))
        self.password_editor.setText(self.get_profile_value('pass'))

    def create_buttons(self):
        self.cancel_button = QPushButton(_('Cancel'))
        #self.clear_button = QPushButton(_('Clear'))
        self.ok_button = QPushButton(_('OK'))
        self.add_button = QPushButton(_('Add'))

        layout = QHBoxLayout()
        layout.setDirection(QBoxLayout.RightToLeft)

        layout.addWidget(self.cancel_button)
        #layout.addWidget(self.clear_button)
        layout.addWidget(self.ok_button)
        layout.addStretch()
        layout.addWidget(self.add_button)

        self.buttons_widget().setLayout(layout)

    def connect_buttons(self):
        self.cancel_button.pressed.connect(self.reject)
        self.ok_button.pressed.connect(self.connect)
        #self.clear_button.pressed.connect(self.clear_fields)
        self.add_button.pressed.connect(self.add_profile)

    def connect(self):
        pass

    #def clear_fields(self):
    #    self.host_editor.clear()
    #    self.port_editor.clear()
    #    self.database_name_editor.clear()
    #    self.username_editor.clear()
    #    self.password_editor.clear()

    def add_profile(self):
        logger.info('adding new database profile')
        info = self.collect_info()
        if info:
            self.profiles.append(info)
            new = self.current_profile()
            self.profiles_choices.append((new, new.capitalize()))
            self.profile_editor.set_choices(self.profiles_choices)
        #store_profiles(self.profiles)

    def current_profile(self):
        #return self.profile_editor.get_value()
        # above returns ValueLoading...
        return self.profile_editor.itemData(self.profile_editor.currentIndex())

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
        logger.info('profilename = %s' % info['profilename'])
        info['dialect'] = self.dialect_editor.get_value()
        logger.info('dialect = %s' % info['dialect'])
        info['host'] = self.host_editor.text()
        logger.info('host = %s' % info['host'])
        info['port'] = self.port_editor.text()
        logger.info('port = %s' % info['port'])
        info['database'] = self.database_name_editor.text()
        logger.info('database = %s' % info['database'])
        info['user'] = self.username_editor.text()
        logger.info('user = %s' % info['user'])
        info['pass'] = self.password_editor.text()
        logger.info('pass = %s' % info['pass'])
        return info


#class ProfileCreationWizard(QWizard):
#
#    def __init__(self, parent):
#        super(ProfileCreationWizard, self).__init__(parent)
#        settings = QSettings()
#
#        self.setWindowTitle(_('Profile Creation Wizard'))
#
#        class DatabaseSettingsPage(QWizardPage):
#
#            def __init__(self):
#                super(nPage, self).__init__()
#                self.setTitle(_('Database Settings'))
#                self.setSubTitle(_('Please enter or change the credentials of '
#                    'the database.'))
#
#                self.layout = QGridLayout()
#                self.setLayout(self.layout)
#
#
#                #profiles = []
#                #self.registerField('database_profile', profile_widget,
#                #    'value', SIGNAL('editingFinished()'))
#
#                #dialects = [name for _importer, name, is_package \
#                #    in pkgutil.iter_modules(sqlalchemy.dialects.__path__ ) \
#                #    if is_package]
#
#                #self.registerField('database_dialect', dialect_widget,
#                #    'value', SIGNAL('editingFinished()'))
#                #dialect_widget.set_choices([(dialect, dialect.capitalize())
#                #    for dialect in dialects])
#                #dialect_widget.set_value(settings_database_dialect)
#
#                ## Qt docs specify that QLineEdit subclasses would work
#                ## fine with the registerField() function so we dont
#                ## need to set a property or signal
#
#                #database_host_widget.set_value(settings_database_host)
#                #self.registerField('database_host',  database_host_widget)
#
#                #database_user_widget.set_value(settings_database_user)
#                #self.registerField('database_user', database_user_widget)
#
#                #database_password_widget.set_value(settings_database_password)
#                #database_password_widget.setEchoMode(QLineEdit.Password)
#                #self.registerField('database_password',
#                #    database_password_widget)
#
#                #database_name_widget.set_value(settings_database_name)
#                #self.registerField('database_name', database_name_widget)
#
#                #layout.addWidget(create_new_profile_widget, 0, 3, Qt.AlignLeft)
#
#                #layout.addWidget(dialect_label_widget)
#                #layout.addWidget(dialect_widget)
#                #layout.addWidget(database_host_label_widget)
#                #layout.addWidget(database_host_widget)
#                #layout.addWidget(database_user_label_widget)
#                #layout.addWidget(database_user_widget)
#                #layout.addWidget(database_password_label_widget)
#                #layout.addWidget(database_password_widget)
#                #layout.addWidget(database_name_label_widget)
#                #layout.addWidget(database_name_widget)
#                #layout.addStretch(1)
#
#                #create_new_profile_widget.pressed.connect(
#                #    self.fill_in_profile_values)
#                #dialect_widget.valueChanged.connect(self.textChanged)
#                #database_host_widget.textChanged.connect(self.textChanged)
#                #database_user_widget.textChanged.connect(self.textChanged)
#                #database_password_widget.textChanged.connect(self.textChanged)
#                #database_name_widget.textChanged.connect(self.textChanged)
#
#            @QtCore.pyqtSlot()
#            @QtCore.pyqtSlot(str)
#            def textChanged(self, text=''):
#                self.completeChanged.emit()
#
#            def isComplete(self):
#                return True
#
#            def is_connection_valid(self, dialect, host, user, passwd, db):
#                self._connection_valid = False
#                connection_string = '%s://%s:%s@%s/%s' % (dialect, user,
#                    passwd, host, db)
#                engine = create_engine(connection_string, pool_recycle=True)
#                connection = engine.raw_connection()
#                cursor = connection.cursor()
#                cursor.close()
#                connection.close()
#                self._connection_valid = True
#                return True
#
#            def validatePage(self):
#                dialect = str(self.field('database_dialect').toString())
#                host = str(self.field('database_host').toString())
#                user = str(self.field('database_user').toString())
#                passwd = str(self.field('database_password').toString())
#                db = str(self.field('database_name').toString())
#
#                mt = SignalSlotModelThread(lambda:None)
#                mt.start()
#
#                progress = ProgressDialog(_('Verify database settings'))
#                mt.post(lambda:self.is_connection_valid(dialect, host, user,
#                    passwd, db), progress.finished, progress.exception)
#                progress.exec_()
#
#                return self._connection_valid
#
#        #class ConfigurationFinished(QWizardPage):
#
#        #    def initializePage(self):
#        #        self.setTitle(_('Configuration finished'))
#        #        self.setSubTitle(_('Congratulations, the database settings '
#        #            'will be saved'))
#
#        #        logger.info('Saving database settings')
#
#        #        settings.setValue('database/driver', QVariant(encode_setting(
#        #            'mysql')))
#        #        settings.setValue('database/dialect', QVariant(encode_setting(
#        #            str(self.field('database_dialect').toString()))))
#        #        settings.setValue('database/host', QVariant(encode_setting(
#        #            str(self.field('database_host').toString()))))
#        #        settings.setValue('database/user', QVariant(encode_setting(
#        #            str(self.field('database_user').toString()))))
#        #        settings.setValue('database/password', QVariant(encode_setting(
#        #            str(self.field('database_password').toString()))))
#        #        settings.setValue('database/name', QVariant(encode_setting(
#        #            str(self.field('database_name').toString()))))
#
#        #        logger.info('Database settings saved')
#
#        self.addPage(DatabaseSelectionPage())
#        #self.addPage(ConfigurationFinished())
#        self.setOption(QWizard.NoBackButtonOnStartPage)
#
#    def done(self, r):
#
#        if r:
#            logger.info('Saving database settings')
#
#            settings = QSettings()
#            settings.setValue('database/driver', QVariant(encode_setting(
#                'mysql')))
#            settings.setValue('database/dialect', QVariant(encode_setting(
#                str(self.field('database_dialect').toString()))))
#            settings.setValue('database/host', QVariant(encode_setting(
#                str(self.field('database_host').toString()))))
#            settings.setValue('database/user', QVariant(encode_setting(
#                str(self.field('database_user').toString()))))
#            settings.setValue('database/password', QVariant(encode_setting(
#                str(self.field('database_password').toString()))))
#            settings.setValue('database/name', QVariant(encode_setting(
#                str(self.field('database_name').toString()))))
#
#            logger.info('Database settings saved')
#
#        super(DatabaseSelectionWizard, self).done(r)
