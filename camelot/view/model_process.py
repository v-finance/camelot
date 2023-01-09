import json
import logging
import multiprocessing

from ..core.serializable import NamedDataclassSerializable
from .requests import StopProcess

LOGGER = logging.getLogger(__name__)

stop_request = StopProcess()


class ModelProcess(multiprocessing.Process):

    def __init__(self):
        super().__init__()
        self._request_queue = multiprocessing.JoinableQueue()

    def run(self):
        LOGGER = logging.getLogger("model_process")
        while True:
            request = self._request_queue.get()
            try:
                request_type_name, request_data = json.loads(request)
                request_type = NamedDataclassSerializable.get_cls_by_name(
                    request_type_name
                )
                if request_type == StopProcess:
                    break
                request_type.execute(request_data, None, self)
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
