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
logger = logging.getLogger('camelot.view.controls.delegates.comboboxdelegate')

from .customdelegate import CustomDelegate, DocumentationMetaclass

import six

from ....core.item_model import PreviewRole
from ....core.qt import Qt, variant_to_py, py_to_variant
from camelot.view.controls import editors

@six.add_metaclass(DocumentationMetaclass)
class ComboBoxDelegate(CustomDelegate):
    
    editor = editors.ChoicesEditor

    @classmethod
    def get_standard_item(cls, locale, value, fa_values):
        item = super(ComboBoxDelegate, cls).get_standard_item(locale, value, fa_values)
        choices = fa_values.get('choices', [])
        for key, verbose in choices:
            if key == value:
                item.setData(py_to_variant(six.text_type(verbose)), PreviewRole)
                break
        else:
            if value is None:
                item.setData(py_to_variant(six.text_type()), PreviewRole)
            else:
                # the model has a value that is not in the list of choices,
                # still try to display it
                item.setData(py_to_variant(six.text_type(value)), PreviewRole)
        return item

    def setEditorData(self, editor, index):
        value = variant_to_py(index.data(Qt.EditRole))
        field_attributes = variant_to_py(index.data(Qt.UserRole))
        editor.set_field_attributes(**(field_attributes or {}))
        editor.set_value(value)


