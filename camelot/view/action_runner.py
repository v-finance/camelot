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

import contextlib
import functools
import logging

import six

from ..core.qt import QtCore, QtWidgets
from camelot.admin.action import ActionStep
from camelot.core.exception import GuiException, CancelRequest
from camelot.view.controls.exception import ExceptionDialog
from camelot.view.model_thread import post

LOGGER = logging.getLogger( 'camelot.view.action_runner' )

@contextlib.contextmanager
def hide_progress_dialog( gui_context ):
    """A context manager to hide the progress dialog of the gui context when
    the context is entered, and restore the original state at exit"""
    progress_dialog = gui_context.progress_dialog
    original_state = None
    if isinstance( progress_dialog, QtWidgets.QWidget ):
        original_state = progress_dialog.isHidden()
    try:
        if original_state == False:
            progress_dialog.hide()
        yield
    finally:
        if original_state == False:
            progress_dialog.show()

class ActionRunner( QtCore.QEventLoop ):
    """Helper class for handling the signals and slots when an action
    is running.  This class takes a generator and iterates it within the
    model thread while taking care of Exceptions raised and ActionSteps
    yielded by the generator.
    
    This is class is intended for internal Camelot use only.
    """
    
    non_blocking_action_step_signal = QtCore.qt_signal(object)
    
    def __init__( self, generator_function, gui_context ):
        """
        :param generator_function: function to be called in the model thread,
            that will return the generator
        :param gui_context: the GUI context of the generator
        """
        super( ActionRunner, self ).__init__()
        self._return_code = None
        self._generator_function = generator_function
        self._generator = None
        self._gui_context = gui_context
        self._model_context = gui_context.create_model_context()
        self._non_blocking_cancel_request = False
        self.non_blocking_action_step_signal.connect( self.non_blocking_action_step )
        post( self._initiate_generator, self.generator, self.exception )
    
    def exit( self, return_code = 0 ):
        """Reimplementation of exit to store the return code"""
        self._return_code = return_code
        return super( ActionRunner, self ).exit( return_code )
    
    def exec_( self, flags = QtCore.QEventLoop.AllEvents ):
        """Reimplementation of exec_ to prevent the event loop being started
        when exit has been called prior to calling exec_.
        
        This can be the case when running in single threaded mode.
        """
        if self._return_code == None:
            return super( ActionRunner, self ).exec_( flags )
        return self._return_code
        
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
        try:
            result = generator_method( *args )
            while True:
                if isinstance(result, ActionStep):
                    if result.blocking:
                        LOGGER.debug( 'blocking step, yield it' )
                        return result
                    else:
                        LOGGER.debug( 'non blocking step, use signal slot' )
                        self.non_blocking_action_step_signal.emit( result )
                #
                # Cancel requests can arrive asynchronously through non 
                # blocking ActionSteps such as UpdateProgress
                #
                if self._non_blocking_cancel_request == True:
                    LOGGER.debug( 'asynchronous cancel, raise request' )
                    result = self._generator.throw( CancelRequest() )
                else:
                    LOGGER.debug( 'move iterator forward' )
                    result = six.advance_iterator( self._generator )
        except CancelRequest as e:
            LOGGER.debug( 'iterator raised cancel request, pass it' )
            return e
        except StopIteration as e:
            LOGGER.debug( 'iterator raised stop, pass it' )
            return e

    @QtCore.qt_slot( object )
    def non_blocking_action_step( self, action_step ):
        try:
            self._was_canceled( self._gui_context )
            action_step.gui_run( self._gui_context )
        except CancelRequest:
            LOGGER.debug( 'non blocking action step requests cancel, set flag' )
            self._non_blocking_cancel_request = True
        
    @QtCore.qt_slot( object )
    def exception( self, exception_info ):
        """Handle an exception raised by the generator"""
        dialog = ExceptionDialog( exception_info )
        dialog.exec_()
        self.exit()
        
    @QtCore.qt_slot( object )
    def generator( self, generator ):
        """Handle the creation of the generator"""
        self._generator = generator
        #
        # when model_run is not a generator, but a normal function it returns
        # no generator, and as such we can exit the event loop
        #
        if self._generator != None:
            post( self._iterate_until_blocking, 
                  self.__next__, 
                  self.exception,
                  args = ( functools.partial( six.advance_iterator,
                                              self._generator ), ) )
        else:
            self.exit()
        
    def _was_canceled( self, gui_context ):
        """raise a :class:`camelot.core.exception.CancelRequest` if the
        user pressed the cancel button of the progress dialog in the
        gui_context.
        """
        if gui_context.progress_dialog:
            if gui_context.progress_dialog.wasCanceled():
                LOGGER.debug( 'progress dialog was canceled, raise request' )
                raise CancelRequest()
            
    @QtCore.qt_slot( object )
    def __next__( self, yielded ):
        """Handle the result of the __next__ call of the generator
        
        :param yielded: the object that was yielded by the generator in the
            *model thread*
        """
        if isinstance( yielded, ActionStep ):
            try:
                self._was_canceled( self._gui_context )
                to_send = yielded.gui_run( self._gui_context )
                self._was_canceled( self._gui_context )
                post( self._iterate_until_blocking, 
                      self.__next__, 
                      self.exception, 
                      args = ( self._generator.send, to_send,) )
            except CancelRequest as exc:
                post( self._iterate_until_blocking,
                      self.__next__,
                      self.exception,
                      args = ( self._generator.throw, exc,) )
            except Exception as exc:
                LOGGER.error( 'gui exception while executing action', 
                              exc_info=exc)
                #
                # In case of an exception in the GUI thread, propagate an
                # exception to make sure the generator ends.  Don't propagate
                # the very same exception, because no references from the GUI
                # should be past to the model.
                #
                post( self._iterate_until_blocking,
                      self.__next__,
                      self.exception,
                      args = ( self._generator.throw, GuiException(), ) )
        elif isinstance( yielded, (StopIteration, CancelRequest) ):
            #
            # Process the events before exiting, as there might be exceptions
            # left in the signal slot queue
            #
            self.processEvents()
            self.exit()
        else:
            LOGGER.error( '__next__ call of generator returned an unexpected object of type %s'%( yielded.__class__.__name__ ) ) 
            LOGGER.error( six.text_type( yielded ) )
            raise Exception( 'this should not happen' )


