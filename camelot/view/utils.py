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
"""Helper functions for the view subpackage"""

import html.parser as html_parser


from datetime import datetime, time, date
import decimal
import re
import logging

from ..core.backend import get_root_backend
from ..core.qt import QtCore
from camelot.core.utils import ugettext

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
        format_sequence = re.split('y*', str(locale.dateFormat(locale.FormatType.ShortFormat)))
        # make sure a year always has 4 numbers
        format_sequence.insert(-1, 'yyyy')
        _local_date_format = str(u''.join(format_sequence))
    return _local_date_format

def local_datetime_format():
    """Get the local datatime format and cache it for reuse"""
    global _local_datetime_format
    if not _local_datetime_format:
        locale = QtCore.QLocale()
        # make sure a year always has 4 numbers
        _local_datetime_format = re.sub('y+', 'yyyy', str(locale.dateTimeFormat(locale.FormatType.ShortFormat)))
    return _local_datetime_format

def local_time_format():
    """Get the local time format and cache it for reuse"""
    global _local_time_format
    if not _local_time_format:
        locale = QtCore.QLocale()
        _local_time_format = str(locale.timeFormat(locale.FormatType.ShortFormat) )
    return _local_time_format

def default_language(*args):
    """takes arguments, to be able to use this function as a
    default field attribute"""
    locale = QtCore.QLocale()
    return str(locale.name())

class ParsingError(Exception): pass

def string_from_string(s):
    if not s:
        return None
    return str(s)

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
    qdt = get_root_backend().date_from_string(s)
    if not qdt.isValid():
        raise ParsingError()
    return date(qdt.year(), qdt.month(), qdt.day())

def time_from_string(s):
    s = s.strip()
    if not s:
        return None
    f = local_time_format()
    tm = locale().toTime(s, f)
    if not tm.isValid():
        raise ParsingError()
    return time( tm.hour(), tm.minute(), tm.second() )

def datetime_from_string(s):
    s = s.strip()
    if not s:
        return None
    f = local_datetime_format()
    dt = locale().toDateTime(s, f)
    if not dt.isValid():
        raise ParsingError()
    return datetime(dt.date().year(), dt.date().month(), dt.date().day(), 
                    dt.time().hour(), dt.time().minute(), dt.time().second())

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
    elif pytype is str:
        return str(s)
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
    return str( value )

def enumeration_to_string(value):
    return ugettext(str(value or u'').replace('_', ' ').capitalize())

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
    #TODO parser error only thrown when using strict mode https://stackoverflow.com/a/59968964

    # try:
    #     parser.feed(unstripped_text.strip())
    # except html_parser.HTMLParseError: # HTMLParseError doesn't exist anymore
    #     logger.debug('html parse error')
    parser.feed(unstripped_text.strip())

    return strings

def richtext_to_string(value):
    if value is None:
        return u''
    return u'\n'.join([line for line in text_from_richtext(value)])

def resize_widget_to_screen( widget_or_window, fraction = 0.75 ):
    """Resize a widget to fill a certain fraction of the screen

    :param widget: the widget to resize
    :param fraction: the fraction of the screen to fill after the resize
    """
    screen = widget_or_window.screen()
    available_geometry = screen.availableGeometry()
    # use the size of the screen instead to set the dialog size
    widget_or_window.resize(
        available_geometry.width() * fraction, 
        available_geometry.height() * fraction
    )

def get_settings_group(admin_route):
    assert len(admin_route) >= 2
    return [admin_route[-2][:255]]

def get_settings(group):
    """A :class:`QtCore.QSettings` object in which Camelot related settings
    can be stored.  This object is intended for Camelot internal use.  If an
    application specific settings object is needed, simply construct one.

    :return: a :class:`QtCore.QSettings` object
    """
    settings = QtCore.QSettings()
    settings.beginGroup('Camelot')
    settings.beginGroup(group[:255])
    return settings
