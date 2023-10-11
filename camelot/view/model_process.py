import json
import logging
import multiprocessing as _mp

from ..core.qt import QtCore
from ..core.serializable import NamedDataclassSerializable, DataclassSerializable
from ..core.naming import initial_naming_context
from .responses import AbstractResponse, ActionStepped, Busy
from .requests import StopProcess

LOGGER = logging.getLogger(__name__)

stop_request = StopProcess()
# force spawn based multiprocessing to enforce no implicit state at the
# moment the process forks
spawned_mp = _mp.get_context('spawn')

class PipeResponseHandler(object):
    """
    Response handler that sends responses through a pipe
    """

    def __init__(self, response_connection):
        self._response_connection = response_connection

    def send_response(self, response):
        if isinstance(response, (ActionStepped,)) and not isinstance(response.step[1], (DataclassSerializable,)):
            response.step = (response.step[0], response.step[1]._to_dict())
        self._response_connection.send_bytes(response._to_bytes())

    def has_cancel_request(self):
        return False


class ModelProcess(spawned_mp.Process):

    def __init__(self, context_name, context):
        super().__init__()
        self._request_queue = spawned_mp.JoinableQueue()
        self._response_receiver, self._response_sender = spawned_mp.Pipe(duplex=False)
        self._context_name = context_name
        self._context = context
        self.socket_notifier = QtCore.QSocketNotifier(
            self._response_receiver.fileno(), QtCore.QSocketNotifier.Type.Read
        )
        self.socket_notifier.activated.connect(self._response_socket_notice)

    def _response_socket_notice(self, socket):
        if self._response_receiver.poll():
            serialized_response = self._response_receiver.recv_bytes()
            AbstractResponse.handle_serialized_response(serialized_response, self.post)

    def __getstate__(self):
        state = self.__dict__.copy()
        state.pop('socket_notifier')
        state.pop('_response_receiver')
        return state

    def run(self):
        LOGGER = logging.getLogger("model_process")
        # begin dirty hack to make sure the unbind action is available,
        # todo is to find a proper solution for setting up the initial naming
        # context when starting a new process.
        from ..admin.action.application_action import application_action_context
        assert application_action_context.resolve('unbind')
        # end of dirty hack
        initial_naming_context.bind(self._context_name, self._context)
        response_handler = PipeResponseHandler(self._response_sender)
        while True:
            response_handler.send_response(Busy(False))
            request = self._request_queue.get()
            response_handler.send_response(Busy(True))
            try:
                request_type_name, request_data = json.loads(request)
                request_type = NamedDataclassSerializable.get_cls_by_name(
                    request_type_name
                )
                if request_type == StopProcess:
                    break
                request_type.execute(request_data, response_handler, response_handler)
            except Exception as e:
                LOGGER.error('Unhandled exception in model process', exc_info=e)
                import traceback
                traceback.print_exc()
            except:
                LOGGER.error('Unhandled event in model process')
            finally:
                self._request_queue.task_done()
        LOGGER.info("Terminated")

    def post(self, request):
        if self._request_queue is None:
            LOGGER.error('Request posted to no longer running process {}'.format(request))
            raise Exception('Process no longer running')
        self._request_queue.put(request._to_bytes())
        return ['process', str(self.pid)]

    def stop(self):
        """
        Request the worker to finish its ongoing tasks and stop
        """
        # make sure no messages can be send to the request queue, after
        # the stop_request was send
        request_queue = self._request_queue
        self._request_queue = None
        request_queue.put(stop_request._to_bytes())
        self.join()
        # as per Qt documentation, explicit disabling of the notifier is advised
        self.socket_notifier.setEnabled(False)
