import json
import logging
import multiprocessing as _mp
import collections

from ..core.backend import get_root_backend
from ..core.qt import QtCore
from ..core.serializable import DataclassSerializable
from .responses import ActionStepped, Busy
from .requests import StopProcess, AbstractRequest, CancelAction

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

    # FIXME: remove this
    def has_cancel_request(self):
        return False


class ModelProcess(spawned_mp.Process):

    def __init__(self):
        super().__init__()
        self._process_queue = spawned_mp.JoinableQueue()
        self._request_queue = collections.deque()
        self._response_receiver, self._response_sender = spawned_mp.Pipe(duplex=False)
        self.socket_notifier = QtCore.QSocketNotifier(
            self._response_receiver.fileno(), QtCore.QSocketNotifier.Type.Read
        )
        self.socket_notifier.activated.connect(self._response_socket_notice)

    def _response_socket_notice(self, socket):
        if self._response_receiver.poll():
            serialized_response = QtCore.QByteArray(
                self._response_receiver.recv_bytes()
            )
            root_backend = get_root_backend()
            root_backend.action_runner().onResponse(serialized_response)

    def __getstate__(self):
        state = self.__dict__.copy()
        state.pop('socket_notifier')
        state.pop('_response_receiver')
        return state

    def start(self):
        rb = get_root_backend()
        rb.action_runner().request.connect(self.post)
        rb.stop.connect(self.stop)
        super().start()

    def initialize(self):
        """
        Overwrite this method in subclasses to initialize a process when it
        starts running.
        """
        pass

    def transfer_queue(self, request=None):

        def append_request(req):
            self._process_queue.task_done()
            self._request_queue.append(json.loads(req))

        if request is not None:
            append_request(request)
        while not self._process_queue.empty():
            req = self._process_queue.get()
            append_request(req)

    def has_cancel_request(self):

        def is_cancel_request(request):
            return request[0] == 'CancelAction'

        self.transfer_queue()
        for request in self._request_queue:
            if is_cancel_request(request):
                LOGGER.info('Found CancelAction in request queue')
                # remove CancelAction request from queue
                self._request_queue = collections.deque([r for r in self._request_queue if not is_cancel_request(r)])
                return True
        return False

    def run(self):
        LOGGER = logging.getLogger("model_process")
        self.initialize()
        response_handler = PipeResponseHandler(self._response_sender)
        while True:
            response_handler.send_response(Busy(False))
            request = self._process_queue.get()
            self.transfer_queue(request)
            request = self._request_queue.popleft()
            response_handler.send_response(Busy(True))
            try:
                AbstractRequest.handle_request(
                    request, response_handler, self
                )
            except Exception as e:
                LOGGER.error('Unhandled exception in model process', exc_info=e)
                import traceback
                traceback.print_exc()
            except SystemExit:
                LOGGER.info('Terminating')
                raise
            except:
                LOGGER.error('Unhandled event in model process')
        LOGGER.info("Terminated")

    def post(self, request):
        if self._process_queue is None:
            LOGGER.error('Request posted to no longer running process {}'.format(request.data()))
            raise Exception('Process no longer running')
        self._process_queue.put(request.data())
        return ['process', str(self.pid)]

    def stop(self):
        """
        Request the worker to finish its ongoing tasks and stop
        """
        get_root_backend().action_runner().request.disconnect(self.post)
        # make sure no messages can be send to the request queue, after
        # the stop_request was send
        process_queue = self._process_queue
        self._process_queue = None
        process_queue.put(stop_request._to_bytes())
        self.join()
        # as per Qt documentation, explicit disabling of the notifier is advised
        self.socket_notifier.setEnabled(False)
