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

import logging
logger = logging.getLogger('camelot.view.controls.delegates.plaintextdelegate')

import six

from ....core.item_model import PreviewRole
from ....core.qt import py_to_variant
from .customdelegate import CustomDelegate
from .customdelegate import DocumentationMetaclass

from camelot.view.controls import editors

DEFAULT_COLUMN_WIDTH = 20

@six.add_metaclass(DocumentationMetaclass)
class PlainTextDelegate(CustomDelegate):
    """Custom delegate for simple string values"""

    editor = editors.TextLineEditor

    def __init__( self, 
                  parent = None, 
                  length = DEFAULT_COLUMN_WIDTH,
                  translate_content=False, 
                  **kw ):
        CustomDelegate.__init__( self, parent, length = length, **kw )
        self._translate_content = translate_content
        char_width = self._font_metrics.averageCharWidth()
        self._width = char_width * min( DEFAULT_COLUMN_WIDTH, length or DEFAULT_COLUMN_WIDTH )

    @classmethod
    def get_standard_item(cls, locale, value, fa_values):
        item = super(PlainTextDelegate, cls).get_standard_item(locale, value, fa_values)
        if value is not None:
            item.setData(py_to_variant(six.text_type(value)), PreviewRole)
        return item


