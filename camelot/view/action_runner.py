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
import logging
import time
import typing

from ..core.naming import CompositeName, NameNotFoundException
from ..core.serializable import json_encoder
from ..core.qt import QtCore, QtGui, is_deleted
from . import gui_naming_context
from camelot.admin.action.base import MetaActionStep
from camelot.core.exception import GuiException, CancelRequest
from camelot.core.singleton import QSingleton
from camelot.view.model_thread import post
from .requests import InitiateAction, SendActionResponse, ThrowActionException

LOGGER = logging.getLogger('camelot.view.action_runner')

@contextlib.contextmanager
def hide_progress_dialog(gui_context_name):
    """A context manager to hide the progress dialog of the gui context when
    the context is entered, and restore the original state at exit"""
    from .qml_view import is_cpp_gui_context_name, qml_action_step
    progress_dialog = None
    if not is_cpp_gui_context_name(gui_context_name):
        gui_context = gui_naming_context.resolve(gui_context_name)
        if gui_context is not None:
            progress_dialog = gui_context.get_progress_dialog()
    if progress_dialog is None:
        is_hidden = None
        if is_cpp_gui_context_name(gui_context_name):
            response = qml_action_step(gui_context_name, 'GetProgressState')
            is_hidden = response["is_hidden"]
            if not is_hidden:
                qml_action_step(gui_context_name, 'HideProgress')
        yield
        if is_cpp_gui_context_name(gui_context_name):
            if not is_hidden:
                qml_action_step(gui_context_name, 'ShowProgress')
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

gui_run_names = gui_naming_context.bind_new_context('gui_run')

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
        from .action_steps.crud import crud_action_steps
        from .qml_view import is_cpp_gui_context_name, qml_action_step
        self.steps.append(type(action_step).__name__)
        # force crud actions steps with a cpp gui context towards qml
        if is_cpp_gui_context_name(self.gui_context_name) and isinstance(action_step, crud_action_steps):
            # FIXME: step is not (yet) serializable, use _to_dict for now
            stream = io.BytesIO()
            stream.write(json_encoder.encode(action_step._to_dict()).encode())
            serialized_step = stream.getvalue()
            return qml_action_step(
                self.gui_context_name, type(action_step).__name__, serialized_step
            )
        return action_step.gui_run(self.gui_context_name)

    def handle_serialized_action_step(self, step_type, serialized_step):
        from .action_steps.crud import crud_action_steps
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
        # force crud actions steps with a cpp gui context towards qml
        if is_cpp_gui_context_name(self.gui_context_name) and issubclass(cls, crud_action_steps):
            result = qml_action_step(
                self.gui_context_name, step_type, serialized_step
            )
        else:
            result = cls.gui_run(self.gui_context_name, serialized_step)
        return result

class ActionRunner(QtCore.QObject, metaclass=QSingleton):
    """Helper class for handling the signals and slots when an action
    is running.  This class takes a generator and iterates it within the
    model thread while taking care of Exceptions raised and ActionSteps
    yielded by the generator.
    
    This is class is intended for internal Camelot use only.
    """
    
    non_blocking_action_step_signal = QtCore.qt_signal(tuple, tuple, object)
    serializable_action_step_signal = QtCore.qt_signal(tuple, tuple, str, bool, bytes)
    action_stopped_signal = QtCore.qt_signal(tuple, tuple, object)

    def __init__(self):
        super().__init__()
        self.non_blocking_action_step_signal.connect(self.non_blocking_action_step)
        self.serializable_action_step_signal.connect(self.serializable_action_step)
        self.action_stopped_signal.connect(self.action_stopped)

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
            time.sleep(0.05)

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
        post(InitiateAction(
            gui_run_name = gui_run_names.bind(str(id(gui_run)), gui_run),
            action_name = gui_run.action_name,
            model_context = gui_run.model_context_name,
            mode = gui_run.mode,
        ))

    @QtCore.qt_slot(tuple, tuple, object)
    def non_blocking_action_step(self, run_name, gui_run_name, action_step ):
        gui_run = gui_naming_context.resolve(gui_run_name)
        try:
            self._was_canceled(gui_run.gui_context_name)
            return gui_run.handle_action_step(action_step)
        except CancelRequest:
            LOGGER.debug( 'non blocking action step requests cancel, set flag' )
            self._throw(run_name, CancelRequest())

    @QtCore.qt_slot(tuple, tuple, str, bool, bytes)
    def serializable_action_step(self, run_name, gui_run_name, step_type, blocking, serialized_step):
        gui_run = gui_naming_context.resolve(gui_run_name)
        try:
            self._was_canceled(gui_run.gui_context_name)
            to_send = gui_run.handle_serialized_action_step(step_type, serialized_step)
            if blocking==True:
                self._send(run_name, to_send)
        except CancelRequest:
            LOGGER.debug( 'non blocking action step requests cancel, set flag' )
            self._throw(run_name, CancelRequest())
        except Exception as exc:
            LOGGER.error('gui exception while executing action', exc_info=exc)
            # In case of an exception in the GUI thread, propagate an
            # exception to make sure the generator ends.  Don't propagate
            # the very same exception, because no references from the GUI
            # should be past to the model.
            self._throw(run_name, GuiException())

    @QtCore.qt_slot(tuple, tuple, object)
    def action_stopped(self, run_name, gui_run_name, exc):
        try:
            gui_naming_context.unbind(gui_run_name)
        except NameNotFoundException:
            LOGGER.error('Could not unbind gui_run {}'.format(gui_run_name))

    def _was_canceled(self, gui_context_name):
        """raise a :class:`camelot.core.exception.CancelRequest` if the
        user pressed the cancel button of the progress dialog in the
        gui_context.
        """
        from .qml_view import is_cpp_gui_context_name
        if is_cpp_gui_context_name(gui_context_name):
            # @TODO : check was canceled for cpp
            return
        try:
            gui_context = gui_naming_context.resolve(gui_context_name)
        except NameNotFoundException:
            return
        if gui_context is None:
            return
        progress_dialog = gui_context.get_progress_dialog()
        if (progress_dialog is not None) and (progress_dialog.wasCanceled()):
            LOGGER.debug( 'progress dialog was canceled, raise request' )
            raise CancelRequest()

    def _throw(self, run_name, exc):
        post(ThrowActionException(
            run_name=run_name, exception=type(exc).__name__
        ))

    def _send(self, run_name, to_send):
        post(SendActionResponse(run_name=run_name, response=to_send))


action_runner = ActionRunner()