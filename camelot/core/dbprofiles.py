#  ============================================================================
#
#  Copyright (C) 2007-2013 Conceptive Engineering bvba. All rights reserved.
#  www.conceptive.be / info@conceptive.be
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
#  visit www.python-camelot.com or contact info@conceptive.be
#
#  This file is provided AS IS with NO WARRANTY OF ANY KIND, INCLUDING THE
#  WARRANTY OF DESIGN, MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE.
#
#  For use of this library in commercial applications, please contact
#  info@conceptive.be
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

from PyQt4 import QtCore

from camelot.core.conf import settings

logger = logging.getLogger('camelot.core.dbprofiles')

profile_fields = [ 'name', 'dialect', 'host', 'database', 'user', 'password',
                   'port', 'media_location', 'locale_language', 'proxy_host',
                   'proxy_port', 'proxy_username', 'proxy_password' ]

@functools.total_ordering
class Profile(object):
    """This class holds the local configuration of the application, such as
    the location of the database.  It provides some convenience functions to
    store and retrieve this information to :class:`QtCore.QSettings`
    
    :param name: the name of the profile
    
    The Profile class has ordering methods based on the name of the profile
    object.
    """
    
    def __init__( self, name, **kwargs ):
        kwargs['name'] = name
        for profile_field in profile_fields:
            kwargs.setdefault( profile_field, '' )
        for key, value in kwargs.iteritems():
            setattr(self, key, value )
    
    def get_connection_string( self ):
        """The database connection string according to SQLAlchemy conventions,
        as specified by this profile.
        """
        connection_string = '%s://'%self.dialect
        if self.user or self.password:
            connection_string = connection_string + '%s:%s@'%( self.user, 
                                                               self.password )
        if self.host:
            connection_string = connection_string + self.host
        if self.port:
            connection_string = connection_string + ':%s'%self.port
        connection_string = connection_string + '/%s'%self.database
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
        for key, value in self.__dict__.iteritems():
            # flip 'pass' and 'password' for backward compatibility
            if key=='password':
                key='pass'
            elif key=='name':
                key='profilename'
            if key != 'profilename':
                state[key] = self._encode(value)
            else:
                state[key] = (value or '').encode('utf-8')
        return state
    
    def __setstate__( self, state ):
        """Restore the state of a profile object.from a dictionary.
        
        :param state: a `dict` with the profile information in encrypted and
            encoded form, as created by `__getstate__`.
        """
        for key, value in state.iteritems():
            if key=='pass':
                key='password'
            if key=='profilename':
                key='name'
            if key != 'name':
                value = self._decode(value)
            else:
                value = value.decode('utf-8')
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
    
    def _cipher( self ):
        """:return: the :class:`Crypto.Cipher` object used for encryption and
        decryption in :meth:`_encode` and :meth:`_decode`.
        """
        from Crypto.Cipher import ARC4
        key = settings.get('CAMELOT_DBPROFILES_CIPHER', 
                           'The Knights Who Say Ni')
        return ARC4.new( key )
    
    def _encode( self, value ):
        """Encrypt and encode a single value, this method is used in 
        `__getstate_`"""
        cipher = self._cipher()
        return base64.b64encode( cipher.encrypt( unicode(value).encode('utf-8' ) ) )
            
    def _decode( self, value ):
        """Decrypt and decode a single value, this method is used in 
        `__setstate__`
        """
        cipher = self._cipher()
        return cipher.decrypt( base64.b64decode( value ) ).decode('utf-8')    

class ProfileStore(object):
    """Class that reads/writes profiles, either to a file or to the local
    application settings.
    
    :param filename: the name of the file to read/write profiles from, if 
        left to `None`, the application settings are used.
       
    :param profile_class: a serializeable class that can be used to create
        new profile objects.
    """
    
    def __init__( self, filename=None, profile_class=Profile ):
        self.profile_class = profile_class
        if filename is None:
            self.settings = QtCore.QSettings()
        else:
            self.settings = QtCore.QSettings(filename, 
                                             QtCore.QSettings.IniFormat)

    def write_to_file(self, filename):
        file_store = ProfileStore(filename)
        file_store.write_profiles(self.read_profiles())
        
    def read_from_file(self, filename):
        file_store = ProfileStore(filename)
        self.write_profiles(file_store.read_profiles())
        
    def read_profiles(self):
        """
        :return: a list of profiles read
        """
        profiles = []
        size = self.settings.beginReadArray('database_profiles')
        if size == 0:
            return profiles
        empty = QtCore.QVariant('')
        for index in range(size):
            self.settings.setArrayIndex(index)
            profile = self.profile_class(name=None)
            state = profile.__getstate__()
            for key in state.keys():
                state[key] = str( self.settings.value(key, empty).toString() )
            profile.__setstate__(state)
            # only profiles with a name can be selected and handled
            if profile.name:
                profiles.append(profile)
        self.settings.endArray()
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
        self.settings.beginWriteArray('database_profiles')
        for index, profile in enumerate(profiles):
            self.settings.setArrayIndex(index)
            for key, value in profile.__getstate__().iteritems():
                self.settings.setValue(key, QtCore.QVariant(value))
        self.settings.endArray()
        self.settings.sync()
        
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
        name = unicode(self.settings.value('last_used_database_profile',
                                           QtCore.QVariant('')).toString(), 
                       'utf-8')
        for profile in profiles:
            if profile.name == name:
                return profile
            
    def set_last_profile(self, profile):
        """
        :param profile: a profile that has been written to or is available in
            the store
        """
        self.settings.setValue('last_used_database_profile', 
                               profile.name.encode('utf-8') )
