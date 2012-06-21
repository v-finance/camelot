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
"""Helper functions for the view subpackage"""
from HTMLParser import HTMLParser

from PyQt4 import QtCore

from datetime import datetime, time, date
import re
import logging
import operator

from camelot.core.sql import like_op
from sqlalchemy.sql.operators import between_op
from camelot.core.utils import ugettext
from camelot.core.utils import ugettext_lazy as _

logger = logging.getLogger('camelot.view.utils')

#
# Cached date and time formats, for internal use only
#
_local_date_format = None
_local_datetime_format = None
_local_time_format = None

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

def local_datetime_format():
    """Get the local datatime format and cache it for reuse"""
    global _local_datetime_format
    if not _local_datetime_format:
        locale = QtCore.QLocale()
        format_sequence = re.split('y*', unicode(locale.dateTimeFormat(locale.ShortFormat)))
        # make sure a year always has 4 numbers
        format_sequence.insert(-1, 'yyyy')
        _local_datetime_format = unicode(u''.join(format_sequence))
    return _local_datetime_format

def local_time_format():
    """Get the local time format and cache it for reuse"""
    global _local_time_format
    if not _local_time_format:
        locale = QtCore.QLocale()
        _local_time_format = unicode(locale.timeFormat(locale.ShortFormat) )
    return _local_time_format

def default_language(*args):
    """takes arguments, to be able to use this function as a
    default field attribute"""
    locale = QtCore.QLocale()
    return unicode(locale.name())

class ParsingError(Exception): pass

def string_from_string(s):
    if not s:
        return None
    return unicode(s)

def bool_from_string(s):
    if s is None: raise ParsingError()
    if s.lower() not in ['false', 'true']: raise ParsingError()
    return eval(s.lower().capitalize())

def _insert_string(original, new, pos):
    '''Inserts new inside original at pos.'''
    return original[:pos] + new + original[pos:]

def date_from_string(s):
    s = s.strip()
    if not s:
        return None
    from PyQt4.QtCore import QDate
    import string
    f = local_date_format()
    dt = QDate.fromString(s, f)
    if not dt.isValid():
        #
        # if there is a mismatch of 1 in length between format and
        # string, prepend a 0, to handle the case of 1/11/2011
        #
        if len(f) == len(s) + 1:
            s = '0' + s
            dt = QDate.fromString(s, f)
    if not dt.isValid():
        #
	# try alternative separators
        #
        separators = u''.join([c for c in f if c not in string.ascii_letters])
        if separators:
            alternative_string = u''.join([(c if c in string.digits else separators[0]) for c in s])
            dt = QDate.fromString(alternative_string, f)
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

def time_from_string(s):
    s = s.strip()
    if not s:
        return None
    from PyQt4.QtCore import QTime
    f = local_time_format()
    tm = QTime.fromString(s, f)
    if not tm.isValid():
        raise ParsingError()
    return time( tm.hour(), tm.minute(), tm.second() )

def datetime_from_string(s):
    s = s.strip()
    if not s:
        return None
    from PyQt4.QtCore import QDateTime
    f = local_datetime_format()
    dt = QDateTime.fromString(s, f)
    if not dt.isValid():
        raise ParsingError()
    return datetime(dt.date().year(), dt.date().month(), dt.date().day(), 
                    dt.time().hour(), dt.time().minute(), dt.time().second())

def code_from_string(s, separator):
    return s.split(separator)

def int_from_string(s):
    if s is None: raise ParsingError()
    if s.isspace(): return int()

    s = s.strip()
    if len(s) == 0: return int()

    try:
	# Convert to float first, to be able to convert a string like '1.0'
	# to 1
        i = int( float( s ) )
    except ValueError:
        raise ParsingError()
    return i

def float_from_string(s):
    if not s:
        return None
    locale = QtCore.QLocale()
    # floats in python are implemented as double in C
    f, ok = locale.toDouble(s)
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

def to_string( value ):
    if value == None:
	return u''
    return unicode( value )

def enumeration_to_string(value):
    return ugettext(unicode(value or u'').replace('_', ' ').capitalize())

operator_names = {
    operator.eq : _( u'=' ),
    operator.ne : _( u'!=' ),
    operator.lt : _( u'<' ),
    operator.le : _( u'<=' ),
    operator.gt : _( u'>' ),
    operator.ge : _( u'>=' ),
    like_op : _( u'like' ),
    between_op: _( u'between' ),
}

def text_from_richtext( unstripped_text ):
    """function that returns a list of lines with escaped data, to be used in 
    templates for example
    :arg unstripped_text: string
    :return: list of strings
    """
    strings = ['']
    if not unstripped_text:
	    return strings

    class HtmlToTextParser(HTMLParser):
        def handle_endtag(self, tag):
            if tag == 'br':
                strings.append('')

        def handle_data(self, data):
            from xml.sax.saxutils import escape
            data = data.strip()
            if data:
                strings.append(escape(data))

    parser = HtmlToTextParser()
    parser.feed(unstripped_text.strip())

    return strings
