import time

from camelot.test import RunningProcessCase
from camelot.core.backend import PythonConnection
from camelot.core.qt import QtCore
from camelot.view.model_process import ModelProcess
from camelot.view.requests import (
    CancelAction, InitiateAction, SendActionResponse, ThrowActionException
)

cancel_action = CancelAction(run_name=['d'])
initiate_action = InitiateAction(
    gui_run_name=['a'], action_name=['b'], model_context=['c'], mode=None,
)
send_action_response = SendActionResponse(run_name=['a'], response=None)
throw_action_exception = ThrowActionException(run_name=['a'], exception=None)


class ModelProcessCase(RunningProcessCase):

    process_cls = ModelProcess

    def test_execute_request(self):
        CancelAction.execute(cancel_action._to_dict()[1], PythonConnection, None)
        InitiateAction.execute(
            initiate_action._to_dict()[1], PythonConnection, None
        )
        SendActionResponse.execute(
            send_action_response._to_dict()[1], PythonConnection, None
        )
        ThrowActionException.execute(
            send_action_response._to_dict()[1], PythonConnection, None
        )

    def test_post_task(self):
        self.thread.post(QtCore.QByteArray(cancel_action._to_bytes()))
        time.sleep(1)
        # qsize is not reliable according to multiprocessing docs
        # self.assertFalse(self.thread._request_queue.qsize())
