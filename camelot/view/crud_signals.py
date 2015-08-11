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



