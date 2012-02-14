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
Various ``ActionStep`` subclasses that inform the GUI of changes
in the model.
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
        signal_handler = get_signal_handler()
        if obj != None:
            signal_handler.sendEntityUpdate( self, obj )
    
    def gui_run( self, gui_context ):
        pass

class DeleteObject( ActionStep ):
    """Inform the GUI that obj is going to be deleted.

    :param obj: the object that is going to be deleted
    """
    
    def __init__( self, obj ):
        signal_handler = get_signal_handler()
        if obj != None:
            signal_handler.sendEntityDelete( self, obj )
    
    def gui_run( self, gui_context ):
        pass
    
class CreateObject( ActionStep ):
    """Inform the GUI that obj was created.

    :param obj: the object that was created
    """
    
    def __init__( self, obj ):
        signal_handler = get_signal_handler()
        if obj != None:
            signal_handler.sendEntityCreate( self, obj )
    
    def gui_run( self, gui_context ):
        pass

