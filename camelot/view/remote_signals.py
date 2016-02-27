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
import logging

LOGGER = logging.getLogger('remote_signals')

from ..core.qt import QtCore

class SignalHandler(QtCore.QObject):
    """The signal handler connects multiple collection proxy classes to
    inform each other when they have changed an object.
    
    If the object is persistent (eg mapped by SQLAlchemy), the signal handler
    could be used to inform other signal handlers on the network of the change.
     """

    entity_update_signal = QtCore.qt_signal(object, object)
    entity_delete_signal = QtCore.qt_signal(object, object)
    entity_create_signal = QtCore.qt_signal(object, object)
    
    def __init__(self):
        super(SignalHandler, self).__init__()
            
    def connect_signals(self, obj):
        """Connect the SignalHandlers its signals to the slots of obj, while
        the mutex is locked"""
        self.entity_update_signal.connect( obj.handle_entity_update, QtCore.Qt.QueuedConnection )
        self.entity_delete_signal.connect( obj.handle_entity_delete, QtCore.Qt.QueuedConnection )
        self.entity_create_signal.connect( obj.handle_entity_create, QtCore.Qt.QueuedConnection )
        
    def send_entity_update(self, sender, entity, scope='local'):
        """Call this method to inform the whole application an entity has 
        changed"""
        self.sendEntityUpdate(sender, entity, scope)
    
    def sendEntityUpdate(self, sender, entity, scope='local'):
        """Call this method to inform the whole application an entity has 
        changed"""
        self.entity_update_signal.emit( sender, entity )
        
    def sendEntityDelete(self, sender, entity, scope='local'):
        """Call this method to inform the whole application an entity is 
        about to be deleted"""
        self.entity_delete_signal.emit( sender, entity )
            
    def sendEntityCreate(self, sender, entity, scope='local'):
        """Call this method to inform the whole application an entity 
        was created"""
        self.entity_create_signal.emit( sender, entity )

_signal_handler_ = []

def construct_signal_handler(*args, **kwargs):
    """Construct the singleton signal handler"""
    _signal_handler_.append(SignalHandler(*args, **kwargs))

def get_signal_handler():
    """Get the singleton signal handler"""
    if not len(_signal_handler_):
        construct_signal_handler()
    return _signal_handler_[-1]

def has_signal_handler():
    """Request if the singleton signal handler was constructed"""
    return len(_signal_handler_)



