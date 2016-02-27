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

from camelot.admin.action.base import ActionStep
from camelot.view.remote_signals import get_signal_handler

class FlushSession( ActionStep ):
    """Flushes the session and informs the GUI about the
    changes.
    
    :param session: an instance of :class:`sqlalchemy.orm.Session`
    :param update_depending_objects: set to `False` if the objects that depend
        on an object that has been modified need not to be updated in the GUI.
        This will make the flushing faster, but the GUI might become
        inconsistent.
    """
        
    def __init__( self, session, update_depending_objects = True ):
        #
        # @todo : deleting of objects should be moved from the collection_proxy
        #         to here, once deleting rows is reimplemented as an action
        #
        # @todo : handle the creation of new objects
        #
        signal_handler = get_signal_handler()
        # list of objects that need to receive an update signal
        dirty_objects = set( session.dirty )
        
        #for dirty_object in session.dirty:
        #    obj_admin = admin.get_related_admin( type( dirty_object ) )
        #    if obj_admin:
        #        dirty_objects.update( obj_admin.get_depending_objects( dirty_object ) )
        
        for obj_to_delete in session.deleted:
        #    obj_admin = admin.get_related_admin( type( obj_to_delete ) )
        #    if obj_admin:
        #        dirty_objects.update( obj_admin.get_depending_objects( obj_to_delete ) )
            signal_handler.sendEntityDelete( self, obj_to_delete )
        #
        # Only now is the full list of dirty objects available, so the deleted
        # can be removed from them
        #
        for obj_to_delete in session.deleted:
            try:
                dirty_objects.remove( obj_to_delete )
            except KeyError:
                pass
        
        session.flush()
        for obj in dirty_objects:
            signal_handler.sendEntityUpdate( self, obj )
    
    def gui_run( self, gui_context ):
        pass
    
class UpdateObject( ActionStep ):
    """Inform the GUI that obj has changed.

    :param obj: the object that has changed
    """
    
    def __init__( self, obj ):
        self.obj = obj
        signal_handler = get_signal_handler()
        if self.obj != None:
            signal_handler.sendEntityUpdate( self, self.obj )
    
    def get_object(self):
        return self.obj

class DeleteObject( UpdateObject ):
    """Inform the GUI that obj is going to be deleted.

    :param obj: the object that is going to be deleted
    """
    
    def __init__( self, obj ):
        self.obj = obj
        signal_handler = get_signal_handler()
        if self.obj != None:
            signal_handler.sendEntityDelete( self, self.obj )
    
class CreateObject( UpdateObject ):
    """Inform the GUI that obj was created.

    :param obj: the object that was created
    """
    
    def __init__( self, obj ):
        self.obj = obj
        signal_handler = get_signal_handler()
        if self.obj != None:
            signal_handler.sendEntityCreate( self, self.obj )




