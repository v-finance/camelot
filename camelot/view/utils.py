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
"""Helper functions for the view subpackage"""

from six.moves import html_parser

import six

from datetime import datetime, time, date
import decimal
import re
import string
import logging
import operator

from ..core.qt import QtCore, QtWidgets
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
_locale = None

def locale():
    """Get the default locale and cache it for reuse"""
    global _locale
    if _locale is None:
        _locale = QtCore.QLocale()
    return _locale

def local_date_format():
    """Get the local data format and cache it for reuse"""
    global _local_date_format
    if not _local_date_format:
        locale = QtCore.QLocale()
        format_sequence = re.split('y*', six.text_type(locale.dateFormat(locale.ShortFormat)))
        # make sure a year always has 4 numbers
        format_sequence.insert(-1, 'yyyy')
        _local_date_format = six.text_type(u''.join(format_sequence))
    return _local_date_format

def local_datetime_format():
    """Get the local datatime format and cache it for reuse"""
    global _local_datetime_format
    if not _local_datetime_format:
        locale = QtCore.QLocale()
        format_sequence = re.split('y*', six.text_type(locale.dateTimeFormat(locale.ShortFormat)))
        # make sure a year always has 4 numbers
        format_sequence.insert(-1, 'yyyy')
        _local_datetime_format = six.text_type(u''.join(format_sequence))
    return _local_datetime_format

def local_time_format():
    """Get the local time format and cache it for reuse"""
    global _local_time_format
    if not _local_time_format:
        locale = QtCore.QLocale()
        _local_time_format = six.text_type(locale.timeFormat(locale.ShortFormat) )
    return _local_time_format

def default_language(*args):
    """takes arguments, to be able to use this function as a
    default field attribute"""
    locale = QtCore.QLocale()
    return six.text_type(locale.name())

class ParsingError(Exception): pass

def string_from_string(s):
    if not s:
        return None
    return six.text_type(s)

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
    f = local_date_format()
    dt = QtCore.QDate.fromString(s, f)
    if not dt.isValid():
        #
        # if there is a mismatch of 1 in length between format and
        # string, prepend a 0, to handle the case of 1/11/2011
        #
        if len(f) == len(s) + 1:
            s = '0' + s
            dt = QtCore.QDate.fromString(s, f)
    if not dt.isValid():
        #
        # try alternative separators
        #
        separators = u''.join([c for c in f if c not in string.ascii_letters])
        if separators:
            alternative_string = u''.join([(c if c in string.digits else separators[0]) for c in s])
            dt = QtCore.QDate.fromString(alternative_string, f)
    if not dt.isValid():
        # try parsing without separators
        # attention : using non ascii letters will fail on windows
        # string.letters then contains non ascii letters of which we don't know the
        # encoding, so we cannot convert them to unicode to compare them
        only_letters_format = u''.join([c for c in f if c in string.ascii_letters])
        only_letters_string = u''.join([c for c in s if c in (string.ascii_letters+string.digits)])
        dt = QtCore.QDate.fromString(only_letters_string, only_letters_format)
        if not dt.isValid():
            # try parsing without the year, and take the current year by default
            only_letters_format = u''.join([c for c in only_letters_format if c not in ['y']])
            dt = QtCore.QDate.fromString(only_letters_string, only_letters_format)
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
    f = local_time_format()
    tm = QtCore.QTime.fromString(s, f)
    if not tm.isValid():
        raise ParsingError()
    return time( tm.hour(), tm.minute(), tm.second() )

def datetime_from_string(s):
    s = s.strip()
    if not s:
        return None
    f = local_datetime_format()
    dt = QtCore.QDateTime.fromString(s, f)
    if not dt.isValid():
        raise ParsingError()
    return datetime(dt.date().year(), dt.date().month(), dt.date().day(), 
                    dt.time().hour(), dt.time().minute(), dt.time().second())

def code_from_string(s, separator):
    return s.split(separator)

def int_from_string(s):
    value = float_from_string(s)
    if value != None:
        value = int( value )
    return value

def float_from_string(s):
    if s == None:
        return None
    s = s.strip()
    if len(s) == 0:
        return None
    locale = QtCore.QLocale()
    # floats in python are implemented as double in C
    f, ok = locale.toDouble(s)
    if not ok:
        raise ParsingError()
    return f

def decimal_from_string(s):
    # direct conversion not possible, due to locale
    return decimal.Decimal( float_from_string( s ) )

def pyvalue_from_string(pytype, s):
    if pytype is str:
        return str(s)
    elif pytype is six.text_type:
        return six.text_type(s)
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
    return six.text_type( value )

def enumeration_to_string(value):
    return ugettext(six.text_type(value or u'').replace('_', ' ').capitalize())

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

    class HtmlToTextParser(html_parser.HTMLParser):
        
        def handle_endtag(self, tag):
            if tag == 'br':
                strings.append('')

        def handle_data(self, data):
            from xml.sax.saxutils import escape
            data = data.strip()
            if data:
                strings.append(escape(data))

    parser = HtmlToTextParser()
    try:
        parser.feed(unstripped_text.strip())
    except html_parser.HTMLParseError:
        logger.warn('html parse error')

    return strings

def resize_widget_to_screen( widget, fraction = 0.75 ):
    """Resize a widget to fill a certain fraction of the screen

    :param widget: the widget to resize
    :param fraction: the fraction of the screen to fill after the resize
    """
    desktop = QtWidgets.QApplication.desktop()
    available_geometry = desktop.availableGeometry( widget )
    # use the size of the screen instead to set the dialog size
    widget.resize( available_geometry.width() * 0.75, 
                   available_geometry.height() * 0.75 )    