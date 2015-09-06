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

from ....core.item_model import PreviewRole
from ....core.qt import variant_to_py, Qt, QtCore, py_to_variant
from .customdelegate import CustomDelegate, DocumentationMetaclass
from camelot.view.controls import editors
from camelot.core.constants import camelot_small_icon_width
from camelot.view.utils import local_date_format

class DateDelegate( six.with_metaclass( DocumentationMetaclass,
                                        CustomDelegate ) ):
    """Custom delegate for date values"""
    
    editor = editors.DateEditor
    
    def __init__(self, parent=None, **kwargs):
        CustomDelegate.__init__(self, parent, **kwargs)
        self.date_format = local_date_format()
        self._width = self._font_metrics.averageCharWidth() * (len(self.date_format) + 2)  + (camelot_small_icon_width*2)

    @classmethod
    def get_standard_item(cls, locale, value, fa_values):
        item = super(DateDelegate, cls).get_standard_item(locale, value, fa_values)
        if value is not None:
            value_str = six.text_type(locale.toString(value, QtCore.QLocale.ShortFormat))
            item.setData(py_to_variant(value_str), PreviewRole)
        else:
            item.setData('', PreviewRole)
        return item

    def paint(self, painter, option, index):
        painter.save()
        self.drawBackground(painter, option, index)
        value = variant_to_py(index.data(PreviewRole))
        self.paint_text(painter, option, index, value, horizontal_align=Qt.AlignRight )
        painter.restore()



