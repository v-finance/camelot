#  ============================================================================
#
#  Copyright (C) 2007-2012 Conceptive Engineering bvba. All rights reserved.
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

from camelot.core.conf import settings

logger = logging.getLogger('camelot.core.dbprofiles')

def get_cipher():
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
    try:
        return profiles[profilename]
    except KeyError:
        logger.error( u'no profile named %s, available profiles are '%profilename )
        for key in profiles.keys():
            logger.error( u' - %s'%key )
        raise

def engine_from_profile():
    from sqlalchemy import create_engine
    profile = selected_profile_info()
    connect_args = dict()
    if profile['dialect'] == 'mysql':
        connect_args['charset'] = 'utf8'

    connection = '%s://%s:%s@%s:%s/%s' % (profile['dialect'],
                                          profile['user'],
                                          profile['pass'],
                                          profile['host'],
                                          profile['port'],
                                          profile['database'])
    return create_engine(connection, pool_recycle=True, connect_args=connect_args)

def media_root_from_profile():
    profile = selected_profile_info()
    return profile['media_location']

def stylesheet_from_profile():
    profile = selected_profile_info()
    from camelot.view import art
    return art.read( 'stylesheet/office2007_' + profile.get('stylesheet', 'blue') + '.qss' )

def last_used_profile():
    settings = QtCore.QSettings()
    return unicode(settings.value('last_used_database_profile',
        QtCore.QVariant('')).toString(), 'utf-8')

def fetch_profiles(from_file=None):
    profiles = {}
    try:
        if from_file is None:
            settings = QtCore.QSettings()
        else:
            settings = QtCore.QSettings(from_file, QtCore.QSettings.IniFormat)

        size = settings.beginReadArray('database_profiles')

        if size == 0:
            return profiles

        for index in range(size):
            settings.setArrayIndex(index)
            info = {}
            profilename = unicode(settings.value('profilename', QtCore.QVariant('')).toString(), 'utf-8')
            if not profilename:
                continue  # well we should not really be doing anything
            info['dialect'] = _decode_setting(settings.value('dialect', QtCore.QVariant('')).toString())
            info['host'] = _decode_setting(settings.value('host', QtCore.QVariant('')).toString())
            info['port'] = _decode_setting(settings.value('port', QtCore.QVariant('')).toString())
            info['database'] = _decode_setting(settings.value('database', QtCore.QVariant('')).toString())
            info['user'] = _decode_setting(settings.value('user', QtCore.QVariant('')).toString())
            info['pass'] = _decode_setting(settings.value('pass', QtCore.QVariant('')).toString())
            info['media_location'] = _decode_setting(settings.value('media_location', QtCore.QVariant('')).toString())
            info['locale_language'] = _decode_setting(settings.value('locale_language', QtCore.QVariant('')).toString())
            info['proxy_host'] = _decode_setting(settings.value('proxy_host', QtCore.QVariant('')).toString())
            info['proxy_port'] = _decode_setting(settings.value('proxy_port', QtCore.QVariant('')).toString())
            info['proxy_username'] = _decode_setting(settings.value('proxy_username', QtCore.QVariant('')).toString())
            info['proxy_password'] = _decode_setting(settings.value('proxy_password', QtCore.QVariant('')).toString())
            profiles[profilename] = info
        settings.endArray()
    except Exception, e:
        logger.warn('Could not read existing profiles, proceed with what was available', exc_info=e)
    return profiles

def store_profiles(profiles, to_file=None):
    if to_file is None:
        settings = QtCore.QSettings()
    else:
        settings = QtCore.QSettings(to_file, QtCore.QSettings.IniFormat)

    settings.beginWriteArray('database_profiles')

    for index, (profilename, info) in enumerate(profiles.items()):
        settings.setArrayIndex(index)
        settings.setValue('profilename', QtCore.QVariant(unicode(profilename).encode('utf-8')))
        settings.setValue('dialect', QtCore.QVariant(_encode_setting(info['dialect'])))
        settings.setValue('host', QtCore.QVariant(_encode_setting(info['host'])))
        settings.setValue('port', QtCore.QVariant(_encode_setting(info['port'])))
        settings.setValue('database', QtCore.QVariant(_encode_setting(info['database'])))
        settings.setValue('user', QtCore.QVariant(_encode_setting(info['user'])))
        settings.setValue('pass', QtCore.QVariant(_encode_setting(info['pass'])))
        settings.setValue('media_location', QtCore.QVariant(_encode_setting(info['media_location'])))
        settings.setValue('locale_language', QtCore.QVariant(_encode_setting(info['locale_language'])))
        settings.setValue('proxy_host', QtCore.QVariant(_encode_setting(info['proxy_host'])))
        settings.setValue('proxy_port', QtCore.QVariant(_encode_setting(info['proxy_port'])))
        settings.setValue('proxy_username', QtCore.QVariant(_encode_setting(info['proxy_username'])))
        settings.setValue('proxy_password', QtCore.QVariant(_encode_setting(info['proxy_password'])))
    settings.endArray()

def use_chosen_profile(profilename):
    settings = QtCore.QSettings()
    settings.setValue('last_used_database_profile', unicode(profilename).encode('utf-8') )

class EmptyProxy():

    @classmethod
    def hostName(cls):
        return ''

    @classmethod
    def user(cls):
        return ''

    @classmethod
    def port(cls):
        return ''

    @classmethod
    def password(cls):
        return ''

def get_network_proxy():
    # turn this temporary off, because it freezes the app on winblows
    return EmptyProxy()

    #from PyQt4 import QtNetwork

    #proxy = None
    #query = QtNetwork.QNetworkProxyQuery(QtCore.QUrl('http://aws.amazon.com'))
    ##proxies = QtNetwork.QNetworkProxyFactory.systemProxyForQuery(query)

    #if proxies:
        #logger.info('Proxy servers found: %s' % ['%s:%s' %
            #(str(proxy.hostName()),str(proxy.port())) for proxy in proxies])
        #if proxies[0].hostName():
            #proxy = proxies[0]

    ## we still need some empty values for the profile
    #if proxy is None:
        #return EmptyProxy()

    #return proxy

