import logging
import json

from camelot.core.qt import QtWidgets, QtCore, jsonvalue_to_py
from .action_runner import action_runner


LOGGER = logging.getLogger(__name__)

def get_qml_root_backend():
    """
    Get the root backend that is used to communicate between python and C++/QML.
    """
    app = QtWidgets.QApplication.instance()
    backend = app.findChild(QtCore.QObject, 'cpp_qml_root_backend')
    return backend

def get_qml_window():
    """
    Get the QQuickView that was created in C++.
    """
    app = QtWidgets.QApplication.instance()
    for widget in app.allWindows():
        if widget.objectName() == 'cpp_qml_window':
            return widget

def is_cpp_gui_context_name(gui_context_name):
    """
    Check if a GUI context name was created in C++. This is the case when the name starts with 'cpp_gui_context'.
    """
    if not len(gui_context_name):
        return False
    return gui_context_name[0] == 'cpp_gui_context'

def qml_action_step(gui_context_name, name, step=QtCore.QByteArray()):
    backend = get_qml_root_backend()
    response = backend.actionStep(gui_context_name, name, step)
    return json.loads(response.data())
