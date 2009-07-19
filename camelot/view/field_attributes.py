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
import sys

from PyQt4 import QtGui
from controls import delegates
from camelot.core.constants import *

_sqlalchemy_to_python_type_ = {
                               
  sqlalchemy.types.Boolean: lambda f: {'python_type': bool,
                                       'editable': True,
                                       'nullable':True,
                                       'delegate': delegates.BoolColumnDelegate },

  sqlalchemy.types.BOOLEAN: lambda f: {'python_type': bool,
                                       'editable': True,
                                       'nullable':True,
                                       'delegate': delegates.BoolColumnDelegate},

  sqlalchemy.types.Date: lambda f: {'python_type': datetime.date,
                                    'format': 'dd/MM/yyyy',
                                    'editable': True,
                                    'min': None,
                                    'max': None,
                                    'nullable':True,
                                    'delegate': delegates.DateColumnDelegate },

  sqlalchemy.types.Float: lambda f: {'python_type': float,
                                     'precision': f.precision,
                                     'editable': True,
                                     'minimum': camelot_minfloat,
                                     'maximum': camelot_maxfloat,
                                     'nullable':True,
                                     'delegate': delegates.FloatColumnDelegate},

  sqlalchemy.types.Integer: lambda f: {'python_type': int,
                                       'editable': True,
                                       'minimum': camelot_minint,
                                       'maximum': camelot_maxint,
                                       'nullable':True,
                                       'delegate':delegates.IntegerColumnDelegate,
                                       'widget': 'int'},

  sqlalchemy.types.INT: lambda f: {'python_type': int,
                                   'editable': True,
                                   'minimum': camelot_minint,
                                   'maximum': camelot_maxint,
                                   'nullable':True,
                                   'delegate':delegates.IntegerColumnDelegate,
                                   'widget': 'int'},

  sqlalchemy.types.String: lambda f: {'python_type': str,
                                      'length': f.length,
                                      'delegate': delegates.PlainTextColumnDelegate,
                                      'editable': True,
                                      'nullable':True,
                                      'widget': 'str'},

  sqlalchemy.types.TEXT: lambda f: {'python_type': str,
                                    'length': f.length,
                                    'delegate': delegates.PlainTextColumnDelegate,
                                    'editable': True,
                                    'nullable':True,
                                    'widget': 'str'},

  sqlalchemy.types.Unicode: lambda f: {'python_type': str,
                                       'length': f.length,
                                       'delegate': delegates.PlainTextColumnDelegate,
                                       'editable': True,
                                       'nullable':True,
                                       'widget': 'str'},

  camelot.types.Image: lambda f: {'python_type': str,
                                  'editable': True,
                                  'nullable':True,
                                  'delegate': delegates.ImageColumnDelegate,
                                  'storage':f.storage,},

  camelot.types.Code: lambda f: {'python_type': str,
                                 'editable': True,
                                 'delegate': delegates.CodeColumnDelegate,
                                 'nullable':True,
                                 'parts': f.parts},

  camelot.types.IPAddress: lambda f: {'python_type': str,
                                 'editable': True,
                                 'widget': 'code',
                                 'nullable':True,
                                 'parts': f.parts},
                                                                  
  camelot.types.VirtualAddress: lambda f:{'python_type':str,
                                          'editable':True,
                                          'nullable':True,
                                          'delegate':delegates.VirtualAddressColumnDelegate,
                                          },

  camelot.types.RichText: lambda f:{'python_type':str,
                                    'editable':True,
                                    'nullable':True,
                                    'delegate':delegates.RichTextColumnDelegate,
                                   },
                                   
  camelot.types.Color: lambda f:{'delegate':delegates.ColorColumnDelegate,
                                 'python_type':str,
                                 'editable':True,
                                 'nullable':True,
                                 'widget':'color'},
                                 
  camelot.types.Rating: lambda f:{'delegate':delegates.StarDelegate,
                                  'editable':True,
                                  'nullable':True,
                                  'python_type':int,
                                  'widget':'star'},
                                  
  camelot.types.Enumeration: lambda f:{'delegate':delegates.ComboBoxColumnDelegate,
                                       'python_type':str,
                                       'choices':lambda o:[(v,v.capitalize().replace('_',' ')) for v in f.choices],
                                       'editable':True,
                                       'nullable':False,
                                       'widget':'combobox',
                                       },
                                                                           
  sqlalchemy.types.Time : lambda f: {'python_type':datetime.time,
                                     'editable':True,
                                     'nullable':True,
                                     'widget':'time',
                                     'delegate':delegates.TimeColumnDelegate,
                                     'format':'hh:mm',
                                     'nullable':True},
                                     
  
  sqlalchemy.types.DateTime : lambda f: {'python_type':datetime.datetime,
                                         'editable':True,
                                         'nullable':True,
                                         'widget':'time',
                                         'format':'dd-MM-yyyy hh:mm',
                                         'nullable':True,
                                         'delegate':delegates.DateTimeColumnDelegate},
  camelot.types.File : lambda f: {'python_type':str,
                                  'editable':True,
                                  'delegate':delegates.FileDelegate,
                                  'storage':f.storage},
                                         
  
}
