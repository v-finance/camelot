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

def encode_setting(value):
    result = base64.b64encode(str(value))
    return result


def decode_setting(value):
    result = base64.b64decode(str(value))
    return result


def last_used_profile():
    settings = QtCore.QSettings()
    return str(decode_setting(settings.value('last_used_database_profile',
        QVariant('')).toString()))


def fetch_profiles():
    profiles = {}
    settings = QtCore.QSettings()
    size = settings.beginReadArray('database_profiles')

    if size == 0:
        return profiles

    for index in range(size):
        settings.setArrayIndex(index)
        info = {}
        profilename = decode_setting(settings.value('profilename', QVariant('')).toString())
        if not profilename:
            continue  # well we should not really be doing anything
        info['dialect'] = decode_setting(settings.value('dialect', QVariant('')).toString())
        info['host'] = decode_setting(settings.value('host', QVariant('')).toString())
        info['port'] = decode_setting(settings.value('port', QVariant('')).toString())
        info['database'] = decode_setting(settings.value('database', QVariant('')).toString())
        info['user'] = decode_setting(settings.value('user', QVariant('')).toString())
        info['pass'] = decode_setting(settings.value('pass', QVariant('')).toString())
        info['media_location'] = decode_setting(settings.value('media_location', QVariant('')).toString())
        profiles[profilename] = info
    settings.endArray()

    return profiles


def store_profiles(profiles):
    settings = QtCore.QSettings()
    settings.beginWriteArray('database_profiles')

    for index, (profilename, info) in enumerate(profiles.items()):
        settings.setArrayIndex(index)
        settings.setValue('profilename', QVariant(encode_setting(profilename)))
        settings.setValue('dialect', QVariant(encode_setting(info['dialect'])))
        settings.setValue('host', QVariant(encode_setting(info['host'])))
        settings.setValue('port', QVariant(encode_setting(info['port'])))
        settings.setValue('database', QVariant(encode_setting(info['database'])))
        settings.setValue('user', QVariant(encode_setting(info['user'])))
        settings.setValue('pass', QVariant(encode_setting(info['pass'])))
        settings.setValue('media_location', QVariant(encode_setting(info['media_location'])))
    settings.endArray()


def use_chosen_profile(profilename, info):
    settings = QtCore.QSettings()
    settings.setValue('last_used_database_profile', QVariant(encode_setting(profilename)))
    settings.setValue('database/driver', QVariant(encode_setting('mysql')))
    settings.setValue('database/dialect', QVariant(encode_setting(info['dialect'])))
    settings.setValue('database/host', QVariant(encode_setting(info['host'])))
    settings.setValue('database/user', QVariant(encode_setting(info['user'])))
    settings.setValue('database/password', QVariant(encode_setting(info['pass'])))
    settings.setValue('database/name', QVariant(encode_setting(info['database'])))
    settings.setValue('extra/media_location', QVariant(encode_setting(info['media_location'])))
