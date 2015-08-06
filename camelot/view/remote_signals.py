#  ============================================================================
#
#  Copyright (C) 2007-2013 Conceptive Engineering bvba. All rights reserved.
#  www.conceptive.be / info@conceptive.be
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
#  visit www.python-camelot.com or contact info@conceptive.be
#
#  This file is provided AS IS with NO WARRANTY OF ANY KIND, INCLUDING THE
#  WARRANTY OF DESIGN, MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE.
#
#  For use of this library in commercial applications, please contact
#  info@conceptive.be
#
#  ============================================================================
import logging

LOGGER = logging.getLogger('remote_signals')

from ..core.qt import QtCore
from .model_thread import object_thread, gui_thread

class SignalHandler(QtCore.QObject):
    """The signal handler connects multiple collection proxy classes to
    inform each other when they have changed an object.
    
    If the object is persistent (eg mapped by SQLAlchemy), the signal handler
    could be used to inform other signal handlers on the network of the change.
     """

    objects_updated = QtCore.qt_signal(object, tuple)
    objects_deleted = QtCore.qt_signal(object, tuple)
    objects_created = QtCore.qt_signal(object, tuple)
    
    def __init__(self):
        super(SignalHandler, self).__init__()
            
    def connect_signals(self, obj):
        """Connect the SignalHandlers its signals to the slots of obj, while
        the mutex is locked"""
        assert object_thread(self)
        self.objects_updated.connect(obj.objects_updated)
        self.objects_deleted.connect(obj.objects_deleted)
        self.objects_created.connect(obj.objects_created)
        
    def send_objects_updated(self, sender, objects, scope='local'):
        """Call this method to inform the whole application an entity has 
        changed"""
        assert object_thread(self)
        self.objects_updated.emit(sender, objects)

    def send_objects_deleted(self, sender, objects, scope='local'):
        """Call this method to inform the whole application an entity is 
        about to be deleted"""
        assert object_thread(self)
        self.objects_deleted.emit(sender, objects)
            
    def send_objects_created(self, sender, objects, scope='local'):
        """Call this method to inform the whole application an entity is 
        about to be deleted"""
        assert object_thread(self)
        self.objects_created.emit(sender, objects)

_signal_handler_ = []

def construct_signal_handler(*args, **kwargs):
    """Construct the singleton signal handler"""
    _signal_handler_.append(SignalHandler(*args, **kwargs))

def get_signal_handler():
    """Get the singleton signal handler"""
    assert gui_thread
    if not len(_signal_handler_):
        construct_signal_handler()
    return _signal_handler_[-1]

def has_signal_handler():
    """Request if the singleton signal handler was constructed"""
    return len(_signal_handler_)


