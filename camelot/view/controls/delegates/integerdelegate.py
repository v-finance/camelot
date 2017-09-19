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

import six

from ....core.qt import py_to_variant, Qt
from ....core.item_model import PreviewRole
from .customdelegate import CustomDelegate, DocumentationMetaclass
from camelot.view.controls import editors

if six.PY3:
    long_int = int
else:
    long_int = six.integer_types[-1]

@six.add_metaclass(DocumentationMetaclass)
class IntegerDelegate(CustomDelegate):
    """Custom delegate for integer values"""
    
    editor = editors.IntegerEditor
    horizontal_align = Qt.AlignRight | Qt.AlignVCenter

    @classmethod
    def get_standard_item(cls, locale, value, fa_values):
        item = super(IntegerDelegate, cls).get_standard_item(locale, value, fa_values)
        if value is not None:
            value_str = locale.toString(long_int(value))
            if fa_values.get('suffix') is not None:
                value_str = value_str + ' ' + fa_values.get('suffix')
            if fa_values.get('prefix') is not None:
                value_str = fa_values.get('prefix') + ' ' + value_str
            item.setData(py_to_variant(value_str), PreviewRole)
        return item




