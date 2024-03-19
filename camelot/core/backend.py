import logging
import json

from camelot.core.qt import QtWidgets, QtCore, jsonvalue_to_py
from camelot.view.action_runner import action_runner

LOGGER = logging.getLogger(__name__)

_backend = None
_window = None

def get_root_backend():
    """
    Get the root backend that is used to communicate between python and C++/QML.
    """
    global _backend
    if _backend is None:
        app = QtWidgets.QApplication.instance()
        _backend = app.findChild(QtCore.QObject, 'cpp_root_backend')
        assert _backend
    return _backend

def get_window():
    """
    Get the QQuickView that was created in C++.
    """
    global _window
    if _window is None:
        _window = get_root_backend().window()
        assert _window
    return _window

def is_cpp_gui_context_name(gui_context_name):
    """
    Check if a GUI context name was created in C++. This is the case when the name starts with 'cpp_gui_context'.
    """
    if not len(gui_context_name):
        return False
    return gui_context_name[0] == 'cpp_gui_context'

def cpp_action(gui_context_name, route, model_context_name, args):
    LOGGER.debug('cpp_action({}, {}, {}, {})'.format(gui_context_name, route, jsonvalue_to_py(args), model_context_name))
    action_runner.run_action(
        tuple(route), tuple(gui_context_name), tuple(model_context_name), jsonvalue_to_py(args)
    )

def cpp_action_step(gui_context_name, name, step=QtCore.QByteArray()):
    response = get_root_backend().action_step(gui_context_name, name, step)
    return json.loads(response.data())


class ActionDispatch(QtCore.QObject):

    def __init__(self, parent=None):
        super().__init__(parent)
        get_root_backend().run_action.connect(self.run_action)

    def run_action(self, gui_context_name, route, model_context_name, args):
        cpp_action(gui_context_name, route, model_context_name, args)

action_dispatch = ActionDispatch()
