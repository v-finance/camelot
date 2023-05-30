import time
import unittest

from camelot.test import RunningProcessCase
from camelot.view.action_runner import action_runner
from camelot.view.model_thread.signal_slot_model_thread import TaskHandler
from camelot.view.requests import (
    CancelAction, InitiateAction, SendActionResponse, ThrowActionException
)

cancel_action = CancelAction(run_name=['d'])
initiate_action = InitiateAction(
    gui_run_name=['a'], action_name=['b'], model_context=['c'], mode=None,
)
send_action_response = SendActionResponse(run_name=['a'], response=None)
throw_action_exception = ThrowActionException(run_name=['a'], exception=None)


class ModelThreadCase(unittest.TestCase):

    def test_handle_request(self):
        task_queue = [None, cancel_action._to_bytes()]
        task_handler = TaskHandler(task_queue)
        task_handler.handle_task()
        self.assertFalse(len(task_queue))

class ModelProcessCase(RunningProcessCase):

    def test_execute_request(self):
        CancelAction.execute(cancel_action._to_dict()[1], action_runner, None)
        InitiateAction.execute(
            initiate_action._to_dict()[1], action_runner, None
        )
        SendActionResponse.execute(
            send_action_response._to_dict()[1], action_runner, None
        )
        ThrowActionException.execute(
            send_action_response._to_dict()[1], action_runner, None
        )

    def test_post_task(self):
        self.thread.post(cancel_action)
        time.sleep(1)
        # qsize is not reliable according to multiprocessing docs
        # self.assertFalse(self.thread._request_queue.qsize())
