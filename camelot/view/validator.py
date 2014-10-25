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

""":class:`QtGui.QValidator` subclasses to be used in the
editors or other widgets.
"""

import six

from camelot.core.qt import QtGui, variant_api

from .utils import date_from_string, ParsingError

class DateValidator(QtGui.QValidator):

    def validate(self, input_, pos):
        try:
            date_from_string(six.text_type(input_))
        except ParsingError:
            if variant_api == 1:
                return (QtGui.QValidator.Intermediate, pos)
            else:
                return (QtGui.QValidator.Intermediate, input_, pos)
        if variant_api == 1:
            return (QtGui.QValidator.Acceptable, pos)
        else:
            return (QtGui.QValidator.Acceptable, input_, pos)