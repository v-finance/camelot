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

"""Helper functions for the view subpackage"""

from PyQt4 import QtCore

from datetime import datetime, time, date
import re
import logging
import operator

from camelot.core import constants
from camelot.core.sql import like_op
from sqlalchemy.sql.operators import between_op
from camelot.core.utils import ugettext

logger = logging.getLogger('camelot.view.utils')

_local_date_format = None
 
def local_date_format():
    """Get the local data format and cache it for reuse"""
    global _local_date_format
    if not _local_date_format:
        locale = QtCore.QLocale()
        format_sequence = re.split('y*', unicode(locale.dateFormat(locale.ShortFormat)))
        # make sure a year always has 4 numbers
        format_sequence.insert(-1, 'yyyy')
        _local_date_format = unicode(u''.join(format_sequence))
    return _local_date_format

class ParsingError(Exception): pass

def string_from_string(s):
    if not s:
        return None
    return unicode(s)

def bool_from_string(s):
    if s is None: raise ParsingError()
    if s.lower() not in ['false', 'true']: raise ParsingError()
    return eval(s.lower().capitalize())

def date_from_string(s):
    if not s:
        return None
    from PyQt4.QtCore import QDate
    import string
    s = s.strip()
    f = local_date_format()
    if not s:
        return None
    dt = QDate.fromString(s, f)
    if not dt.isValid():
        # try parsing without separators
        # attention : using non ascii letters will fail on windows
        # string.letters then contains non ascii letters of which we don't know the
        # encoding, so we cannot convert them to unicode to compare them
        only_letters_format = u''.join([c for c in f if c in string.ascii_letters])
        only_letters_string = u''.join([c for c in s if c in (string.ascii_letters+string.digits)])
        dt = QDate.fromString(only_letters_string, only_letters_format)
        if not dt.isValid():
            # try parsing without the year, and take the current year by default
            only_letters_format = u''.join([c for c in only_letters_format if c not in ['y']])
            dt = QDate.fromString(only_letters_string, only_letters_format)
            if not dt.isValid():
                raise ParsingError()
#                # try parsing without year and month, and take the current year and month by default
#                only_letters_format = u''.join([c for c in only_letters_format if c not in ['M']])
#                dt = QDate.fromString(only_letters_string, only_letters_format)
#                if not dt.isValid():   
#                    raise ParsingError()
#                else:
#                    today = date.today()
#                    return date(today.year, today.month, dt.day())
            else:
                return date(date.today().year, dt.month(), dt.day())
    return date(dt.year(), dt.month(), dt.day())

def time_from_string(s, format=constants.strftime_time_format):
    if s is None: raise ParsingError()
    s = s.strip()
    try:
        dt = datetime.strptime(s, format)
    except ValueError:
        raise ParsingError()
    return dt.time()


def datetime_from_string(s, format=constants.strftime_datetime_format):
    if s is None: raise ParsingError()
    s = s.strip()

    try:
        dt = datetime.strptime(s, format)
    except ValueError:
        raise ParsingError()
    return dt


def int_from_string(s):
    if s is None: raise ParsingError()
    if s.isspace(): return int()

    s = s.strip()
    if len(s) == 0: return int()

    try:
        i = int(s)
    except ValueError:
        raise ParsingError()
    return i


def float_from_string(s):
    if not s:
        return None
    locale = QtCore.QLocale()
    f, ok = locale.toFloat(s)
    if not ok:
        raise ParsingError()
    return f


def pyvalue_from_string(pytype, s):
    if pytype is str:
        return str(s)
    elif pytype is unicode:
        return unicode(s)
    elif pytype is bool:
        return bool_from_string(s)
    elif pytype is date:
        return date_from_string(s)
    elif pytype is time:
        return date_from_string(s)
    elif pytype is datetime:
        return datetime_from_string(s)
    elif pytype is float:
        return float_from_string(s)
    elif pytype is int:
        return int_from_string(s)

def enumeration_to_string(value):
    return ugettext(unicode(value or u'').replace('_', ' ').capitalize())

operator_names = {
    operator.eq : u'=',
    operator.ne : u'!=',
    operator.lt : u'<',
    operator.le : u'<=',
    operator.gt : u'>',
    operator.ge : u'>=',
    like_op : u'like',
    between_op: u'between',
}

def text_from_richtext(unstripped_text, newlines=True, word_xml=False):
    # TODO improve/expand
    from HTMLParser import HTMLParser    
    strings = []
    if not unstripped_text:
	    return ''
    class HtmlToTextParser(HTMLParser):
        def handle_data(self, data):
            data = data.strip()
            if data:
                newline = ' '
                if newlines:
                    newline = "\n"
                    if word_xml:
                        newline = '<w:br />'
                strings.append('%s%s' % (data, newline))

    parser = HtmlToTextParser()
    parser.feed(unstripped_text.strip())
    
    return ''.join(strings)
