from dataclasses import dataclass
import json
import logging
import typing

from ..core.exception import CancelRequest
from ..core.naming import (
    CompositeName, NamingException, NameNotFoundException, initial_naming_context
)
from ..core.serializable import NamedDataclassSerializable, Serializable

LOGGER = logging.getLogger('camelot.view.requests')

class ModelRun(object):
    """
    Server side information of an ongoing action run
    """

    def __init__(self, gui_run_name: CompositeName, generator):
        self.gui_run_name = gui_run_name
        self.generator = generator
        self.cancel = False
        self.last_step = None

model_run_names = initial_naming_context.bind_new_context('model_run')

class AbstractRequest(NamedDataclassSerializable):
    """
    Serialiazable Requests the UI can send to the model
    """

    @classmethod
    def handle_request(cls, request, response_handler, cancel_handler):
        request_type_name, request_data = json.loads(request)
        request_type = NamedDataclassSerializable.get_cls_by_name(
            request_type_name
        )
        request_type.execute(request_data, response_handler, cancel_handler)

    @classmethod
    def execute(cls, request_data, response_handler, cancel_handler):
        cls._iterate_until_blocking(
            request_data, response_handler, cancel_handler
        )

    @classmethod
    def _next(cls, run, request_data):
        return None

    @classmethod
    def _stop_action(cls, run_name, gui_run_name, response_handler, e):
        from .action_steps import PopProgressLevel
        from .responses import ActionStopped, ActionStepped
        response_handler.send_response(ActionStepped(
            run_name=run_name, gui_run_name=gui_run_name, blocking=False,
            step=(PopProgressLevel.__name__, PopProgressLevel())
        ))
        if run_name != ('constant', 'null'):
            initial_naming_context.unbind(run_name)
        response_handler.send_response(ActionStopped(
            run_name=run_name, gui_run_name=gui_run_name, exception=str(e)
        ))

    @classmethod
    def _send_stop_message(cls, run_name, gui_run_name, response_handler, e):
        from .responses import ActionStepped
        from .action_steps import MessageBox
        response_handler.send_response(ActionStepped(
            run_name=run_name, gui_run_name=gui_run_name, blocking=False,
            step=(MessageBox.__name__, MessageBox.from_exception(
                LOGGER,
                'Unhandled exception caught : {}'.format(type(e).__name__),
                e
            ))
        ))
        cls._stop_action(run_name, gui_run_name, response_handler, e)

    @classmethod
    def _iterate_until_blocking(cls, request_data, response_handler, cancel_handler):
        """Helper calling for generator methods.  The decorated method iterates
        the generator until the generator yields an :class:`ActionStep` object that
        is blocking.  If a non blocking :class:`ActionStep` object is yielded, then
        send it to the GUI thread for execution through the signal slot mechanism.
        
        :param generator_method: the method of the generator to be called
        :param *args: the arguments to use when calling the generator method.
        """
        from ..admin.action import ActionStep
        from .responses import ActionStepped
        try:
            run_name = tuple(request_data['run_name'])
            run = initial_naming_context.resolve(run_name)
        except NameNotFoundException:
            LOGGER.error('Run name not found : {} for request {}'.format(run_name, request_data))
            return
        gui_run_name = run.gui_run_name
        try:
            result = cls._next(run, request_data)
            while True:
                if isinstance(result, ActionStep):
                    run.last_step = result
                    response_handler.send_response(ActionStepped(
                        run_name=run_name, gui_run_name=gui_run_name,
                        step=(type(result).__name__, result),
                        blocking=result.blocking,
                    ))
                    if result.blocking:
                        # this step is blocking, interrupt the loop
                        return
                #
                # Cancel requests can arrive asynchronously through non 
                # blocking ActionSteps such as UpdateProgress
                #
                if cancel_handler.has_cancel_request():
                    LOGGER.debug( 'asynchronous cancel, raise request' )
                    result = run.generator.throw(CancelRequest())
                else:
                    result = next(run.generator)
        except CancelRequest as e:
            LOGGER.debug( 'iterator raised cancel request, pass it' )
            cls._stop_action(run_name, gui_run_name, response_handler, e)
        except StopIteration as e:
            cls._stop_action(run_name, gui_run_name, response_handler, e)
        except Exception as e:
            cls._send_stop_message(
                ('constant', 'null'), gui_run_name, response_handler, e
            )

