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
from ....core.qt import py_to_variant, Qt
from .customdelegate import CustomDelegate, DocumentationMetaclass
from camelot.view.controls import editors
from camelot.core import constants

@six.add_metaclass(DocumentationMetaclass)
class FloatDelegate(CustomDelegate):
    """Custom delegate for float values"""

    editor = editors.FloatEditor
    horizontal_align = Qt.AlignRight

    def __init__( self,
                 minimum=constants.camelot_minfloat,
                 maximum=constants.camelot_maxfloat,
                 parent=None,
                 **kwargs ):
        super(FloatDelegate, self).__init__(parent=parent,
                                            minimum=minimum, maximum=maximum,
                                            **kwargs )
        self.minimum = minimum
        self.maximum = maximum

    @classmethod
    def get_standard_item(cls, locale, value, fa_values):
        item = super(FloatDelegate, cls).get_standard_item(locale, value, fa_values)
        precision = fa_values.get('precision', 2)
        if value is not None:
            value_str = six.text_type(
                locale.toString(float(value), 'f', precision)
            )
            item.setData(py_to_variant(value_str), PreviewRole)
        else:
            item.setData(py_to_variant(six.text_type()), PreviewRole)
        return item


