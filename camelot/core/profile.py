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

"""
This module is used to store/retrieve user profiles on the local machine.
A user profile can contain information such as connection parameters to the
database or the language the user wants to use in the application.

For this module to function correctly, the `settings` should have an attribute
named `CAMELOT_DBPROFILES_CIPHER`.  This is a 'secret' per application string
that is used to encrypt the profile information as it is stored on the local
machine.
"""

import base64
import functools
import logging
import pkgutil
import sqlalchemy.dialects
from typing import Optional
import copy


from .qt import QtCore, QtWidgets

from camelot.core.conf import settings
from camelot.core.dataclasses import dataclass
from camelot.admin.dataclass_admin import DataclassAdmin
from camelot.view.controls import delegates
from camelot.admin.action import list_action


LOGGER = logging.getLogger('camelot.core.profile')


@functools.total_ordering
@dataclass
class Profile:
    """This class holds the local configuration of the application, such as
    the location of the database.  It provides some convenience functions to
    store and retrieve this information to :class:`QtCore.QSettings`
    
    :param name: the name of the profile
    
    The Profile class has ordering methods based on the name of the profile
    object.
    """
    
    name: str = ''
    dialect: Optional[str] = None
    host: str = ''
    port: Optional[int] = None
    database: str = ''
    user: str = ''
    password: str = ''
    media_location: str = ''
    locale_language: str = QtCore.QLocale.system().name()

    def get_connection_string( self ):
        """The database connection string according to SQLAlchemy conventions,
        as specified by this profile.
        """
        dialect = self.dialect or ''
        user = self.user or ''
        password = self.password or ''
        host = self.host or ''
        database = self.database or ''

        connection_string = '%s://' % dialect
        if user or password:
            connection_string = connection_string + '%s:%s@' % (user, password)
        if host:
            connection_string = connection_string + host
        if self.port:
            connection_string = connection_string + ':%s' % self.port
        connection_string = connection_string + '/%s' % database
        return connection_string
    
    def create_engine( self, **kwargs ):
        """
        create a SQLAlchemy Engine from the selected profile, all arguments
        are passed to the `create_engine` function.
        """
        from sqlalchemy import create_engine
        kwargs.setdefault( 'pool_recycle', 600 )
        if self.dialect == 'mysql':
            kwargs.setdefault( 'connect_args', dict(charset='utf8') )
        return create_engine( self.get_connection_string(), **kwargs )

    def get_language_code(self):
        """
        :return: two-letter ISO 639 language code
        """
        return self.locale_language[:2]
    
    def get_country_code(self):
        """
        :return: two-letter ISO 3166 country code
        """
        return self.locale_language[2:]
        
    def __getstate__( self ):
        """Retrieve the state of a profile object into a dictionary
        
        :return: a `dict` with the profile information, in encrypted and 
            encoded form
        """
        state = dict()
        for key, value in self.__dict__.items():
            # flip 'pass' and 'password' for backward compatibility
            if key=='password':
                key='pass'
            elif key=='name':
                key='profilename'
            # Avoid None values
            if value is None and key != 'port':
                value = ''
            state[key] = value
        return state
    
    def __setstate__( self, state ):
        """Restore the state of a profile object.from a dictionary.
        
        :param state: a `dict` with the profile information in encrypted and
            encoded form, as created by `__getstate__`.
        """
        for key, value in state.items():
            if key=='pass':
                key='password'
            if key=='profilename':
                key='name'
            setattr(self, key, value)

    def __lt__(self, other):
        if isinstance(other, Profile):
            return self.name.__lt__(other.name)
        return id(self) < id(other)
    
    def __eq__(self, other):
        if isinstance(other, Profile):
            return self.name.__eq__(other.name)
        return False
    
    def __hash__(self):
        return hash(self.name)

    class Admin(DataclassAdmin):
        list_display = ['name', 'dialect', 'host', 'port', 'database']
        form_display = ['name', 'dialect', 'host', 'port', 'database', 'user', 'password', 'media_location', 'locale_language']
        related_toolbar_actions = [
            list_action.delete_selection,
            list_action.duplicate_selection,
            list_action.add_new_profile
        ]
        list_action = list_action.edit_profile
        field_attributes = {
            'dialect': {
                'choices': [(name,name) for i, name in enumerate([name for _importer, name, is_package in pkgutil.iter_modules(sqlalchemy.dialects.__path__)])]
            },
            'host': { 'nullable': True },
            'port': {
                'nullable': True,
                'delegate': delegates.IntegerDelegate,
                'calculator': False
            },
            'database': { 'nullable': True },
            'user': { 'nullable': True },
            'password': {
                'nullable': True,
                'echo_mode': QtWidgets.QLineEdit.EchoMode.Password
            },
            'media_location': {
                'nullable': True,
                'delegate': delegates.LocalFileDelegate,
                'directory': True
            },
            'locale_language': {
                'nullable': True,
                'delegate': delegates.LanguageDelegate
            },
        }

        def copy(self, entity_instance):
            new_entity_instance = super().copy(entity_instance)
            new_entity_instance.name = new_entity_instance.name + ' - Copy'
            return new_entity_instance

