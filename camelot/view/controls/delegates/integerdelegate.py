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

import six

from ....core.qt import py_to_variant
from ....core.item_model import PreviewRole
from .customdelegate import CustomDelegate, DocumentationMetaclass
from camelot.view.controls import editors

if six.PY3:
    long_int = int
else:
    long_int = six.integer_types[-1]

class IntegerDelegate( six.with_metaclass( DocumentationMetaclass,
                                           CustomDelegate ) ):
    """Custom delegate for integer values"""
    
    editor = editors.IntegerEditor

    @classmethod
    def get_standard_item(cls, locale, value, fa_values):
        item = super(IntegerDelegate, cls).get_standard_item(locale, value, fa_values)
        if value is not None:
            value_str = locale.toString(long_int(value))
            item.setData(py_to_variant(value_str), PreviewRole)
        return item


