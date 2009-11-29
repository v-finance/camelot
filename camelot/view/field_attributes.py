#  ============================================================================
#
#  Copyright (C) 2007-2008 Conceptive Engineering bvba. All rights reserved.
#  www.conceptive.be / project-camelot@conceptive.be
#
#  This file is part of the Camelot Library.
#
#  This file may be used under the terms of the GNU General Public
#  License version 2.0 as published by the Free Software Foundation
#  and appearing in the file LICENSE.GPL included in the packaging of
#  this file.  Please review the following information to ensure GNU
#  General Public Licensing requirements will be met:
#  http://www.trolltech.com/products/qt/opensource.html
#
#  If you are unsure which license is appropriate for your use, please
#  review the following information:
#  http://www.trolltech.com/products/qt/licensing.html or contact
#  project-camelot@conceptive.be.
#
#  This file is provided AS IS with NO WARRANTY OF ANY KIND, INCLUDING THE
#  WARRANTY OF DESIGN, MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE.
#
#  For use of this library in commercial applications, please contact
#  project-camelot@conceptive.be
#
#  ============================================================================

"""Default field attributes for various sqlalchemy column types"""

import sqlalchemy.types
import camelot.types
import datetime

from controls import delegates
from camelot.core import constants
from camelot.core.utils import ugettext as _
from camelot.view.utils import (
    bool_from_string,
    date_from_string,
    time_from_string,
    datetime_from_string,
    int_from_string,
    float_from_string,
    string_from_string,
)