class NonEditableProfileAdmin(Profile.Admin):
        field_attributes = copy.deepcopy(Profile.Admin.field_attributes)

for field in Profile.Admin.list_display:
    NonEditableProfileAdmin.field_attributes.setdefault(field, {})['editable'] = False

class ProfileStore(object):
    """Class that reads/writes profiles, either to a file or to the local
    application settings.
    
    :param filename: the name of the file to read/write profiles from, if 
        left to `None`, the application settings are used.
       
    :param profile_class: a serializeable class that can be used to create
        new profile objects.
        
    :param cipher_key: cipher key used to encrypt profile information to make
        it only readeable to the application itself.  If left to `None`,
        `camelot.core.conf.settings.CAMELOT_DBPROFILES_CIPHER is used.

    Profiles are supposed to be encrypted within the settings, unless the
    profile has a key with the name `encrypted` and a value different from `1`.
    This allows an external script or application that does not know the
    cipther to generate a profile.  Upon first modification, the profile will
    be encrypted.
    """
    
    def __init__( self, filename=None, profile_class=Profile, cipher_key=None):
        if cipher_key is None:
            cipher_key = settings.get('CAMELOT_DBPROFILES_CIPHER', 
                                      'The Knights Who Say Ni')
        self.cipher_key = cipher_key
        self.profile_class = profile_class
        self.filename = filename

    def _cipher( self ):
        """:return: the :class:`Crypto.Cipher` object used for encryption and
        decryption in :meth:`_encode` and :meth:`_decode`.
        """
        from .pyarc4 import Arc4
        return Arc4(self.cipher_key.encode('ascii'))

    def _encode( self, value ):
        """Encrypt and encode a single value, this method is used to 
        write profiles."""
        cipher = self._cipher()
        if value is None:
            value = ''
        return base64.b64encode( cipher.encrypt( str(value).encode('utf-8' ) ) ).decode('ascii')
            
    def _decode( self, value ):
        """Decrypt and decode a single value, this method is used to
        read profiles.
        """
        cipher = self._cipher()
        return cipher.decrypt( base64.b64decode( value ) ).decode('utf-8')

    def _qsettings(self):
        # recreate QSettings each time it's needed, to make sure we're at
        # the same entry point
        if self.filename is None:
            return QtCore.QSettings()
        else:
            return QtCore.QSettings(self.filename, 
                                    QtCore.QSettings.Format.IniFormat)
    
    def write_to_file(self, filename):
        file_store = ProfileStore(filename, cipher_key=self.cipher_key)
        file_store.write_profiles(self.read_profiles())
        
    def read_from_file(self, filename):
        file_store = ProfileStore(filename, cipher_key=self.cipher_key)
        self.write_profiles(file_store.read_profiles())
        
    def read_profiles(self):
        """
        :return: a list of profiles read
        """
        profiles = []
        qsettings = self._qsettings()
        size = qsettings.beginReadArray('database_profiles')
        if size == 0:
            return profiles
        empty = b''
        for index in range(size):
            qsettings.setArrayIndex(index)
            profile = self.profile_class(name=None)
            state = profile.__getstate__()
            encrypted = int(qsettings.value('encrypted', 1))
            for key in state.keys():
                value = qsettings.value(key, empty)
                if (key != 'profilename') and (encrypted==1):
                    value = self._decode(value or b'')
                else:
                    value = value
                state[key] = value
            profile.__setstate__(state)
            # Port used to be stored as string
            try:
                profile.port = int(profile.port)
            except ValueError:
                profile.port = None
            # only profiles with a name can be selected and handled
            if profile.name:
                profiles.append(profile)
        qsettings.endArray()
        return profiles
    
    def read_profile(self, name):
        """
        :return: the profile object with the requested name, 
            `None` if there is no such profile
        """
        for profile in self.read_profiles():
            if profile.name==name:
                return profile
            
    def write_profiles(self, profiles):
        """
        :param profiles: a list of profiles
        """
        qsettings = self._qsettings()
        qsettings.beginWriteArray('database_profiles', len(profiles))
        for index, profile in enumerate(profiles):
            qsettings.setArrayIndex(index)
            qsettings.setValue('encrypted', 1)
            for key, value in profile.__getstate__().items():
                if key != 'profilename':
                    value = self._encode(value)
                else:
                    value = (value or u'')
                qsettings.setValue(key, value)
        qsettings.endArray()
        qsettings.sync()
        
    def write_profile(self, profile):
        """
        :param profile: a :class:`Profile` object
        """
        profiles = self.read_profiles()
        for existing_profile in profiles:
            if existing_profile.name == profile.name:
                profiles.remove(existing_profile)
                break
        profiles.append(profile)
        self.write_profiles(profiles)
    
    def get_last_profile(self):
        """
        :return: the last used profile, or `None` of no profile has been used
            yet or the profile information is not available.
        """
        profiles = self.read_profiles()
        name = self._qsettings().value('last_used_database_profile', u'')
        for profile in profiles:
            if profile.name == name:
                return profile
            
    def set_last_profile(self, profile):
        """
        :param profile: a profile that has been written to or is available in
            the store
        """
        qsettings = self._qsettings()
        qsettings.setValue('last_used_database_profile', 
                           profile.name)
        qsettings.sync()

