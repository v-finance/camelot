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

import contextlib
import io
import json
import logging
import time
import typing

from ..core.naming import (
    initial_naming_context, CompositeName, NameNotFoundException
)
from ..core.serializable import DataclassSerializable, json_encoder
from ..core.qt import QtCore, QtGui, is_deleted
from . import gui_naming_context
from camelot.admin.action import ActionStep
from camelot.admin.action.base import MetaActionStep
from camelot.core.exception import GuiException, CancelRequest
from camelot.core.singleton import QSingleton
from camelot.view.model_thread import post

LOGGER = logging.getLogger('camelot.view.action_runner')
REQUEST_LOGGER = logging.getLogger('camelot.view.action_runner.request')

@contextlib.contextmanager
def hide_progress_dialog(gui_context_name):
    """A context manager to hide the progress dialog of the gui context when
    the context is entered, and restore the original state at exit"""
    from .qml_view import is_cpp_gui_context_name
    progress_dialog = None
    if not is_cpp_gui_context_name(gui_context_name):
        gui_context = gui_naming_context.resolve(gui_context_name)
        if gui_context is not None:
            progress_dialog = gui_context.get_progress_dialog()
    if progress_dialog is None:
        yield
        return
    original_state, original_minimum_duration = None, None
    original_state = progress_dialog.isHidden()
    original_minimum_duration = progress_dialog.minimumDuration()
    try:
        progress_dialog.setMinimumDuration(0)
        if original_state == False:
            progress_dialog.hide()
        yield
    finally:
        if not is_deleted(progress_dialog):
            progress_dialog.setMinimumDuration(original_minimum_duration)
            if original_state == False:
                progress_dialog.show()

model_run_names = initial_naming_context.bind_new_context('model_run')
gui_run_names = gui_naming_context.bind_new_context('gui_run')

class ModelRun(object):
    """
    Server side information of an ongoing action run
    """

    def __init__(self, gui_run_name: CompositeName, generator):
        self.gui_run_name = gui_run_name
        self.generator = generator
        self.cancel = False

class GuiRun(object):
    """
    Client side information and statistics of an ongoing action run
    """

    def __init__(
        self,
        gui_context_name: CompositeName,
        action_name: CompositeName,
        model_context_name: CompositeName,
        mode
        ):
        self.gui_context_name = gui_context_name
        self.action_name = action_name
        self.model_context_name = model_context_name
        self.mode = mode
        self.started_at = time.time()
        self.steps = []

    @property
    def step_count(self):
        return len(self.steps)

    def time_running(self):
        """
        :return: the time the action has been running
        """
        return time.time() - self.started_at

    def handle_action_step(self, action_step):
        from .qml_view import is_cpp_gui_context_name, qml_action_step
        self.steps.append(type(action_step).__name__)
        # dispatch to RootBackend if this is a cpp gui context
        if is_cpp_gui_context_name(self.gui_context_name) and action_step.blocking==False:
            # FIXME: step is not (yet) serializable, use _to_dict for now
            stream = io.BytesIO()
            stream.write(json_encoder.encode(action_step._to_dict()).encode())
            serialized_step = stream.getvalue()
            return qml_action_step(
                self.gui_context_name, type(action_step).__name__, serialized_step
            )
        return action_step.gui_run(self.gui_context_name)

    def handle_serialized_action_step(self, step_type, serialized_step):
        from .qml_view import is_cpp_gui_context_name, qml_action_step
        self.steps.append(step_type)
        cls = MetaActionStep.action_steps[step_type]
        if cls.blocking==True:
            app = QtGui.QGuiApplication.instance()
            if app.platformName() == "offscreen":
                # When running tests in offscreen mode, print the exception and exit with -1 status
                print("Blocking action step occurred while executing an action:")
                print()
                print("======================================================================")
                print()
                print("Type: {}".format(step_type))
                print("Detail: {}".format(serialized_step))
                print()
                print("======================================================================")
                print()
                app.exit(-1)
        if is_cpp_gui_context_name(self.gui_context_name) and cls.blocking==False:
            result = qml_action_step(
                self.gui_context_name, step_type, serialized_step
            )
        else:
            result = cls.gui_run(self.gui_context_name, serialized_step)
        return cls.deserialize_result(self.gui_context_name, result)