_sqlalchemy_to_python_type_ = {

    sqlalchemy.types.Boolean: lambda f: {
        'python_type': bool,
        'editable': True,
        'nullable': True,
        'delegate': delegates.BoolDelegate,
        'from_string': bool_from_string
    },

    sqlalchemy.types.BOOLEAN: lambda f: {
        'python_type': bool,
        'editable': True,
        'nullable': True,
        'delegate': delegates.BoolDelegate,
        'from_string': bool_from_string
    },

    sqlalchemy.types.Date: lambda f: {
        'python_type': datetime.date,
        'format': constants.camelot_date_format,
        'editable': True,
        'min': None,
        'max': None,
        'nullable': True,
        'delegate': delegates.DateDelegate,
        'from_string': date_from_string
    },

    sqlalchemy.types.Time : lambda f: {
            'python_type': datetime.time,
            'editable': True,
            'nullable': True,
            'widget': 'time',
            'delegate': delegates.TimeDelegate,
            'format': constants.camelot_time_format,
            'nullable': True,
            'from_string': time_from_string
    },

    sqlalchemy.types.DateTime : lambda f: {
        'python_type': datetime.datetime,
        'editable': True,
        'nullable': True,
        'widget': 'time',
        'format': constants.camelot_datetime_format,
        'nullable': True,
        'delegate': delegates.DateTimeDelegate,
        'from_string': datetime_from_string
    },

    sqlalchemy.types.Float: lambda f: {
        'python_type': float,
        'precision': f.precision,
        'editable': True,
        'minimum': constants.camelot_minfloat,
        'maximum': constants.camelot_maxfloat,
        'nullable': True,
        'delegate': delegates.FloatDelegate,
        'from_string': float_from_string
    },

    sqlalchemy.types.Integer: lambda f: {
        'python_type': int,
        'editable': True,
        'minimum': constants.camelot_minint,
        'maximum': constants.camelot_maxint,
        'nullable': True,
        'delegate': delegates.IntegerDelegate,
        'from_string': int_from_string,
        'to_string': unicode,
        'widget': 'int'
    },

    sqlalchemy.types.INT: lambda f: {
        'python_type': int,
        'editable': True,
        'minimum': constants.camelot_minint,
        'maximum': constants.camelot_maxint,
        'nullable': True,
        'delegate': delegates.IntegerDelegate,
        'from_string': int_from_string,
        'widget': 'int'
    },

    sqlalchemy.types.String: lambda f: {
        'python_type': str,
        'length': f.length,
        'delegate': delegates.PlainTextDelegate,
        'editable': True,
        'nullable': True,
        'widget': 'str',
        'from_string': string_from_string,
    },

    sqlalchemy.types.TEXT: lambda f: {
        'python_type': str,
        'length': f.length,
        'delegate': delegates.PlainTextDelegate,
        'editable': True,
        'nullable': True,
        'widget': 'str',
        'from_string': string_from_string,
    },

    sqlalchemy.types.Unicode: lambda f: {
        'python_type': str,
        'length': f.length,
        'delegate': delegates.PlainTextDelegate,
        'editable': True,
        'nullable': True,
        'widget': 'str',
        'from_string': string_from_string,
    },

    camelot.types.Image: lambda f: {
        'python_type': str,
        'editable': True,
        'nullable': True,
        'delegate': delegates.ImageDelegate,
        'storage': f.storage,
        'preview_width': 100,
        'preview_height': 100
    },

    camelot.types.Code: lambda f: {
        'python_type': str,
        'editable': True,
        'delegate': delegates.CodeDelegate,
        'nullable': True,
        'parts': f.parts
    },

    camelot.types.IPAddress: lambda f: {
        'python_type': str,
        'editable': True,
        'nullable': True,
        'parts': f.parts,
        'delegate': delegates.CodeDelegate,
        'widget': 'code'
    },

    camelot.types.VirtualAddress: lambda f: {
        'python_type': str,
        'editable': True,
        'nullable': True,
        'delegate': delegates.VirtualAddressDelegate
    },

    camelot.types.RichText: lambda f: {
        'python_type': str,
        'editable': True,
        'nullable': True,
        'delegate': delegates.RichTextDelegate,
        'from_string': string_from_string,
    },

    camelot.types.Color: lambda f: {
        'delegate': delegates.ColorDelegate,
        'python_type': str,
        'editable': True,
        'nullable': True,
        'widget': 'color'
    },

    camelot.types.Rating: lambda f: {
        'delegate': delegates.StarDelegate,
        'editable': True,
        'nullable': True,
        'python_type': int,
        'widget': 'star',
        'from_string': int_from_string
    },

    camelot.types.Enumeration: lambda f: {
        'delegate': delegates.EnumerationDelegate,
        'python_type': str,
        'choices': [
            (v, unicode(_(unicode(v).replace('_', ' '))).capitalize()) 
            for v in f.choices
        ],
        'from_string': lambda s:dict((unicode(_(unicode(v).replace('_', ' '))).capitalize(), v)
                                     for v in f.choices)[s],
        'editable': True,
        'nullable': False,
        'widget': 'combobox',
    },
    
    camelot.types.Language: lambda f: {
        'delegate': delegates.EnumerationDelegate,
        'python_type': str,
        'choices': f.choices,
        'from_string': string_from_string,
        'editable': True,
        'nullable': False,
        'widget': 'combobox',
    },    

    camelot.types.File : lambda f: {
        'python_type': str,
        'editable': True,
        'delegate': delegates.FileDelegate,
        'storage': f.storage
    },
}

#
# Generate a restructured text table out of the prevous data structure
#

class DummyField(object):
    def __init__(self):
        self.length = 20
        self.parts = ['AAA', '99']
        self.choices = ['planned', 'canceled']
        self.precision = 2
        self.storage = None

row_separator = '+' + '-'*20 + '+' + '-'*30 + '+' + '-'*70 + '+'
row_format = """| %-18s | %-28s | %-68s |"""

doc = """Field types handled through introspection :

""" + row_separator + """
""" + row_format%('**Field type**', '**Default delegate**', '**Default editor**') + """
""" + row_separator + """
"""

field_types = _sqlalchemy_to_python_type_.keys()
field_types.sort(lambda x, y: cmp(x.__name__, y.__name__))

for field_type in field_types:
    field_attributes = _sqlalchemy_to_python_type_[field_type](DummyField())
    delegate = field_attributes['delegate']
    row = row_format%(field_type.__name__, delegate.__name__, '.. image:: ../_static/editors/%s_editable.png'%(delegate.editor.__name__))
    doc += row + """
  """ + row_separator + """
  """

doc += """
"""

__doc__ = doc
