import logging
import multiprocessing
import os

LOGGER = logging.getLogger(__name__)

class StopProcess(object):
    pass


class ModelProcess(multiprocessing.Process):


    def __init__(self):
        super(ModelProcess, self).__init__()
        self._gui_end, self._model_end = multiprocessing.Pipe()

    def start(self):
        LOGGER.info("Starting model process")
        super(ModelProcess, self).start()

    def run(self):
        LOGGER = logging.getLogger("model_process")
        while True:
            try:
                task = self._receive_task()
            # EOFError will be raised if the pipe has been closed by the parent
            except EOFError:
                LOGGER.info("Pipe closed, terminating")
                break
            if isinstance(task, StopProcess):
                LOGGER.info("Request to stop process, terminating")
                break
            try:
               task()
            except Exception as e:
                LOGGER.error('Unhandled exception in model process', exc_info=e)
                import traceback
                traceback.print_exc()
            except:
                LOGGER.error('Unhandled event in model process')
        LOGGER.info("Terminated")

    def _validate_parent(self):
        if not self.is_alive():
            raise Exception('Model is not alive and cannot communicate')
        if self.parent_pid != os.getpid():
            raise Exception('Only the gui can communicate with the model')

    def stop(self):
        """
        Request the worker to finish its ongoing work and stop
        """
        self._gui_end.send(StopProcess())
        self._gui_end.close()

    def _receive_task(self):
        """
        Receive a task to be executed in the model
        """
        if self.pid != os.getpid():
            raise Exception('only the worker can receive work')
        if not self.is_alive():
            raise Exception('Worker is not alive, and cannot send results')
        return self._model_end.recv()
