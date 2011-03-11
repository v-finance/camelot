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

from PyQt4 import QtCore
from PyQt4.QtCore import QVariant

logger = logging.getLogger('camelot.core.dbprofiles')

def get_cipher():
    import settings
    from Crypto.Cipher import ARC4
    if hasattr( settings, 'CAMELOT_DBPROFILES_CIPHER' ):
        key = getattr( settings, 'CAMELOT_DBPROFILES_CIPHER' )
    else:
        key = 'The Knights Who Say Ni'
    return ARC4.new( key )

def get_languagecode(profile=None):
    """
    :return: two-letter ISO 639 language code
    """
    if not profile:
        profile = selected_profile_info()
    return selected_profile_info()['locale_language'][:2]

def get_countrycode(profile=None):
    """
    :return: two-letter ISO 3166 country code
    """
    if not profile:
        profile = selected_profile_info()
    return selected_profile_info()['locale_language'][2:]

def _encode_setting(value):
    return base64.b64encode( get_cipher().encrypt( unicode(value).encode('utf-8' ) ) )

def _decode_setting(value):
    return get_cipher().decrypt( base64.b64decode( value ) ).decode('utf-8')

def selected_profile_info():
    """
    :return: a dict with the info of the selected profile
    """
    profiles = fetch_profiles()
    profilename = last_used_profile()
    return profiles[profilename]
    
def engine_from_profile():
    from sqlalchemy import create_engine
    profile = selected_profile_info()   
    connect_args = dict()
    if profile['dialect'] == 'mysql':
        connect_args['charset'] = 'utf8'
                    
    connection = '%s://%s:%s@%s/%s' % (profile['dialect'], 
                                       profile['user'], 
                                       profile['pass'], 
                                       profile['host'], 
                                       profile['database'])
    return create_engine(connection, pool_recycle=True, connect_args=connect_args)

def last_used_profile():
    settings = QtCore.QSettings()
    return unicode(settings.value('last_used_database_profile',
        QVariant('')).toString(), 'utf-8')

def fetch_profiles():
    profiles = {}
    try:
        settings = QtCore.QSettings()
        size = settings.beginReadArray('database_profiles')
    
        if size == 0:
            return profiles
    
        for index in range(size):
            settings.setArrayIndex(index)
            info = {}
            profilename = unicode(settings.value('profilename', QVariant('')).toString(), 'utf-8')
            if not profilename:
                continue  # well we should not really be doing anything
            info['dialect'] = _decode_setting(settings.value('dialect', QVariant('')).toString())
            info['host'] = _decode_setting(settings.value('host', QVariant('')).toString())
            info['port'] = _decode_setting(settings.value('port', QVariant('')).toString())
            info['database'] = _decode_setting(settings.value('database', QVariant('')).toString())
            info['user'] = _decode_setting(settings.value('user', QVariant('')).toString())
            info['pass'] = _decode_setting(settings.value('pass', QVariant('')).toString())
            info['media_location'] = _decode_setting(settings.value('media_location', QVariant('')).toString())
            info['locale_language'] = _decode_setting(settings.value('locale_language', QVariant('')).toString())
            info['proxy_host'] = _decode_setting(settings.value('proxy_host', QVariant('')).toString())
            info['proxy_username'] = _decode_setting(settings.value('proxy_username', QVariant('')).toString())
            info['proxy_password'] = _decode_setting(settings.value('proxy_password', QVariant('')).toString())
            profiles[profilename] = info
        settings.endArray()
    except Exception, e:
        logger.warn('Could not read existing profiles, proceed with what was available', exc_info=e)
    return profiles

def store_profiles(profiles):
    settings = QtCore.QSettings()
    settings.beginWriteArray('database_profiles')

    for index, (profilename, info) in enumerate(profiles.items()):
        settings.setArrayIndex(index)
        settings.setValue('profilename', QVariant(unicode(profilename).encode('utf-8')))
        settings.setValue('dialect', QVariant(_encode_setting(info['dialect'])))
        settings.setValue('host', QVariant(_encode_setting(info['host'])))
        settings.setValue('port', QVariant(_encode_setting(info['port'])))
        settings.setValue('database', QVariant(_encode_setting(info['database'])))
        settings.setValue('user', QVariant(_encode_setting(info['user'])))
        settings.setValue('pass', QVariant(_encode_setting(info['pass'])))
        settings.setValue('media_location', QVariant(_encode_setting(info['media_location'])))
        settings.setValue('locale_language', QVariant(_encode_setting(info['locale_language'])))
        settings.setValue('proxy_host', QVariant(_encode_setting(info['proxy_host'])))
        settings.setValue('proxy_username', QVariant(_encode_setting(info['proxy_username'])))
        settings.setValue('proxy_password', QVariant(_encode_setting(info['proxy_password'])))
    settings.endArray()

def use_chosen_profile(profilename):
    settings = QtCore.QSettings()
    settings.setValue('last_used_database_profile', unicode(profilename).encode('utf-8') )
