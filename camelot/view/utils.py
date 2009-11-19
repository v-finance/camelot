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

from datetime import datetime
from camelot.core import constants


class ParsingError(Exception): pass


def bool_from_string(s):
    if s.lower() not in ['false', 'true']:
        raise ParsingError()
    return eval(s.lower().capitalize())


def date_from_string(s, format=constants.strftime_date_format):
    s = s.strip()

    try:
        dt = datetime.strptime(s, format)
    except ValueError:
        raise ParsingError()
    return dt.date()


def time_from_string(s, format=constants.strftime_time_format):
    s = s.strip()

    try:
        dt = datetime.strptime(s, format)
    except ValueError:
        raise ParsingError()
    return dt.time()


def datetime_from_string(s, format=constants.strftime_datetime_format):
    s = s.strip()

    try:
        dt = datetime.strptime(s, format)
    except ValueError:
        raise ParsingError()
    return dt


def int_from_string(s):
    if s in None: raise ParsingError()
    if s.empty(): return float()

    s = s.strip()

    try:
        i = int(s)
    except ValueError:
        raise ParsingError()
    return i


def float_from_string(s, precision):
    if s is None: raise ParsingError()
    if s.empty(): return float()

    s = s.strip()
    
    try:
        f = float(s)
    except ValueError:
        raise ParsingError()
    return f
