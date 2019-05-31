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

"""Default field attributes for various sqlalchemy column types"""

import itertools

import six

import sqlalchemy.types

import camelot.types
from camelot.core.sql import like_op
from sqlalchemy.sql.operators import between_op
import datetime
import operator

from .controls import delegates
from camelot.core import constants
from camelot.view.utils import (
    bool_from_string,
    date_from_string,
    time_from_string,
    datetime_from_string,
    int_from_string,
    float_from_string,
    string_from_string,
    enumeration_to_string,
    default_language,
    richtext_to_string,
)

_numerical_operators = (operator.eq, operator.ne, operator.lt, operator.le, operator.gt, operator.ge, between_op)
_text_operators = (operator.eq, operator.ne, like_op)

#
# operators assuming an order in the values they operate on.  these operators don't
# work on None values
#
order_operators = (operator.lt, operator.le, operator.gt, operator.ge, between_op, like_op)

_sqlalchemy_to_python_type_ = {

    sqlalchemy.types.Boolean: lambda f: {
        'python_type': bool,
        'editable': True,
        'nullable': True,
        'delegate': delegates.BoolDelegate,
        'from_string': bool_from_string,
        'operators' : (operator.eq,),
    },

    sqlalchemy.types.Date: lambda f: {
        'python_type': datetime.date,
        'format': constants.camelot_date_format,
        'editable': True,
        'min': None,
        'max': None,
        'nullable': True,
        'delegate': delegates.DateDelegate,
        'from_string': date_from_string,
        'operators' : _numerical_operators,
    },

    sqlalchemy.types.Time : lambda f: {
        'python_type': datetime.time,
        'editable': True,
        'nullable': True,
        'widget': 'time',
        'delegate': delegates.TimeDelegate,
        'format': constants.camelot_time_format,
        'nullable': True,
        'from_string': time_from_string,
        'operators': _numerical_operators,
    },

    sqlalchemy.types.DateTime : lambda f: {
        'python_type': datetime.datetime,
        'editable': True,
        'nullable': True,
        'widget': 'time',
        'format': constants.camelot_datetime_format,
        'nullable': True,
        'delegate': delegates.DateTimeDelegate,
        'from_string': datetime_from_string,
        'operators': _numerical_operators,
    },

    sqlalchemy.types.Float: lambda f: {
        'python_type': float,
        'precision': (f.precision if not isinstance(f.precision, tuple) else f.precision[1]) or 2,
        'editable': True,
        'minimum': constants.camelot_minfloat,
        'maximum': constants.camelot_maxfloat,
        'nullable': True,
        'delegate': delegates.FloatDelegate,
        'from_string': float_from_string,
        'operators': _numerical_operators,
    },

    sqlalchemy.types.Numeric: lambda f: {
        'python_type': float,
        'precision': f.scale,
        'editable': True,
        'minimum': constants.camelot_minfloat,
        'maximum': constants.camelot_maxfloat,
        'nullable': True,
        'delegate': delegates.FloatDelegate,
        'from_string': float_from_string,
        'operators': _numerical_operators,
        'decimal':True,
    },

    sqlalchemy.types.Integer: lambda f: {
        'python_type': int,
        'editable': True,
        'minimum': constants.camelot_minint,
        'maximum': constants.camelot_maxint,
        'nullable': True,
        'delegate': delegates.IntegerDelegate,
        'from_string': int_from_string,
        'to_string': six.text_type,
        'widget': 'int',
        'operators': _numerical_operators,
    },

    sqlalchemy.types.String: lambda f: {
        'python_type': str,
        'length': f.length,
        'delegate': delegates.PlainTextDelegate,
        'editable': True,
        'nullable': True,
        'widget': 'str',
        'from_string': string_from_string,
        'operators' : _text_operators,
    },

    camelot.types.VirtualAddress: lambda f: {
        'python_type': str,
        'editable': True,
        'nullable': True,
        'delegate': delegates.VirtualAddressDelegate,
        'operators' : _text_operators,
        'from_string' : lambda str:None,
    },

    camelot.types.RichText: lambda f: {
        'python_type': str,
        'editable': True,
        'nullable': True,
        'delegate': delegates.RichTextDelegate,
        'from_string': string_from_string,
        'operators' : [],
        'to_string': richtext_to_string,
    },

    camelot.types.Color: lambda f: {
        'delegate': delegates.ColorDelegate,
        'python_type': str,
        'editable': True,
        'nullable': True,
        'widget': 'color',
        'operators' : _text_operators,
    },

    camelot.types.Enumeration: lambda f: {
        'delegate': delegates.ComboBoxDelegate,
        'python_type': str,
        'choices': [(v, enumeration_to_string(v)) for v in f.choices],
        'from_string': lambda s:dict((enumeration_to_string(v), v) for v in f.choices)[s],
        'minimal_column_width':max(itertools.chain((0,), (len(enumeration_to_string(v)) for v in f.choices))),
        'editable': True,
        'nullable': True,
        'widget': 'combobox',
        'operators' : _numerical_operators,
    },

    camelot.types.Language: lambda f: {
        'delegate': delegates.LanguageDelegate,
        'python_type': str,
        'default': default_language,
        'from_string': string_from_string,
        'editable': True,
        'nullable': False,
        'widget': 'combobox',
    },

    camelot.types.File : lambda f: {
        'python_type': str,
        'editable': True,
        'delegate': delegates.FileDelegate,
        'storage': f.storage,
        'operators' : _text_operators,
        'remove_original': False,
    },
}

#
# Generate a restructured text table out of the previous data structure
#

class DummyField(object):
    def __init__(self):
        self.length = 20
        self.parts = ['AAA', '99']
        self.choices = ['planned', 'canceled']
        self.precision = 2
        self.scale = 2
        self.storage = None
        self.separator = u'.'

row_separator = '+' + '-'*50 + '+' + '-'*100 + '+' + '-'*70 + '+'
row_format = """| %-48s | %-98s | %-68s |"""

doc = """Field types handled through introspection :

""" + row_separator + """
""" + row_format%('**Field type**', '**Default delegate**', '**Default editor**') + """
""" + row_separator + """
"""

field_types = sorted( six.iterkeys(_sqlalchemy_to_python_type_),
                      key = lambda ft:ft.__name__ )

for field_type in field_types:
    field_attributes = _sqlalchemy_to_python_type_[field_type](DummyField())
    delegate = field_attributes['delegate']
    row = row_format%( ':class:`' + field_type.__module__ + '.' + field_type.__name__ + '`',
                       ':class:`' + delegate.__module__ + '.' + delegate.__name__ + '`',
                       '.. image:: /_static/editors/%s_editable.png'%(delegate.editor.__name__))
    doc += row + """
""" + row_separator + """
"""

doc += """
"""

__doc__ = doc





