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

from ....core.item_model import PreviewRole
from ....core.qt import py_to_variant

import six

from .customdelegate import CustomDelegate, DocumentationMetaclass
from .. import editors
from ...utils import text_from_richtext

@six.add_metaclass(DocumentationMetaclass)
class RichTextDelegate(CustomDelegate):
    """Custom delegate for rich text (HTML) string values
  """
    
    editor = editors.RichTextEditor
    
    def __init__(self, parent=None, editable=True, **kwargs):
        CustomDelegate.__init__(self, parent, editable)
        self.editable = editable
        self._height = self._height * 10
        self._width = self._width * 3

    @classmethod
    def get_standard_item(cls, locale, value, fa_values):
        item = super(RichTextDelegate, cls).get_standard_item(locale, value, fa_values)
        if value is not None:
            value_str = u' '.join(text_from_richtext(value))[:256]
            item.setData(py_to_variant(six.text_type(value_str)), PreviewRole)
        return item
