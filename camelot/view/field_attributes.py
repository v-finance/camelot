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
from controls.editors import *
from controls.delegates import *

camelot_maxint = 2147483647
camelot_minint = -2147483648

_sqlalchemy_to_python_type_ = {
                               
  sqlalchemy.types.Boolean: lambda f: {'python_type': bool,
                                       'editable': True,
                                       'widget': QtGui.QCheckBox },

  sqlalchemy.types.BOOLEAN: lambda f: {'python_type': bool,
                                       'editable': True,
                                       'widget': QtGui.QCheckBox},

  sqlalchemy.types.Date: lambda f: {'python_type': datetime.date,
                                    'format': 'dd-mm-YYYY',
                                    'editable': True,
                                    'min': None,
                                    'max': None,
                                    'widget': DateEditor },

  sqlalchemy.types.Float: lambda f: {'python_type': float,
                                     'precision': f.precision,
                                     'editable': True,
                                     'min': None,
                                     'max': None,
                                     'widget': 'float'},

  sqlalchemy.types.Integer: lambda f: {'python_type': int,
                                       'editable': True,
                                       'minimum': camelot_minint,
                                       'maximum': camelot_maxint,
                                       'widget': 'int'},

  sqlalchemy.types.INT: lambda f: {'python_type': int,
                                   'editable': True,
                                   'minimum': camelot_minint,
                                   'maximum': camelot_maxint,
                                   'widget': 'int'},

  sqlalchemy.types.String: lambda f: {'python_type': str,
                                      'length': f.length,
                                      'editable': True,
                                      'widget': 'str'},

  sqlalchemy.types.TEXT: lambda f: {'python_type': str,
                                    'length': f.length,
                                    'editable': True,
                                    'widget': 'str'},

  sqlalchemy.types.Unicode: lambda f: {'python_type': str,
                                       'length': f.length,
                                       'editable': True,
                                       'widget': 'str'},

  camelot.types.Image: lambda f: {'python_type': str,
                                  'editable': True,
                                  'widget': 'image'},

  camelot.types.Code: lambda f: {'python_type': str,
                                 'editable': True,
                                 'widget': 'code',
                                 'parts': f.parts},

  camelot.types.IPAddress: lambda f: {'python_type': str,
                                 'editable': True,
                                 'widget': 'code',
                                 'parts': f.parts},
                                                                  
  camelot.types.VirtualAddress: lambda f:{'python_type':str,
                                          'editable':True,
                                          'widget':'virtual_address',
                                          },

  camelot.types.RichText: lambda f:{'python_type':str,
                                    'editable':True,
                                    'widget':'richtext',
                                   },
                                   
  camelot.types.Color: lambda f:{'delegate':ColorColumnDelegate,
                                 'python_type':str,
                                 'editable':True,
                                 'nullable':True,
                                 'widget':'color'},
                                                                           
  sqlalchemy.types.Time : lambda f: {'python_type':datetime.time,
                                     'editable':True,
                                     'widget':'time',
                                     'delegate':TimeColumnDelegate,
                                     'format':'hh:mm',
                                     'nullable':True},
  
  sqlalchemy.types.DateTime : lambda f: {'python_type':datetime.datetime,
                                         'editable':True,
                                         'widget':'time',
                                         'format':'dd-MM-yyyy hh:mm',
                                         'nullable':True,
                                         'widget':'datetime'},
                                         
  
}
