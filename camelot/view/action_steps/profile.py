#  ============================================================================
#
#  Copyright (C) 2007-2016 Conceptive Engineering bvba.
#  www.conceptive.be / info@conceptive.be
#
#  Redistribution and use in source and binary forms, with or without
#  modification, are permitted provided that the following conditions are met:
#      * Redistributions of source code must retain the above copyright
#        notice, this list of conditions and the following disclaimer.
#      * Redistributions in binary form must reproduce the above copyright
#        notice, this list of conditions and the following disclaimer in the
#        documentation and/or other materials provided with the distribution.
#      * Neither the name of Conceptive Engineering nor the
#        names of its contributors may be used to endorse or promote products
#        derived from this software without specific prior written permission.
#  
#  THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
#  ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
#  WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
#  DISCLAIMED. IN NO EVENT SHALL <COPYRIGHT HOLDER> BE LIABLE FOR ANY
#  DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
#  (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
#  LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
#  ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
#  (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
#  SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#
#  ============================================================================

import logging
import pkgutil

import six

from ...core.qt import QtCore, QtGui, QtWidgets, QtNetwork, Qt

from camelot.admin.action import ActionStep
from camelot.core.exception import CancelRequest
from camelot.core.utils import ugettext as _
from camelot.view import art
from camelot.view.controls.editors import ChoicesEditor, TextLineEditor, LanguageEditor
from camelot.view.controls.standalone_wizard_page import HSeparator, StandaloneWizardPage

logger = logging.getLogger('camelot.view.action_steps.profile')

