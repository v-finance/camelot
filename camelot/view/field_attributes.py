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
from decimal import Decimal


import sqlalchemy.types

import camelot.types
import datetime

from .controls import delegates
from ..admin.action import list_filter, field_action
from camelot.core import constants
from camelot.types.typing import Color, Note, Directory, File, Months
from camelot.view.utils import (
    bool_from_string,
    date_from_string,
    datetime_from_string,
    int_from_string,
    float_from_string,
    string_from_string,
    enumeration_to_string,
    default_language,
    richtext_to_string,
)
_sqlalchemy_to_python_type_ = {

    sqlalchemy.types.Boolean: lambda f: {
        'python_type': bool,
        'editable': True,
        'nullable': True,
        'delegate': delegates.BoolDelegate,
        'from_string': bool_from_string,
        'search_strategy': list_filter.BoolFilter,
        'filter_strategy': list_filter.BoolFilter,
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
        'search_strategy': list_filter.DateFilter,
        'filter_strategy': list_filter.DateFilter,
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
        'search_strategy': list_filter.DateFilter,
        'filter_strategy': list_filter.DateFilter,
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
        'search_strategy': list_filter.DecimalFilter,
        'filter_strategy': list_filter.DecimalFilter,
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
        'decimal':True,
        'search_strategy': list_filter.DecimalFilter,
        'filter_strategy': list_filter.DecimalFilter,
    },

    camelot.types.Months: lambda f: {
        'python_type': int,
        'delegate': delegates.MonthsDelegate,
        'editable': True,
        'nullable': True,
        'from_string': int_from_string,
        'to_string': str,
        'search_strategy': list_filter.MonthsFilter,
        'filter_strategy': list_filter.MonthsFilter,
    },

    sqlalchemy.types.Integer: lambda f: {
        'python_type': int,
        'editable': True,
        'minimum': constants.camelot_minint,
        'maximum': constants.camelot_maxint,
        'nullable': True,
        'delegate': delegates.IntegerDelegate,
        'from_string': int_from_string,
        'to_string': str,
        'widget': 'int',
        'search_strategy': list_filter.IntFilter,
        'filter_strategy': list_filter.IntFilter,
    },

    sqlalchemy.types.String: lambda f: {
        'python_type': str,
        'length': f.length,
        'delegate': delegates.PlainTextDelegate,
        'editable': True,
        'nullable': True,
        'widget': 'str',
        'from_string': string_from_string,
        'search_strategy': list_filter.StringFilter,
        'filter_strategy': list_filter.StringFilter,
    },

    camelot.types.VirtualAddress: lambda f: {
        'python_type': str,
        'editable': True,
        'nullable': True,
        'delegate': delegates.VirtualAddressDelegate,
        'from_string' : lambda str:None,
        'search_strategy': list_filter.NoFilter,
        'filter_strategy': list_filter.NoFilter,
    },

    camelot.types.RichText: lambda f: {
        'python_type': str,
        'editable': True,
        'nullable': True,
        'delegate': delegates.RichTextDelegate,
        'from_string': string_from_string,
        'to_string': richtext_to_string,
        'search_strategy': list_filter.StringFilter,
        'filter_strategy': list_filter.StringFilter,
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
        'to_string': enumeration_to_string,
        'search_strategy': list_filter.NoFilter,
        'filter_strategy': list_filter.ChoicesFilter,
    },

    camelot.types.Language: lambda f: {
        'delegate': delegates.LanguageDelegate,
        'python_type': str,
        'default': default_language,
        'from_string': string_from_string,
        'editable': True,
        'nullable': False,
        'widget': 'combobox',
        'search_strategy': list_filter.StringFilter,
        'filter_strategy': list_filter.StringFilter,
    },

    camelot.types.File : lambda f: {
        'python_type': str,
        'editable': True,
        'delegate': delegates.FileDelegate,
        'storage': f.storage,
        'remove_original': False,
        'search_strategy': list_filter.NoFilter,
        'filter_strategy': list_filter.NoFilter,
        'actions': [
            field_action.DetachFile(),
            field_action.OpenFile(),
            field_action.UploadFile(),
            field_action.SaveFile()
        ],
    },

    camelot.types.Color: lambda f: {
        'delegate': delegates.ColorDelegate,
        'python_type': str,
        'from_string': string_from_string,
        'editable': True,
        'nullable': True,
        'search_strategy': list_filter.NoFilter,
        'filter_strategy': list_filter.NoFilter,
    },
}

_typing_to_python_type = {
    bool: {
        'python_type': bool,
        'delegate': delegates.BoolDelegate,
        'from_string': bool_from_string,
    },
    datetime.date: {
        'python_type': datetime.date,
        'format': constants.camelot_date_format,
        'min': None,
        'max': None,
        'delegate': delegates.DateDelegate,
        'from_string': date_from_string,
    },
    float: {
        'python_type': float,
        'minimum': constants.camelot_minfloat,
        'maximum': constants.camelot_maxfloat,
        'delegate': delegates.FloatDelegate,
        'from_string': float_from_string,
    },
    Decimal: {
        'python_type': float,
        'minimum': constants.camelot_minfloat,
        'maximum': constants.camelot_maxfloat,
        'delegate': delegates.FloatDelegate,
        'from_string': float_from_string,
        'decimal':True,
    },    
    int: {
        'python_type': int,
        'minimum': constants.camelot_minint,
        'maximum': constants.camelot_maxint,
        'delegate': delegates.IntegerDelegate,
        'from_string': int_from_string,
        'to_string': str,
        'widget': 'int',
    },
    str: {
        'python_type': str,
        'delegate': delegates.PlainTextDelegate,
        'widget': 'str',
        'from_string': string_from_string,
    },
    Note: {
        'python_type': str,
        'delegate': delegates.NoteDelegate,
        'editable': False,
    },
    Directory:{
        'python_type': str,
        'delegate': delegates.LocalFileDelegate,
        'directory':True ,      
    },
    File:{
        'python_type': str,
        'delegate': delegates.LocalFileDelegate,
    }, 
    Months:{
        'python_type': int,
        'delegate': delegates.MonthsDelegate,
    },

    Color: {
        'python_type': str,
        'delegate': delegates.ColorDelegate,
        'from_string': string_from_string,
    },

}

