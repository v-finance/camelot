#  ============================================================================
#
#  Copyright (C) 2007-2012 Conceptive Engineering bvba. All rights reserved.
#  www.conceptive.be / project-camelot@conceptive.be
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
#  visit www.python-camelot.com or contact project-camelot@conceptive.be
#
#  This file is provided AS IS with NO WARRANTY OF ANY KIND, INCLUDING THE
#  WARRANTY OF DESIGN, MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE.
#
#  For use of this library in commercial applications, please contact
#  project-camelot@conceptive.be
#
#  ============================================================================
'''
Some helper functions and classes related
to threading issues
'''

from PyQt4 import QtCore

def synchronized( original_function ):
    """Decorator for synchronized access to an object, the object should
    have an attribute _mutex which is of type QMutex
    """

    from functools import wraps

    @wraps( original_function )
    def wrapper(self, *args, **kwargs):
        locker = QtCore.QMutexLocker(self._mutex)
        result = original_function(self, *args, **kwargs)
        locker.unlock()
        return result

    return wrapper



