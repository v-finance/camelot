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
import six

from ..core.qt import QtCore, valid_variant, variant_to_py

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
        if valid_variant( monitored.property(self._key_name) ):
            key = variant_to_py(monitored.property( self._key_name ))
        else:
            self._max_monitor_key += 1
            key = self._max_monitor_key
            monitored.destroyed[QtCore.QObject].connect( self._monitored_object_destroyed )
        LOGGER.debug('monitor object with key %s'%key)
        self._registed_by_monitor_key[key] = registered
        monitored.setProperty( self._key_name, key )
        
    @QtCore.qt_slot(QtCore.QObject)
    def _monitored_object_destroyed(self, qobject):
        """slot to indicate a monitored object is destroyed"""
        key = variant_to_py( qobject.property( self._key_name ) )
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

def dump_register( logger ):
    """Method to see the currently monitored objects, for debugging
    purposes"""
    if _global_register_:
        for k,v in six.iteritems(_global_register_._registed_by_monitor_key):
            logger.warn( '%s : %s'%( k, v ) )


