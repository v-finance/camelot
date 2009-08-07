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

"""Utility functions"""

def create_constant_function(constant):
  return lambda:constant


def variant_to_pyobject(qvariant=None):
    from PyQt4 import QtCore, QtGui
    from PyQt4.QtCore import Qt
    import datetime
    if not qvariant:
        return None
    
    type = qvariant.type()
    if type == QtCore.QVariant.String:
      value = unicode(qvariant.toString())
    elif type == QtCore.QVariant.Date:
      value = qvariant.toDate()
      value = datetime.date(year=value.year(),
                            month=value.month(),
                            day=value.day())
    elif type == QtCore.QVariant.Int:
      value = int(qvariant.toInt()[0])
    elif type == QtCore.QVariant.Double:
      value = float(qvariant.toDouble()[0])
    elif type == QtCore.QVariant.Bool:
      value = bool(qvariant.toBool())
    elif type == QtCore.QVariant.Time:
        value = qvariant.toTime()
        value = datetime.time(hour = value.hour(),
                              minute = value.minute(),
                              second = value.second())
    else:
      value = qvariant.toPyObject()
      
    
    return value