class ActionRunner(QtCore.QObject, metaclass=QSingleton):
    """Helper class for handling the signals and slots when an action
    is running.  This class takes a generator and iterates it within the
    model thread while taking care of Exceptions raised and ActionSteps
    yielded by the generator.
    
    This is class is intended for internal Camelot use only.
    """
    
    non_blocking_action_step_signal = QtCore.qt_signal(tuple, tuple, object)
    non_blocking_serializable_action_step_signal = QtCore.qt_signal(tuple, tuple, str, bytes)
    
    def __init__(self):
        super().__init__()
        self.non_blocking_action_step_signal.connect(self.non_blocking_action_step)
        self.non_blocking_serializable_action_step_signal.connect(self.non_blocking_serializable_action_step)

    @classmethod
    def wait_for_completion(cls, max_wait=5):
        """
        Wait until all actions are completed

        :param max_wait: maximum time to wait for an action to complete
        """
        actions_running = True
        while actions_running:
            run_names = list(gui_run_names.list())
            actions_running = len(run_names) > 0
            if actions_running:
                LOGGER.info('{} actions running'.format(len(run_names)))
                for run_name in run_names:
                    run = gui_run_names.resolve(run_name)
                    LOGGER.info('{} : {}'.format(run_name, run.action_name))
                    LOGGER.info('  Generated {} steps during {} seconds'.format(run.step_count, run.time_running()))
                    LOGGER.info('  Steps : {}'.format(run.steps))
                    if run.time_running() >= max_wait:
                        raise Exception('Action running for more then {} seconds'.format(max_wait))
            QtCore.QCoreApplication.instance().processEvents()
            time.sleep(0.1)

    def run_action(self,
        action_name: CompositeName,
        gui_context: CompositeName,
        model_context: CompositeName,
        mode: typing.Union[str, dict, list, int]
    ):
        gui_run = GuiRun(gui_context, action_name, model_context, mode)
        self.run_gui_run(gui_run)

    def run_gui_run(self, gui_run):
        gui_naming_context.validate_composite_name(gui_run.gui_context_name)
        assert gui_run.gui_context_name != ('constant', 'null')
        gui_run_name = gui_run_names.bind(str(id(gui_run)), gui_run)
        message = {
            'action_name': gui_run.action_name,
            'model_context': gui_run.model_context_name,
            'gui_run_name': gui_run_name,
            'mode': gui_run.mode,
        }
        serialized_message = json_encoder.encode(message)
        if REQUEST_LOGGER.isEnabledFor(logging.DEBUG):
            REQUEST_LOGGER.debug(serialized_message)
        post(self._initiate_generator, self.generator, args=(serialized_message,))

    def _initiate_generator(self, serialized_message):
        """Create the model context and start the generator"""
        from camelot.view.action_steps import PushProgressLevel, MessageBox
        message = json.loads(serialized_message)
        LOGGER.debug('Iniate run of action {}'.format(message['action_name']))
        action = initial_naming_context.resolve(tuple(message['action_name']))
        gui_run_name = tuple(message['gui_run_name'])
        try:
            model_context = initial_naming_context.resolve(tuple(message['model_context']))
        except NameNotFoundException:
            LOGGER.error('Could not create model context, no binding for name: {}'.format(message['model_context']))
            return
        try:
            generator = action.model_run(model_context, message.get('mode'))
        except Exception as exception:
            self.non_blocking_serializable_action_step_signal.emit(
                ('constant', 'null'), gui_run_name, MessageBox.__name__,
                MessageBox.from_exception(
                    LOGGER,
                    'Exception caught in {}'.format(type(action).__name__),
                    exception
                )._to_bytes()
            )
            return None
        if generator is None:
            return None
        run = ModelRun(gui_run_name, generator)
        run_name = model_run_names.bind(str(id(run)), run)
        self.non_blocking_serializable_action_step_signal.emit(
            run_name, gui_run_name, "PushProgressLevel",
            PushProgressLevel('Please wait')._to_bytes()
        )
        LOGGER.debug('Action {} runs in generator {}'.format(message['action_name'], run_name))
        return run_name


    def _iterate_until_blocking(self, run_name, method, *args):
        """Helper calling for generator methods.  The decorated method iterates
        the generator until the generator yields an :class:`ActionStep` object that
        is blocking.  If a non blocking :class:`ActionStep` object is yielded, then
        send it to the GUI thread for execution through the signal slot mechanism.
        
        :param generator_method: the method of the generator to be called
        :param *args: the arguments to use when calling the generator method.
        """
        from camelot.view.action_steps import MessageBox
        run = initial_naming_context.resolve(run_name)
        gui_run_name = run.gui_run_name
        try:
            if method == 'send':
                result = run.generator.send(*args)
            elif method == 'throw':
                result = run.generator.throw(*args)
            else:
                raise Exception('Unhandled method')
            while True:
                if isinstance(result, ActionStep):
                    if result.blocking and isinstance(result, (DataclassSerializable,)):
                        LOGGER.debug( 'serializable blocking step, yield it' )
                        return (run_name, gui_run_name, (type(result).__name__, result._to_bytes()))
                    elif result.blocking:
                        LOGGER.debug( 'blocking step, yield it' )
                        return (run_name, gui_run_name, result)
                    # for now, only send data class serializable steps over the wire
                    elif isinstance(result, (DataclassSerializable,)):
                        LOGGER.debug( 'non blocking serializable step, use signal slot' )
                        self.non_blocking_serializable_action_step_signal.emit(
                            run_name, gui_run_name, type(result).__name__,
                            result._to_bytes()
                        )
                    else:
                        LOGGER.debug( 'non blocking step, use signal slot' )
                        self.non_blocking_action_step_signal.emit(
                            run_name, gui_run_name, result
                        )
                #
                # Cancel requests can arrive asynchronously through non 
                # blocking ActionSteps such as UpdateProgress
                #
                if run.cancel == True:
                    LOGGER.debug( 'asynchronous cancel, raise request' )
                    result = run.generator.throw(CancelRequest())
                else:
                    LOGGER.debug( 'move iterator forward' )
                    result = next(run.generator)
        except CancelRequest as e:
            LOGGER.debug( 'iterator raised cancel request, pass it' )
            self.non_blocking_serializable_action_step_signal.emit(
                run_name, gui_run_name, "PopProgressLevel", b"null"
            )
            return (run_name, gui_run_name, e)
        except StopIteration as e:
            LOGGER.debug( 'iterator raised stop, pass it' )
            self.non_blocking_serializable_action_step_signal.emit(
                run_name, gui_run_name, "PopProgressLevel", b"null"
            )
            initial_naming_context.unbind(run_name)
            return (run_name, gui_run_name, e)
        except Exception as e:
            self.non_blocking_serializable_action_step_signal.emit(
                ('constant', 'null'), gui_run_name, MessageBox.__name__,
                MessageBox.from_exception(
                    LOGGER,
                    'Exception caught',
                    e
                )._to_bytes()
            )
            LOGGER.debug( 'iterator raised stop, pass it' )
            self.non_blocking_serializable_action_step_signal.emit(
                run_name, gui_run_name, "PopProgressLevel", b"null"
            )
            initial_naming_context.unbind(run_name)
            return (run_name, gui_run_name, e)

    @QtCore.qt_slot(tuple, tuple, object)
    def non_blocking_action_step(self, run_name, gui_run_name, action_step ):
        gui_run = gui_naming_context.resolve(gui_run_name)
        try:
            self._was_canceled(gui_run.gui_context_name)
            return gui_run.handle_action_step(action_step)
        except CancelRequest:
            LOGGER.debug( 'non blocking action step requests cancel, set flag' )
            post(self.request_cancel, args=(run_name,))

    @QtCore.qt_slot(tuple, tuple, str, bytes)
    def non_blocking_serializable_action_step(self, run_name, gui_run_name, step_type, serialized_step):
        gui_run = gui_naming_context.resolve(gui_run_name)
        try:
            self._was_canceled(gui_run.gui_context_name)
            return gui_run.handle_serialized_action_step(step_type, serialized_step)
        except CancelRequest:
            LOGGER.debug( 'non blocking action step requests cancel, set flag' )
            post(self.request_cancel, args=(run_name,))

    @QtCore.qt_slot(tuple)
    def generator(self, run_name):
        """Handle the creation of the generator"""
        #
        # when model_run is not a generator, but a normal function it returns
        # no generator, and as such we can exit the event loop
        #
        if run_name is not None:
            post( self._iterate_until_blocking, 
                  self.__next__, 
                  args = (run_name, 'send', None) )

    def _was_canceled(self, gui_context_name):
        """raise a :class:`camelot.core.exception.CancelRequest` if the
        user pressed the cancel button of the progress dialog in the
        gui_context.
        """
        from .qml_view import is_cpp_gui_context_name
        if is_cpp_gui_context_name(gui_context_name):
            # @TODO : check was canceled for cpp
            return False
        else:
            try:
                gui_context = gui_naming_context.resolve(gui_context_name)
            except NameNotFoundException:
                return False
            assert gui_context, '{} python gui context resolves to none'.format(gui_context_name)
            progress_dialog = gui_context.get_progress_dialog()
            if (progress_dialog is not None) and (progress_dialog.wasCanceled()):
                LOGGER.debug( 'progress dialog was canceled, raise request' )
                raise CancelRequest()

    @QtCore.qt_slot(object)
    def __next__(self, run_yielded):
        """Handle the result of the __next__ call of the generator
        
        :param yielded: the object that was yielded by the generator in the
            *model thread*
        """
        run_name, gui_run_name, yielded = run_yielded
        gui_run = gui_naming_context.resolve(gui_run_name)
        gui_context_name = gui_run.gui_context_name

        if isinstance(yielded, (ActionStep, tuple)):
            try:
                self._was_canceled(gui_context_name)
                if isinstance(yielded, tuple):
                    step_type, serialized_step = yielded
                    to_send = gui_run.handle_serialized_action_step(step_type, serialized_step)
                else:
                    to_send = gui_run.handle_action_step(yielded)
                self._was_canceled(gui_context_name)
                post( self._iterate_until_blocking, 
                      self.__next__, 
                      args = (run_name, 'send', to_send,) )
            except CancelRequest as exc:
                post( self._iterate_until_blocking,
                      self.__next__,
                      args = (run_name, 'throw', exc,) )
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
                      args = (run_name, 'throw', GuiException(),) )
        elif isinstance( yielded, (StopIteration, CancelRequest, Exception) ):
            try:
                gui_naming_context.unbind(gui_run_name)
            except NameNotFoundException:
                LOGGER.error('Could not unbind gui_run {}'.format(gui_run_name))
        else:
            LOGGER.error( '__next__ call of generator returned an unexpected object of type %s'%( yielded.__class__.__name__ ) ) 
            LOGGER.error( str( yielded ) )
            raise Exception( 'this should not happen' )

action_runner = ActionRunner()