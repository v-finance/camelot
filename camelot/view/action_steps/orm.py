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

"""
Various ``ActionStep`` subclasses that inform the GUI of changes
in the model.

These action steps can be used to update the GUI before changes have been
saved to the database through the manual updates :
    
.. literalinclude:: ../../../test/test_action.py
   :start-after: begin manual update
   :end-before: end manual update
       
Or use introspection of the SQLAlchemy session to update the GUI :

.. literalinclude:: ../../../test/test_action.py
   :start-after: begin auto update
   :end-before: end auto update
   
"""

import warnings

from camelot.admin.action.base import ActionStep
from ..crud_signals import CrudSignalHandler

class AbstractCrudSignal(ActionStep):

    def __init__(self):
        self.objects_deleted = tuple()
        self.objects_updated = tuple()
        self.objects_created = tuple()

    def gui_run(self, gui_context):
        super(AbstractCrudSignal, self).gui_run(gui_context)
        crud_signal_handler = CrudSignalHandler()
        if len(self.objects_deleted):
            crud_signal_handler.send_objects_deleted(self, self.objects_deleted)
        if len(self.objects_updated):
            crud_signal_handler.send_objects_updated(self, self.objects_updated)
        if len(self.objects_created):
            crud_signal_handler.send_objects_created(self, self.objects_created)

class FlushSession(AbstractCrudSignal):
    """Flushes the session and informs the GUI about the
    changes.
    
    :param session: an instance of :class:`sqlalchemy.orm.Session`
    :param update_depending_objects: set to `False` if the objects that depend
        on an object that has been modified need not to be updated in the GUI.
        This will make the flushing faster, but the GUI might become
        inconsistent.
    """

    def __init__(self, session, update_depending_objects = True):
        super(FlushSession, self).__init__()
        #
        # @todo : deleting of objects should be moved from the collection_proxy
        #         to here, once deleting rows is reimplemented as an action
        #
        # @todo : handle the creation of new objects
        #
        # list of objects that need to receive an update signal
        dirty_objects = set( session.dirty )
        
        #for dirty_object in session.dirty:
        #    obj_admin = admin.get_related_admin( type( dirty_object ) )
        #    if obj_admin:
        #        dirty_objects.update( obj_admin.get_depending_objects( dirty_object ) )
        self.objects_deleted = tuple(session.deleted)
        #
        # Only now is the full list of dirty objects available, so the deleted
        # can be removed from them
        #
        for obj_to_delete in session.deleted:
            try:
                dirty_objects.remove(obj_to_delete)
            except KeyError:
                pass
        
        session.flush()
        self.objects_updated = tuple(dirty_objects)


class UpdateObjects(AbstractCrudSignal):
    """Inform the GUI that objects have changed.

    :param objects: the objects that have changed
    """

    def __init__(self, objects):
        super(UpdateObjects, self).__init__()
        self.objects_updated = tuple(objects)

    def get_objects(self):
        return self.objects_updated

class DeleteObjects(AbstractCrudSignal):
    """Inform the GUI that objects are going to be deleted.

    :param objects: the objects that are going to be deleted
    """

    def __init__( self, objects ):
        super(DeleteObjects, self).__init__()
        self.objects_deleted = tuple(objects)

    def get_objects(self):
        return self.objects_deleted

class CreateObjects(AbstractCrudSignal):
    """Inform the GUI that objects were created.

    :param objects: the objects that were created
    """

    def __init__( self, objects ):
        super(CreateObjects, self).__init__()
        self.objects_created = tuple(objects)

    def get_objects(self):
        return self.objects_created

class UpdateObject(UpdateObjects):
    """For backwards compatibility, don't use, use UpdateObjects"""

    def __init__(self, obj):
        super(UpdateObject, self).__init__((obj,))
        warnings.warn("deprecated, use UpdateObjects", DeprecationWarning)

    def get_object(self):
        warnings.warn("deprecated, use get_objects", DeprecationWarning)
        return self.objects_updated[0]

class DeleteObject(DeleteObjects):
    """For backwards compatibility, don't use, use DeleteObjects"""

    def __init__(self, obj):
        warnings.warn("deprecated, use DeleteObjects", DeprecationWarning)
        super(DeleteObject, self).__init__((obj,))

    def get_object(self):
        warnings.warn("deprecated, use get_objects", DeprecationWarning)
        return self.objects_deleted[0]

class CreateObject(CreateObjects):
    """For backwards compatibility, don't use, use CreateObjects"""

    def __init__(self, obj):
        warnings.warn("deprecated, use CreateObjects", DeprecationWarning)
        super(CreateObject, self).__init__((obj,))

    def get_object(self):
        warnings.warn("deprecated, use get_objects", DeprecationWarning)
        return self.objects_created[0]




