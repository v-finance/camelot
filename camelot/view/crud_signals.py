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

LOGGER = logging.getLogger('camelot.view.crud_signals')

from ..core.qt import QtCore
from .model_thread import object_thread, gui_thread


class CrudSignalHandler(QtCore.QObject):
    """The signal handler connects multiple :class:`QtCore.QObject` instances to
    inform each other when they have changed an object.

    A gui :class:`QtCore.QObject` instances that wants to be informed on object
    changes should instantiate the signal handler and connect to its signals.

    The signal handler could be used to inform other signal handlers
    on the network of the change.
     """

    objects_updated = QtCore.qt_signal(object, tuple)
    objects_deleted = QtCore.qt_signal(object, tuple)
    objects_created = QtCore.qt_signal(object, tuple)

    __instance = None

    def __new__(cls):
        assert gui_thread()
        if cls.__instance is None:
            instance = super(CrudSignalHandler, cls).__new__(cls)
            instance.__init__()
            cls.__instance = instance
        return cls.__instance

    def __init__(self):
        if self.__instance is None:
            super(CrudSignalHandler, self).__init__()

    def connect_signals(self, obj):
        """Connect the SignalHandlers its signals to the slots of obj"""
        assert object_thread(self)
        assert object_thread(obj)
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




