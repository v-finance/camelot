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
Global registry to register that an Python Object should
be scheduled for garbage collection, when a
QObject is destroyed.

This is used to combine models and views, where
the model should be garbage collected once it has
no views any more.  But as long as it has views, it
should be kept alive.
'''

import logging

from PyQt4 import QtCore

LOGGER = logging.getLogger('camelot.view.register')

class Register(QtCore.QObject):
    """The register that takes care of the dependencies.
    It monitors an object and when the monitored object
    is destroyed, its registered object is scheduled for
    collection.
    """
    
    def __init__(self):
        super(Register, self).__init__()
        self._key_name = 'monitor_key'
        self._max_monitor_key = 0
        self._registed_by_monitor_key = dict()
        
    def register(self, registered, monitored):
        """
        :param registered: the object that will be registered
        :param monitored: the object that will be monitored
        """
        if monitored.property(self._key_name).isValid():
            key, _success = monitored.property( self._key_name ).toLongLong()
        else:
            self._max_monitor_key += 1
            key = self._max_monitor_key
            monitored.destroyed[QtCore.QObject].connect( self._monitored_object_destroyed )
        LOGGER.debug('monitor object with key %s'%key)
        self._registed_by_monitor_key[key] = registered
        monitored.setProperty( self._key_name, key )
        
    @QtCore.pyqtSlot(QtCore.QObject)
    def _monitored_object_destroyed(self, qobject):
        """slot to indicate a monitored object is destroyed"""
        key, _success = qobject.property( self._key_name ).toLongLong()
        LOGGER.debug('object with key %s is destroyed'%key)
        del self._registed_by_monitor_key[key]
        
_global_register_ = None

def register(registered, monitored):
    """Global function to register an object and start monitoring
    the dependent object
    
    This function takes care of creating the global register as well.
    """
    global _global_register_
    if _global_register_ == None:
        _global_register_ = Register()
    _global_register_.register(registered, monitored)

def dump_register():
    """Method to see the currently monitored objects, for debugging
    purposes"""
    for k,v in _global_register_._registed_by_monitor_key.items():
        print k,v

