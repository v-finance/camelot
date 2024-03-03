import logging
import json

from camelot.admin.action.base import MetaActionStep
from camelot.core.exception import CancelRequest
from camelot.core.qt import QtWidgets, QtCore
from camelot.core.serializable import json_encoder, NamedDataclassSerializable

from .requests import StopProcess

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

class QmlDispatch(QtCore.QObject):
    """
    Dispatch requests from the root backend that cannot be handled
    by the root backend itself to the python code being able to handle it.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        root_backend = get_qml_root_backend()
        root_backend.unhandledActionStep.connect(self.onUnhandledActionStep)
        self.action_runner = root_backend.actionRunner()

    @QtCore.qt_slot('QStringList', str, 'QStringList', QtCore.QByteArray)
    def onUnhandledActionStep(self, gui_run_name, step_type, gui_context_name, serialized_step):
        """The backend has cannot handle an action step"""
        root_backend = get_qml_root_backend()
        try:
            step_cls = MetaActionStep.action_steps[step_type]
            result = step_cls.gui_run(tuple(gui_context_name), bytes(serialized_step))
            if step_cls.blocking == True:
                serialized_result = json_encoder.encode(result).encode('utf-8')
                root_backend.actionStepResultValid.emit(gui_run_name, serialized_result, False, "")
        except CancelRequest:
            root_backend.actionStepResultValid.emit(gui_run_name, b'', True, "")
        except Exception as e:
            LOGGER.error("Step type {}".format(step_type))
            LOGGER.error("Gui context name {}".format(gui_context_name))
            LOGGER.error("Unhandled action step raised an exception", exc_info=e)
            root_backend.actionStepResultValid.emit(gui_run_name, b'', False, str(e))

qml_dispatch = QmlDispatch()

def qml_action_step(gui_context_name, name, step=QtCore.QByteArray()):
    backend = get_qml_root_backend()
    response = backend.actionStep(gui_context_name, name, step)
    return json.loads(response.data())

class PythonConnection(QtCore.QObject):
    """Use python to connect to a server, this is done by using
    the PythonRootBackend, and lister for signals from the action runner
    and the dgc
    """

    def __init__(self):
        super().__init__()
        backend = get_qml_root_backend()
        dgc = backend.distributedGarbageCollector()
        dgc.request.connect(self.onRequest)
        backend.request.connect(self.onRequest)

    @classmethod
    def _execute_serialized_request(cls, serialized_request, response_handler):
        try:
            request_type_name, request_data = json.loads(serialized_request)
            request_type = NamedDataclassSerializable.get_cls_by_name(
                request_type_name
            )
            if request_type == StopProcess:
                pass
                #break
            request_type.execute(request_data, response_handler, response_handler)
        except Exception as e:
            LOGGER.error('Unhandled exception in model process', exc_info=e)
            import traceback
            traceback.print_exc()
        except:
            LOGGER.error('Unhandled event in model process')

    @QtCore.qt_slot(QtCore.QByteArray)
    def onRequest(self, request):
        print('Received request', request.data())
        self._execute_serialized_request(request.data(), self)

    @classmethod
    def send_response(cls, response):
        print('send response', type(response))
        backend = get_qml_root_backend()
        action_runner = backend.actionRunner()
        action_runner.onResponse(QtCore.QByteArray(response._to_bytes()))

    def has_cancel_request(self):
        return False
