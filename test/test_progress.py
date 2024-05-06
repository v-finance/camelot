from camelot.admin.action.base import Action
from camelot.core.qt import QtCore
from camelot.core.backend import get_root_backend, PythonBackend
from camelot.core.exception import CancelRequest
from camelot.core.naming import initial_naming_context
from camelot.view.model_process import ModelProcess
from camelot.view.action_steps.update_progress import UpdateProgress
from camelot.test import RunningProcessCase

from .test_model import cancelable_action_name

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
        get_root_backend().cancel_action(self.client_run_name)


class ProgressCase(RunningProcessCase):

    process_cls = ModelProcess

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
