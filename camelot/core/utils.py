#  ============================================================================
#
#  Copyright (C) 2007-2008 Conceptive Engineering bvba. All rights reserved.
#  www.conceptive.be / project-camelot@conceptive.be
#
#  This file is part of the Camelot Library.
#
#  This file may be used under the terms of the GNU General Public
#  License version 2.0 as published by the Free Software Foundation
#  and appearing in the file LICENSE.GPL included in the packaging of
#  this file.  Please review the following information to ensure GNU
#  General Public Licensing requirements will be met:
#  http://www.trolltech.com/products/qt/opensource.html
#
#  If you are unsure which license is appropriate for your use, please
#  review the following information:
#  http://www.trolltech.com/products/qt/licensing.html or contact
#  project-camelot@conceptive.be.
#
#  This file is provided AS IS with NO WARRANTY OF ANY KIND, INCLUDING THE
#  WARRANTY OF DESIGN, MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE.
#
#  For use of this library in commercial applications, please contact
#  project-camelot@conceptive.be
#
#  ============================================================================

"""Utility functions"""

from PyQt4 import QtCore
from PyQt4.QtCore import QCoreApplication


def create_constant_function(constant):
    return lambda:constant


def variant_to_pyobject(qvariant=None):
    """Try to convert a QVariant to a python object as good
    as possible"""
    import datetime
    if not qvariant:
        return None
    if qvariant.isNull():
        return None
    type = qvariant.type()
    if type == QtCore.QVariant.String:
        value = unicode(qvariant.toString())
    elif type == QtCore.QVariant.Date:
        value = qvariant.toDate()
        value = datetime.date(year=value.year(),
                              month=value.month(),
                              day=value.day())
    elif type == QtCore.QVariant.Int:
        value = int(qvariant.toInt()[0])
    elif type == QtCore.QVariant.LongLong:
        value = int(qvariant.toLongLong()[0])      
    elif type == QtCore.QVariant.Double:
        value = float(qvariant.toDouble()[0])
    elif type == QtCore.QVariant.Bool:
        value = bool(qvariant.toBool())
    elif type == QtCore.QVariant.Time:
        value = qvariant.toTime()
        value = datetime.time(hour = value.hour(),
                              minute = value.minute(),
                              second = value.second())
    elif type == QtCore.QVariant.DateTime:
        value = qvariant.toDateTime()
        value = value.toPyDateTime ()
    else:
        value = qvariant.toPyObject()
      
    return value

#
# Global dictionary containing all user defined translations in the
# current locale
#  
_translations_ = {}

def load_translations():
    """Fill the global dictionary of translations with all data from the
    database, to be able to do fast gui thread lookups of translations"""
    language = unicode(QtCore.QLocale().name())
    from camelot.model.i18n import Translation
    tls = Translation.query.filter(Translation.language==language)
    tls = tls.filter(Translation.value!=None).all()
    for t in tls:
        if t.value:
            _translations_[t.source] = t.value
  
def ugettext(string_to_translate):
    """Translate the string_to_translate to the language of the current locale.
    This is a two step process.  First the function will try to get the
    translation out of the Translation entity, if this is not successfull, the
    function will ask QCoreApplication to translate string_to_translate 
    (which tries to get the translation from the .po files)"""
    result = _translations_.get(string_to_translate, None)
    if not result:
        result = unicode(QCoreApplication.translate('', string_to_translate))
    return result
  
class ugettext_lazy(object):
  
    def __init__(self, string_to_translate):
        self._string_to_translate = string_to_translate
      
    def __str__(self):
        return ugettext(self._string_to_translate)
    
    def __unicode__(self):
        return ugettext(self._string_to_translate)
