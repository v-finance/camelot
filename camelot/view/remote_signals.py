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

"""
Classes to connect the QT event loop with a messaging
server.  To enable multiple clients to push model updates
to each other or messages for the users.

As a messaging server, Apache active MQ was tested in combination
with the stomp library (http://docs.codehaus.org/display/STOMP/Python)
"""

import logging
import re

LOGGER = logging.getLogger('remote_signals')

from PyQt4 import QtCore

class SignalHandler(QtCore.QObject):
    """The signal handler connects multiple collection proxy classes to
    inform each other when they have changed an object.
    
    If the object is persistent (eg mapped by SQLAlchemy), the signal hanler
    can inform other signal handlers on the network of the change.
    
    A couple of the methods of this thread are protected by a QMutex through
    the synchronized decorator.  It appears that python/qt deadlocks when the
    entity_update_signal is connected to and emitted at the same time.  This
    can happen when the user closes a window that is still building up (the
    CollectionProxies are being constructed and they connect to the signal
    handler).
    
    These deadlock issues are resolved in recent PyQt, so comment out the 
    mutex stuff. (2011-08-12)
     """

    entity_update_signal = QtCore.pyqtSignal(object, object)
    entity_delete_signal = QtCore.pyqtSignal(object, object)
    entity_create_signal = QtCore.pyqtSignal(object, object)
    
    entity_update_pattern = r'^/topic/Camelot.Entity.(?P<entity>.*).update$' 
    
    def __init__(self):
        super(SignalHandler, self).__init__()
        self.update_expression = re.compile(self.entity_update_pattern)
            
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
        # deprecated
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

