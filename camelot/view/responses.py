from dataclasses import dataclass
import json
import logging
import typing

from . import gui_naming_context
from .requests import SendActionResponse, ThrowActionException, CancelAction
from ..core.exception import CancelRequest, GuiException
from ..core.naming import CompositeName, NameNotFoundException
from ..core.serializable import NamedDataclassSerializable

LOGGER = logging.getLogger('camelot.view.responses')


@dataclass
class AbstractResponse(NamedDataclassSerializable):
    """
    Serialiazable Responses the model can send to the UI
    """

    @classmethod
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
            # @todo : to avoid a second raise of a cancelrequest, reset
            #         the dialog, this might hide the dialog, even if the
            #         cancel request is not accepted.
            progress_dialog.reset()
            raise CancelRequest()

    @classmethod
    def handle_serialized_response(cls, serialized_response, post_method):
        response_type_name, response_data = json.loads(serialized_response)
        response_type = NamedDataclassSerializable.get_cls_by_name(
            response_type_name
        )
        response_type.handle_response(response_data, post_method)

    @classmethod
    def handle_response(cls, response_data, post_method):
        pass

@dataclass
class Busy(AbstractResponse):

    busy: bool

    @classmethod
    def handle_response(cls, response_data, post_method):
        from .action_runner import action_runner
        action_runner.busy.emit(response_data['busy'])

@dataclass
class ActionStepped(AbstractResponse):

    run_name: CompositeName
    gui_run_name: CompositeName
    blocking: bool
    step: NamedDataclassSerializable
    
    @classmethod
    def handle_response(cls, response_data, post_method):
        gui_run_name = tuple(response_data['gui_run_name'])
        run_name = tuple(response_data['run_name'])
        step_type, step = response_data['step']
        gui_run = gui_naming_context.resolve(gui_run_name)
        LOGGER.debug('{0} for action {1.action_name}'.format(step_type, gui_run))
        try:
            serialized_step = json.dumps(step).encode()
            cls._was_canceled(gui_run.gui_context_name)
            to_send = gui_run.handle_serialized_action_step(step_type, serialized_step)
            if response_data['blocking']==True:
                post_method(SendActionResponse(run_name=run_name, response=to_send))
        except CancelRequest:
            LOGGER.debug( 'non blocking action step requests cancel, set flag' )
            post_method(CancelAction(run_name=run_name))
        except Exception as exc:
            LOGGER.error('gui exception while executing action', exc_info=exc)
            # In case of an exception in the GUI thread, propagate an
            # exception to make sure the generator ends.  Don't propagate
            # the very same exception, because no references from the GUI
            # should be passed to the model.
            post_method(ThrowActionException(
                run_name=run_name, exception=GuiException.__name__
            ))


@dataclass
class ActionStopped(AbstractResponse):

    run_name: CompositeName
    gui_run_name: CompositeName
    exception: typing.Any

    @classmethod
    def handle_response(cls, response_data, post_method):
        gui_run_name = tuple(response_data['gui_run_name'])
        try:
            gui_run = gui_naming_context.resolve(gui_run_name)
            gui_naming_context.unbind(gui_run_name)
            action_name = gui_run.action_name
            time_running = gui_run.time_running()
        except NameNotFoundException:
            LOGGER.error('Could not unbind gui_run {}'.format(gui_run_name))
            action_name = 'unknown action'
            time_running = 'unknown'
        exception = response_data.get('exception')
        if exception:
            LOGGER.error('Stop {0} with exception {1}'.format(action_name, exception))
        else:
            LOGGER.debug('Stop {0}, took {1}'.format(action_name, time_running))
