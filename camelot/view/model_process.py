import logging
from multiprocessing import connection
import multiprocessing as _mp

from ..core.backend import get_root_backend
from ..core.qt import QtCore
from ..core.serializable import DataclassSerializable
from .responses import ActionStepped, Busy
from .requests import StopProcess, AbstractRequest

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

    def __init__(self):
        super().__init__()
        self._request_queue = spawned_mp.JoinableQueue()
        self.listener = connection.Listener(('127.0.0.1', 0), 'AF_INET')
        self._address = self.listener.address

    def _response_socket_notice(self, socket):
        try:
            while self._response_receiver.poll():
                serialized_response = QtCore.QByteArray(
                    self._response_receiver.recv_bytes()
                )
                root_backend = get_root_backend()
                root_backend.action_runner().onResponse(serialized_response)
        except EOFError:
            LOGGER.info("Terminated")


    def __getstate__(self):
        state = self.__dict__.copy()
        state.pop('listener')
        return state

    def start(self):
        rb = get_root_backend()
        rb.action_runner().request.connect(self.post)
        rb.stop.connect(self.stop)
        super().start()
        # accept blocks until the child process connects
        self._response_receiver = self.listener.accept()
        self.socket_notifier = QtCore.QSocketNotifier(
            self._response_receiver.fileno(), QtCore.QSocketNotifier.Type.Read
        )
        self.socket_notifier.activated.connect(self._response_socket_notice)
        # as per Qt documentation, explicit enabling of the notifier is advised
        self.socket_notifier.setEnabled(True)
        rb.action_runner().onConnected()
        self._response_socket_notice(self._response_receiver.fileno())

    def initialize(self):
        """
        Overwrite this method in subclasses to initialize a process when it
        starts running.
        """
        pass

    def run(self):
        LOGGER = logging.getLogger("model_process")
        self.initialize()
        self._response_sender = connection.Client(
            self._address, 'AF_INET'
        )
        response_handler = PipeResponseHandler(self._response_sender)
        while True:
            response_handler.send_response(Busy(False))
            request = self._request_queue.get()
            response_handler.send_response(Busy(True))
            try:
                AbstractRequest.handle_request(
                    request, response_handler, response_handler
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
            finally:
                self._request_queue.task_done()
        LOGGER.info("Terminated")

    def post(self, request):
        if self._request_queue is None:
            LOGGER.error('Request posted to no longer running process {}'.format(request.data()))
            raise Exception('Process no longer running')
        self._request_queue.put(request.data())
        return ['process', str(self.pid)]

    def stop(self):
        """
        Request the worker to finish its ongoing tasks and stop
        """
        get_root_backend().action_runner().request.disconnect(self.post)
        # make sure no messages can be send to the request queue, after
        # the stop_request was send
        request_queue = self._request_queue
        self._request_queue = None
        request_queue.put(stop_request._to_bytes())
        self.join()
        # as per Qt documentation, explicit disabling of the notifier is advised
        self.socket_notifier.setEnabled(False)
