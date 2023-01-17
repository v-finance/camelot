import json
import logging
import multiprocessing

from ..core.qt import QtCore
from ..core.serializable import NamedDataclassSerializable, DataclassSerializable
from .requests import StopProcess
from .responses import AbstractResponse, ActionStepped, Busy

LOGGER = logging.getLogger(__name__)

stop_request = StopProcess()


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


class ModelProcess(multiprocessing.Process):

    def __init__(self):
        super().__init__()
        self._request_queue = multiprocessing.JoinableQueue()
        self._response_receiver, self._response_sender = multiprocessing.Pipe(duplex=False)
        self.socket_notifier = QtCore.QSocketNotifier(
            self._response_receiver.fileno(), QtCore.QSocketNotifier.Type.Read
        )
        self.socket_notifier.activated.connect(self._response_socket_notice)

    def _response_socket_notice(self, socket):
        if self._response_receiver.poll():
            serialized_response = self._response_receiver.recv_bytes()
            AbstractResponse.handle_serialized_response(serialized_response, self.post)
    
    def run(self):
        LOGGER = logging.getLogger("model_process")
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
        self._request_queue.put(request._to_bytes())

    def stop(self):
        """
        Request the worker to finish its ongoing tasks and stop
        """
        self.post(stop_request)
        self.join()
