import json
import os
import time

from camelot.test import RunningProcessCase, ActionMixinCase
from camelot.core.backend import PythonConnection, get_root_backend
from camelot.core.qt import QtCore
from camelot.view.requests import (
    CancelAction, InitiateAction, SendActionResponse, ThrowActionException
)

from .testing_context import cancelable_action_name

cancel_action = CancelAction(run_name=['d'])
initiate_action = InitiateAction(
    gui_run_name=['a'], action_name=['b'], model_context=['c'], mode=None,
)
send_action_response = SendActionResponse(run_name=['a'], response=None)
throw_action_exception = ThrowActionException(run_name=['a'], exception=None)

test_context = """

import sys
sys.path.append('{}')

import testing_context

""".format(os.path.join(os.path.dirname(__file__)))

testing_context_args = json.dumps([test_context])

class DelayedCancel(QtCore.QObject):

    def __init__(self, client_run_name, delay):
        super().__init__()
        self.client_run_name = client_run_name
        self.timer = QtCore.QTimer()
        self.timer.setSingleShot(True)
        self.timer.timeout.connect(self.cancel)
        self.timer.start(delay)

    @QtCore.qt_slot()
    def cancel(self):
        print('============================')
        print('CANCEL...')
        print('============================')
        get_root_backend().cancel_action(self.client_run_name)


class ModelProcessCase(RunningProcessCase, ActionMixinCase):

    args = testing_context_args

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

    def test_start_stop_service(self):
        service = self.rb.create_server_process()
        service.start('exec', testing_context_args)
        service.waitForConnected(10000)
        service.stop()
        service.waitForFinished(10000)

    def test_cancel(self):
        root_backend = get_root_backend()
        gui_context_name = ('constant', 'null')
        model_context_name = ('constant', 'null')

        # This action yields 10 UpdateProgress steps, 1 every 3 seconds
        gui_run_name = root_backend.run_action(
            gui_context_name, cancelable_action_name, model_context_name, None
        )

        # Cancel the action after 10 seconds
        self.cancel = DelayedCancel(gui_run_name, 10000)
        # Wait until all actions are done
        root_backend.action_runner().waitForCompletion()

        # Check that there less than 10 steps
        steps = self._recorded_steps[tuple(gui_run_name)]
        self.assertLess(len(steps), 10)