@dataclass
class InitiateAction(AbstractRequest):
    """
    Initiate a new run of an action, the run is uniquely identified on the
    client side by its gui_run_name
    """
    gui_run_name: CompositeName
    action_name: CompositeName
    model_context: CompositeName
    mode: typing.Union[str, dict, list, int]

    @classmethod
    def execute(cls, request_data, response_handler, cancel_handler):
        from .action_steps import PushProgressLevel
        from .responses import ActionStopped, ActionStepped
        gui_run_name = tuple(request_data['gui_run_name'])
        LOGGER.debug('Run of action {} with mode {}'.format(request_data['action_name'], request_data['mode']))
        try:
            action = initial_naming_context.resolve(tuple(request_data['action_name']))
            model_context = initial_naming_context.resolve(tuple(request_data['model_context']))
        except (NamingException, NameNotFoundException) as e:
            if isinstance(e, NamingException):
                LOGGER.error('Could not resolve action from gui_run {}, invalid name: {}'.format(
                    gui_run_name, e.message_text
                ))
            else:
                LOGGER.error('Could not resolve action from gui_run {}, no binding for name: {}'.format(
                    gui_run_name, e.name
                ))
            response_handler.send_response(ActionStopped(
                run_name=('constant', 'null'), gui_run_name=gui_run_name, exception=None
            ))
            return
        generator, exception = None, None
        try:
            generator = action.model_run(model_context, request_data.get('mode'))
        except Exception as exc:
            exception = str(exc)
        if generator is None:
            response_handler.send_response(ActionStopped(
                run_name=('constant', 'null'), gui_run_name=gui_run_name, exception=exception
            ))
            return
        run = ModelRun(gui_run_name, generator)
        run_name = model_run_names.bind(str(id(run)), run)
        response_handler.send_response(ActionStepped(
            run_name=run_name, gui_run_name=gui_run_name, blocking=False,
            step=(PushProgressLevel.__name__, PushProgressLevel('Please wait'))
        ))
        request_data["run_name"] = run_name
        LOGGER.debug('Action {} runs in generator {}'.format(request_data['action_name'], run_name))
        cls._iterate_until_blocking(
            request_data, response_handler, cancel_handler
        )

@dataclass
class SendActionResponse(AbstractRequest):
    """
    Send a response to a running action that is waiting for the response from
    the client.  The running action is uniquely identied on the server side
    by its run_name.
    """
    run_name: CompositeName
    response: Serializable

    @classmethod
    def _next(cls, run, request_data):
        response = run.last_step.deserialize_result(
            None, request_data['response']
        )
        return run.generator.send(response)

@dataclass
class ThrowActionException(AbstractRequest):
    """
    Raise an exception within an action that is waiting for the response
    from the client.  The running action is uniquely identied on the server side
    by its run_name.
    """
    run_name: CompositeName
    exception: Serializable

    @classmethod
    def _next(cls, run, request_data):
        return run.generator.throw(Exception(request_data['exception']))


@dataclass
class CancelAction(AbstractRequest):
    """
    Request an action run to be canceled, even if the action is not waiting
    for a response. The running action is uniquely identied on the server side
    by its run_name.
    """
    run_name: CompositeName

    @classmethod
    def _next(cls, run, request_data):
        return run.generator.throw(CancelRequest())

@dataclass
class StopProcess(AbstractRequest):
    """Sentinel task to end all tasks to be executed by a process"""
    pass
