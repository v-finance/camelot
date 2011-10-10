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

import logging

from PyQt4 import QtCore

from camelot.admin.action import ActionStep
from camelot.core.exception import GuiException, CancelRequest
from camelot.view.model_thread import post

LOGGER = logging.getLogger( 'camelot.view.action_runner' )

class ActionRunner( QtCore.QEventLoop ):
    """Helper class for handling the signals and slots when an action
    is running.  This class takes a generator and iterates it within the
    model thread while taking care of Exceptions raised and ActionSteps
    yielded by the generator.
    
    This is class is intended for internal Camelot use only.
    """
    
    non_blocking_action_step_signal = QtCore.pyqtSignal(object)
    
    def __init__( self, generator_function, gui_context, model_context ):
        """
        :param generator_function: function to be called in the model thread,
            that will return the generator
        :param gui_context: the GUI context of the generator
        """
        super( ActionRunner, self ).__init__()
        self._generator_function = generator_function
        self._generator = None
        self._gui_context = gui_context
        self._model_context = gui_context.create_model_context()
        self.non_blocking_action_step_signal.connect( self.non_blocking_action_step )
        post( self._initiate_generator, self.generator, self.exception )
    
    def _initiate_generator( self ):
        """Create the model context and start the generator"""
        return self._generator_function( self._model_context )
            
    def _iterate_until_blocking( self, generator_method, *args ):
        """Helper calling for generator methods.  The decorated method iterates
        the generator until the generator yields an :class:`ActionStep` object that
        is blocking.  If a non blocking :class:`ActionStep` object is yielded, then
        send it to the GUI thread for execution through the signal slot mechanism.
        
        :param generator_method: the method of the generator to be called
        :param *args: the arguments to use when calling the generator method.
        """
        result = None
        try:
            result = generator_method( *args )
        except CancelRequest:
            pass
        while True:
            if isinstance( result, (ActionStep,)):
                if result.blocking:
                    return result
                else:
                    self.non_blocking_action_step_signal.emit( result )
            result = self._generator.next()

    @QtCore.pyqtSlot( object )
    def non_blocking_action_step( self, action_step ):
        action_step.gui_run( self._gui_context )
        
    @QtCore.pyqtSlot( object )
    def exception( self, exception_info ):
        """Handle an exception raised by the generator"""
        from camelot.view.controls.exception import model_thread_exception_message_box
        model_thread_exception_message_box( exception_info )
        self.exit()
        
    @QtCore.pyqtSlot( object )
    def generator( self, generator ):
        """Handle the creation of the generator"""
        self._generator = generator
        #
        # when model_run is not a generator, but a normal function it returns
        # no generator
        #
        if self._generator != None:
            post( self._iterate_until_blocking, 
                  self.next, 
                  self.exception,
                  args = ( self._generator.next, ) )
        
    @QtCore.pyqtSlot( object )
    def next( self, yielded ):
        """Handle the result of the next call of the generator
        
        :param yielded: the object that was yielded by the generator in the
            *model thread*
        """
        if isinstance( yielded, (ActionStep,) ):
            try:
                to_send = yielded.gui_run( self._gui_context )
                post( self._iterate_until_blocking, 
                      self.next, 
                      self.exception, 
                      args = ( self._generator.send, to_send,) )
            except CancelRequest, exc:
                post( self._iterate_until_blocking,
                      self.next,
                      self.exception,
                      args = ( self._generator.throw, exc,) )
            except Exception, exc:
                LOGGER.error( 'gui exception while executing action', 
                              exc_info=exc)
                #
                # In case of an exception in the GUI thread, propagate an
                # exception to make sure the generator ends.  Don't propagate
                # the very same exception, because no references from the GUI
                # should be past to the model.
                #
                post( self._iterate_until_blocking,
                      self.next,
                      self.exception,
                      args = ( self._generator.throw, GuiException(), ) )
        elif isinstance( yielded, (StopIteration,) ):
             #
             # Process the events before exiting, as there might be exceptions
             # left in the signal slot queue
             #
            self.processEvents()
            self.exit()
        else:
            raise Exception( 'this should not happen' )
