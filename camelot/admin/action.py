#  ============================================================================
#
#  Copyright (C) 2007-2011 Conceptive Engineering bvba. All rights reserved.
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
This is part of a test implementation of the new actions draft, it is not
intended for production use
"""

import logging

from PyQt4 import QtCore

from camelot.core.exception import GuiException, CancelRequest
from camelot.core.utils import ugettext_lazy as _
from camelot.view.model_thread import post
from camelot.view.art import Icon

LOGGER = logging.getLogger( 'camelot.admin.action' )

class GuiContext( object ):
    
    def __init__( self, admin = None, workspace = None ):
        """The context of an action available in the *GUI thread*
        during the execution of the action.
        :param admin: the Admin class to use during the execution of the action,
           to be used to retrieve Admin classes for classes when needed.
           defaults to the unique ApplicationAdmin.
        """
        self._admin = admin
        self._workspace = workspace
        
    def get_admin( self ):
        """
        :return: the admin class that can be used to retrieve related admin
           classes
        """
        from camelot.admin.application_admin import get_application_admin
        return self._admin or get_application_admin()
    
    def get_workspace( self ):
        return self._workspace
    
class ActionRunner( QtCore.QEventLoop ):
    """Helper class for handling the signals and slots when an action
    is running.
    """
    
    def __init__( self, generator_function, gui_context ):
        """
        :param generator_function: function to be called in the model thread,
            that will return a generator
        :param gui_context: the GUI context of the generator
        """
        super( ActionRunner, self ).__init__()
        self._generator_function = generator_function
        self._generator = None
        self._gui_context = gui_context
        post( self._wrapped_generator_function, self.generator, self.exception )
        
    def _wrapped_generator_function( self ):
        """Wrapper around the generator_function that handles exceptions"""
        try:
            return self._generator_function()
        except CancelRequest:
            return None

    def _wrapped_generator_next( self ):
        """Wrapper around the next call of the generator that handles exceptions"""
        try:
            return self._generator.next()
        except CancelRequest:
            return None
        
    def _wrapped_generator_send( self, obj ):
        """Wrapper around the send call of the generator that handles exceptions"""
        try:
            return self._generator.send( obj )
        except CancelRequest:
            return None
        
    def _wrapped_generator_throw( self, exc ):
        """Wrapper around the throw call of the generator that handles exceptions"""
        try:
            return self._generator.throw( exc )
        except CancelRequest:
            return None
        
    @QtCore.pyqtSlot( object )
    def exception( self, exception_info ):
        from camelot.view.controls.exception import model_thread_exception_message_box
        model_thread_exception_message_box( exception_info )
        self.exit()
        
    @QtCore.pyqtSlot( object )
    def generator( self, generator ):
        self._generator = generator
        post( self._wrapped_generator_next, self.next, self.exception )
        
    @QtCore.pyqtSlot( object )
    def next( self, yielded ):
        """Handle the result of the next call of the generator
        
        :param yielded: the object that was yielded by the generator in the
            *model thread*
        """
        if isinstance( yielded, (ActionStep,) ):
            try:
                to_send = yielded.gui_run( self._gui_context )
                post( self._wrapped_generator_send, 
                      self.next, 
                      self.exception, 
                      args = (to_send,) )
            except CancelRequest, exc:
                post( self._wrapped_generator_throw,
                      self.next,
                      self.exception,
                      args = (exc,) )
            except Exception, exc:
                LOGGER.error( 'gui exception while executing action', 
                              exc_info=exc)
                #
                # In case of an exception in the GUI thread, propagate an
                # exception to make sure the generator ends.  Don't propagate
                # the very same exception, because no references from the GUI
                # should be past to the model.
                #
                post( self._wrapped_generator_throw,
                      self.next,
                      self.exception,
                      args = ( GuiException(), ) )
        elif isinstance( yielded, (StopIteration,) ):
             #
             # Process the events before exiting, as there might be exceptions
             # left in the signal slot queue
             #
            self.processEvents()
            self.exit()
        else:
            post( self._wrapped_generator_next,
                  self.next,
                  self.exception, )


        #self.exit()
    
class ActionStep( object ):
    """A reusable part of an action.  Action step object can be yielded inside
    the :meth:`model_run`.  When this happens, their :meth:`gui_run` method will
    be called inside the *GUI thread*.  The :meth:`gui_run` can pop up a dialog
    box or perform other GUI related tasks, and when finished return control
    to the :meth:`model_run` method.
    """

    verbose_name = _('Step')
    icon = Icon('tango/16x16/emblems/emblem-system.png')
        
    def get_verbose_name( self ):
        return self.verbose_name
        
    def get_icon( self ):
        return self.icon
        
    def gui_run( self, gui_context ):
        """This method is called in the *GUI thread* upon execution of the
        action step.  The return value of this method is the result of the
        :keyword:`yield` statement in the *model thread*.
        
        The default behavior of this method is to call the model_run generator
        in the *model thread* until it is finished.
        
        :param gui_context:  An object of type 
            :class:`camelot.admin.action.GuiContext`, which is the context 
            of this action available in the *GUI thread*.  What is in the 
            context depends on how the action was called.
        """
        runner = ActionRunner( self.model_run, gui_context )
        runner.exec_()
        
    def model_run( self, model_context = None ):
        """A generator that yields :class:`camelot.admin.action.ActionStep`
        objects.  This generator can be called in the *model thread*.
        
        :param context:  An object of type
            :class:`camelot.admin.action.ModelContext`, which is context 
            of this action available in the model_thread.  What is in the 
            context depends on how the action was called.
        """
        print 1
        yield
        print 2
