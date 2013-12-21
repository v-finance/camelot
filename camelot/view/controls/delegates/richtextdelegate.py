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

from ....core.qt import Qt, variant_to_py

import six

from .customdelegate import CustomDelegate, DocumentationMetaclass
from .. import editors
from ...utils import text_from_richtext
from ...proxy import ValueLoading

class RichTextDelegate( six.with_metaclass( DocumentationMetaclass,
                                            CustomDelegate ) ):
    """Custom delegate for rich text (HTML) string values
  """
    
    editor = editors.RichTextEditor
    
    def __init__(self, parent=None, editable=True, **kwargs):
        CustomDelegate.__init__(self, parent, editable)
        self.editable = editable
        self._height = self._height * 10
        self._width = self._width * 3
    
    def paint(self, painter, option, index):
        painter.save()
        self.drawBackground(painter, option, index)
        value = six.text_type(variant_to_py(index.model().data(index, Qt.EditRole)))

        value_str = u''
        if value not in (None, ValueLoading):
            value_str = ' '.join(text_from_richtext(value))[:256]

        self.paint_text(painter, option, index, value_str)
        painter.restore()
    




