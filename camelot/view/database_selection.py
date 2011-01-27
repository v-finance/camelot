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
from PyQt4.QtGui import QWizard, QWizardPage, QVBoxLayout, QLabel, QLineEdit
from PyQt4.QtCore import QSettings, QVariant, SIGNAL

from camelot.view import art
from camelot.view.controls.editors import ChoicesEditor, TextLineEditor
from camelot.view.controls.progress_dialog import ProgressDialog
from camelot.core.utils import ugettext as _
from camelot.view.model_thread.signal_slot_model_thread import \
    SignalSlotModelThread

logger = logging.getLogger('camelot.view.database_configure')


def encode_setting(value):
    result = base64.b64encode(str(value))
    return result


def decode_setting(value):
    result = base64.b64decode(str(value))
    return result


def select_database():
    wizard = DatabaseSelectionWizard(None)
    wizard.setPixmap(QWizard.LogoPixmap,
        art.Icon('tango/22x22/categories/preferences-system.png').getQPixmap())
    wizard.exec_()


class DatabaseSelectionWizard(QWizard):

    def __init__(self, parent):
        super(DatabaseSelectionWizard, self).__init__(parent)
        settings = QSettings()

        self.setWindowTitle(_('Database Selection'))

        settings_database_dialect = decode_setting(
            settings.value('database/dialect', QVariant('')).toString()) \
                or 'mysql'
        settings_database_host = decode_setting(
            settings.value('database/host', QVariant('')).toString())
        settings_database_user = decode_setting(
            settings.value('database/user', QVariant('')).toString())
        settings_database_password = decode_setting(
            settings.value('database/password', QVariant('')).toString())
        settings_database_name = decode_setting(
            settings.value('database/name', QVariant('')).toString())

        class DatabaseSelectionPage(QWizardPage):

            def __init__(self):
                super(DatabaseSelectionPage, self).__init__()
                self.setTitle(_('Database Settings'))
                self.setSubTitle(_('Please enter or change the credentials of '
                    'the database.'))

                layout = QVBoxLayout()

                dialect_label_widget = QLabel(_('Driver'))
                dialect_widget = ChoicesEditor(parent=self)
                dialects = [name for _importer, name, is_package \
                    in pkgutil.iter_modules(sqlalchemy.dialects.__path__ ) \
                    if is_package]

                self.registerField('database_dialect', dialect_widget,
                    'value', SIGNAL('editingFinished()'))
                dialect_widget.set_choices([(dialect, dialect.capitalize())
                    for dialect in dialects])
                dialect_widget.set_value(settings_database_dialect)

                # Qt docs specify that QLineEdit subclasses would work
                # fine with the registerField() function so we dont
                # need to set a property or signal

                database_host_label_widget = QLabel(_('Host'))
                database_host_widget = TextLineEditor(self)
                database_host_widget.set_value(settings_database_host)
                self.registerField('database_host',  database_host_widget)

                database_user_label_widget = QLabel(_('Username'))
                database_user_widget = TextLineEditor(self)
                database_user_widget.set_value(settings_database_user)
                self.registerField('database_user', database_user_widget)

                database_password_label_widget = QLabel(_('Password'))
                database_password_widget = TextLineEditor(self)
                database_password_widget.set_value(settings_database_password)
                database_password_widget.setEchoMode(QLineEdit.Password)
                self.registerField('database_password',
                    database_password_widget)

                database_name_label_widget = QLabel(_('Database'))
                database_name_widget = TextLineEditor(self)
                database_name_widget.set_value(settings_database_name)
                self.registerField('database_name', database_name_widget)

                layout.addWidget(dialect_label_widget)
                layout.addWidget(dialect_widget)
                layout.addWidget(database_host_label_widget)
                layout.addWidget(database_host_widget)
                layout.addWidget(database_user_label_widget)
                layout.addWidget(database_user_widget)
                layout.addWidget(database_password_label_widget)
                layout.addWidget(database_password_widget)
                layout.addWidget(database_name_label_widget)
                layout.addWidget(database_name_widget)
                layout.addStretch(1)
                self.setLayout(layout)

                dialect_widget.valueChanged.connect(self.textChanged)
                database_host_widget.textChanged.connect(self.textChanged)
                database_user_widget.textChanged.connect(self.textChanged)
                database_password_widget.textChanged.connect(self.textChanged)
                database_name_widget.textChanged.connect(self.textChanged)

            @QtCore.pyqtSlot()
            @QtCore.pyqtSlot(str)
            def textChanged(self, text=''):
                self.completeChanged.emit()

            def isComplete(self):
                return True

            def is_connection_valid(self, dialect, host, user, passwd, db):
                self._connection_valid = False
                connection_string = '%s://%s:%s@%s/%s' % (dialect, user,
                    passwd, host, db)
                engine = create_engine(connection_string, pool_recycle=True)
                connection = engine.raw_connection()
                cursor = connection.cursor()
                cursor.close()
                connection.close()
                self._connection_valid = True
                return True

            def validatePage(self):
                dialect = str(self.field('database_dialect').toString())
                host = str(self.field('database_host').toString())
                user = str(self.field('database_user').toString())
                passwd = str(self.field('database_password').toString())
                db = str(self.field('database_name').toString())

                mt = SignalSlotModelThread(lambda:None)
                mt.start()

                progress = ProgressDialog(_('Verify database settings'))
                mt.post(lambda:self.is_connection_valid(dialect, host, user,
                    passwd, db), progress.finished, progress.exception)
                progress.exec_()

                return self._connection_valid

        class ConfigurationFinished(QWizardPage):

            def initializePage(self):
                self.setTitle(_('Configuration finished'))
                self.setSubTitle(_('Congratulations, the database settings '
                    'will be saved'))

                logger.info('Saving database settings')

                settings.setValue('database/driver', QVariant(encode_setting(
                    'mysql')))
                settings.setValue('database/dialect', QVariant(encode_setting(
                    str(self.field('database_dialect').toString()))))
                settings.setValue('database/host', QVariant(encode_setting(
                    str(self.field('database_host').toString()))))
                settings.setValue('database/user', QVariant(encode_setting(
                    str(self.field('database_user').toString()))))
                settings.setValue('database/password', QVariant(encode_setting(
                    str(self.field('database_password').toString()))))
                settings.setValue('database/name', QVariant(encode_setting(
                    str(self.field('database_name').toString()))))

                logger.info('Database settings saved')

        self.addPage(DatabaseSelectionPage())
        self.addPage(ConfigurationFinished())
        self.setOption(QWizard.NoBackButtonOnStartPage)