class ProfileWizard(StandaloneWizardPage):
    """Wizard for the creation of a new database
profile.

.. attribute:: languages
.. attribute:: dialects

A list of languages allowed in the profile selection, an empty list will
allow all languages
    """

    languages = []
    dialects = []

    def __init__(self, profiles, parent=None):
        super(ProfileWizard, self).__init__(parent)

        self._connection_valid = False
        self.network_reply = None
        self.profiles = dict((profile.name,profile) for profile in profiles)

        self.setWindowTitle(_('Profile Wizard'))
        self.set_banner_logo_pixmap(art.Icon('tango/22x22/categories/preferences-system.png').getQPixmap())
        self.set_banner_title(_('Create New/Edit Profile'))
        self.set_banner_subtitle(_('Please enter the database settings'))
        self.banner_widget().setStyleSheet('background-color: white;')

        self.manager = QtNetwork.QNetworkAccessManager( self )
        self.manager.finished.connect( self.update_network_status )

        self.create_labels_and_widgets()
        self.create_buttons()
        self.set_tab_order()
        self.set_widgets_values()
        # note: connections come after labels and widgets are created
        # and have default values
        self.connect_widgets()
        self.connect_buttons()
        self.toggle_ok_button()

        timer = QtCore.QTimer(self)
        timer.timeout.connect( self.new_network_request )
        timer.setInterval( 3000 )
        timer.start()
        self.new_network_request()

    def create_labels_and_widgets(self):
        self.profile_label = QtWidgets.QLabel(_('Profile Name:'))
        self.dialect_label = QtWidgets.QLabel(_('Driver:'))
        self.host_label = QtWidgets.QLabel(_('Server Host:'))
        self.port_label = QtWidgets.QLabel(_('Port:'))
        self.database_name_label = QtWidgets.QLabel(_('Database Name:'))
        self.username_label = QtWidgets.QLabel(_('Username:'))
        self.password_label = QtWidgets.QLabel(_('Password:'))
        self.media_location_label = QtWidgets.QLabel(_('Media Location:'))
        self.language_label = QtWidgets.QLabel(_('Language:'))
        self.proxy_host_label = QtWidgets.QLabel(_('Proxy Host:'))
        self.proxy_port_label = QtWidgets.QLabel(_('Port:'))
        self.proxy_username_label = QtWidgets.QLabel(_('Proxy Username:'))
        self.proxy_password_label = QtWidgets.QLabel(_('Proxy Password:'))
        self.network_status_label = QtWidgets.QLabel()

        self.not_accessible_media_path_label = QtWidgets.QLabel(_('Media location path '\
            'is not accessible.'))
        self.not_accessible_media_path_label.setStyleSheet('color: red')
        self.not_writable_media_path_label = QtWidgets.QLabel(_('Media location path '\
            'is not writable.'))
        self.not_writable_media_path_label.setStyleSheet('color: red')

        layout = QtGui.QGridLayout()

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

        self.profile_editor = QtWidgets.QComboBox(self)
        self.profile_editor.setEditable(True)

        # 32767 is Qt max length for string
        # should be more than enough for folders
        # http://doc.qt.nokia.com/latest/qlineedit.html#maxLength-prop
        self.dialect_editor = ChoicesEditor(parent=self)
        self.dialect_editor.set_value(None)
        self.host_editor = TextLineEditor(self, length=32767)
        self.host_editor.set_value('')
        self.port_editor = TextLineEditor(self)
        self.port_editor.setFixedWidth(60)
        self.port_editor.set_value('')
        self.database_name_editor = TextLineEditor(self, length=32767)
        self.database_name_editor.set_value('')
        self.username_editor = TextLineEditor(self)
        self.username_editor.set_value('')
        self.password_editor = TextLineEditor(
            echo_mode=QtWidgets.QLineEdit.Password,
            parent=self
        )
        self.password_editor.set_value('')
        self.media_location_editor = TextLineEditor(self, length=32767)
        self.media_location_editor.set_value('')
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
        self.proxy_host_editor.set_value('')
        self.proxy_port_editor = TextLineEditor(self)
        self.proxy_port_editor.setFixedWidth(60)
        self.proxy_port_editor.set_value('')
        self.proxy_username_editor = TextLineEditor(self)
        self.proxy_username_editor.set_value('')
        self.proxy_password_editor = TextLineEditor(
            echo_mode=QtWidgets.QLineEdit.Password,
            parent=self
        )
        self.proxy_password_editor.set_value('')

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

        layout.addWidget(self.network_status_label, 13, 1, 1, 4)

        self.main_widget().setLayout(layout)

    def set_widgets_values(self):
        self.profile_editor.clear()
        self.dialect_editor.set_value(None)

        if self.dialects:
            dialects = self.dialects
        else:
            import sqlalchemy.dialects
            dialects = [name for _importer, name, is_package in \
                        pkgutil.iter_modules(sqlalchemy.dialects.__path__) \
                        if is_package]
        self.dialect_editor.set_choices([(dialect, dialect.capitalize()) \
            for dialect in dialects])

        self.profile_editor.insertItems(1, [''] + list(self.profiles.keys()))
        self.profile_editor.setFocus()
        self.update_wizard_values()

    def connect_widgets(self):
        self.profile_editor.editTextChanged.connect(self.toggle_ok_button)
        self.profile_editor.currentIndexChanged.connect(self.update_wizard_values)
        self.dialect_editor.editingFinished.connect(self.toggle_ok_button)

    def create_buttons(self):
        self.cancel_button = QtWidgets.QPushButton(_('Cancel'))
        self.ok_button = QtWidgets.QPushButton(_('OK'))

        layout = QtWidgets.QHBoxLayout()
        layout.setDirection(QtWidgets.QBoxLayout.RightToLeft)

        layout.addWidget(self.cancel_button)
        layout.addWidget(self.ok_button)
        layout.addStretch()

        self.buttons_widget().setLayout(layout)

        self.browse_button = QtWidgets.QPushButton(_('Browse'))
        self.main_widget().layout().addWidget(self.browse_button, 7, 2, 1, 3)

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
        self.ok_button.pressed.connect(self.accept)
        self.browse_button.pressed.connect(self.fill_media_location)

    @QtCore.qt_slot()
    def toggle_ok_button(self):
        enabled = bool(self.profile_editor.currentText()) and bool(self.dialect_editor.get_value())
        self.ok_button.setEnabled(enabled)

    def current_profile(self):
        text = six.text_type(self.profile_editor.currentText())
        return text

    def set_current_profile(self, profile_name):
        self.profile_editor.lineEdit().setText(profile_name)
        self.update_wizard_values()

    def update_wizard_values(self):
        #network_proxy = get_network_proxy()
        # self.dialect_editor.set_value(self.get_profile_value('dialect') or 'mysql')
        # self.host_editor.setText(self.get_profile_value('host') or '127.0.0.1')
        # self.port_editor.setText(self.get_profile_value('port') or '3306')
        self.dialect_editor.set_value(self.get_profile_value('dialect') or None)
        self.host_editor.set_value(self.get_profile_value('host'))
        self.port_editor.set_value(self.get_profile_value('port'))
        # self.port_editor.setText(self.get_profile_value('port') or self._related_default_port(self.dialect_editor))
        self.database_name_editor.set_value(self.get_profile_value('database'))
        self.username_editor.set_value(self.get_profile_value('user'))
        self.password_editor.set_value(self.get_profile_value('password'))
        self.media_location_editor.set_value(self.get_profile_value('media_location'))
        self.language_editor.set_value(self.get_profile_value('locale_language'))
        self.proxy_host_editor.set_value(self.get_profile_value('proxy_host'))
        self.proxy_port_editor.set_value(self.get_profile_value('proxy_port'))
        self.proxy_username_editor.set_value(self.get_profile_value('proxy_username'))
        self.proxy_password_editor.set_value(self.get_profile_value('proxy_password'))
        self.network_status_label.setText('')
        self.network_status_label.setStyleSheet('')
        self.toggle_ok_button()

    # this line segfaults on OSX using Python 3.3
    #@QtCore.qt_slot(QtNetwork.QNetworkReply)
    def update_network_status(self, reply):
        if reply.isFinished():
            error = reply.error()
            if error == QtNetwork.QNetworkReply.NoError:
                self.network_status_label.setText(_('Internet available.'))
                self.network_status_label.setStyleSheet('color: green')
                return
        self.network_status_label.setText(_('Internet not available.\n%s.'%reply.errorString()))
        self.network_status_label.setStyleSheet('color: red')

    @QtCore.qt_slot()
    def new_network_request(self):
        if self.network_reply and not self.network_reply.isFinished():
            self.network_reply.abort()
        if self.proxy_host_editor.get_value() and self.proxy_port_editor.get_value():
            proxy = QtNetwork.QNetworkProxy( QtNetwork.QNetworkProxy.HttpProxy,
                                             self.proxy_host_editor.get_value(),
                                             int( str( self.proxy_port_editor.get_value() ) ) )#,
                                             #self.proxy_username_editor.text(),
                                             #self.proxy_password_editor.text() )
            self.manager.setProxy( proxy )
        else:
            self.manager.setProxy( QtNetwork.QNetworkProxy() )
        self.network_reply = self.manager.get( QtNetwork.QNetworkRequest( QtCore.QUrl('http://aws.amazon.com') ) )

    def get_profile_value(self, key):
        current = self.current_profile()
        if current in self.profiles:
            return getattr(self.profiles[current], key)
        return ''

    def get_profile_info(self):
        logger.info('collecting new database profile info')
        info = {}
        info['name'] = self.current_profile()
        info['dialect'] = self.dialect_editor.get_value()
        info['host'] = self.host_editor.get_value()
        info['port'] = self.port_editor.get_value()
        info['database'] = self.database_name_editor.get_value()
        info['user'] = self.username_editor.get_value()
        info['password'] = self.password_editor.get_value()
        info['media_location'] = self.media_location_editor.get_value()
        info['locale_language'] = self.language_editor.get_value()
        info['proxy_host'] = self.proxy_host_editor.get_value()
        info['proxy_port'] = self.proxy_port_editor.get_value()
        info['proxy_username'] = self.proxy_username_editor.get_value()
        info['proxy_password'] = self.proxy_password_editor.get_value()
        return info

    def fill_media_location(self):
        caption = _('Select media location')
        selected = six.text_type(QtGui.QFileDialog.getExistingDirectory(self, caption))

        if not selected:
            return

        info = QtCore.QFileInfo(selected)
        if not info.isReadable():
            self.main_widget().layout().addWidget(
                self.not_accessible_media_path_label, 13, 1, 1, 4)
            return
        if not info.isWritable():
            self.main_widget().layout().addWidget(
                self.not_writable_media_path_label, 13, 1, 1, 4)
            return

        self.media_location_editor.set_value(selected)


class EditProfiles(ActionStep):
    """Allows the user to change or create his current database and media
    settings.

    :param profiles: a list of :class:`camelot.core.profile.Profile` objects
    :param dialog_class: a :class:`QtWidgets.QDialog` to display the needed
        fields to store in a profile
    :param current_profile`: the name of the current profile, or an empty string
        if there is no current profile.

    .. image:: /_static/actionsteps/edit_profile.png
    """

    def __init__(self, profiles, current_profile='', dialog_class=None):
        self.profiles = profiles
        if dialog_class is None:
            self.dialog_class = ProfileWizard
        else:
            self.dialog_class = dialog_class
        self.current_profile = current_profile

    def render(self, gui_context):
        dialog = self.dialog_class(self.profiles)
        dialog.set_current_profile(self.current_profile)
        return dialog

    def gui_run(self, gui_context):
        dialog = self.render(gui_context)
        result = dialog.exec_()
        if result == QtWidgets.QDialog.Rejected:
            raise CancelRequest()
        return dialog.get_profile_info()

