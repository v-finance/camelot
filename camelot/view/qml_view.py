import logging
import json

from camelot.core.qt import QtWidgets, QtQuick, QtCore, QtQml, jsonvalue_to_py
from camelot.core.exception import UserException
from .action_runner import ActionRunner


LOGGER = logging.getLogger(__name__)


def check_qml_errors(obj, url):
    """
    Check for QML errors.

    :param obj: a `QtQml.QQmlComponent` or `QtQuick.QQuickView` instance.
    :param url: The component QML source url.
    """
    Error = QtQml.QQmlComponent.Status.Error if isinstance(obj, QtQml.QQmlComponent) else QtQuick.QQuickView.Status.Error
    if obj.status() == Error:
        errors = []
        for error in obj.errors():
            errors.append(error.description())
            LOGGER.error(error.description())
        raise UserException(
            "Could not create QML component {}".format(url),
            detail='\n'.join(errors)
        )

def create_qml_component(url, engine=None):
    """
    Create a `QtQml.QQmlComponent` from an url.

    :param url: The url containing the QML source.
    :param engine: A `QtQml.QQmlEngine` instance.
    """
    if engine is None:
        engine = QtQml.QQmlEngine()
    component = QtQml.QQmlComponent(engine, url)
    check_qml_errors(component, url)
    return component

def create_qml_item(url, initial_properties={}, engine=None):
    """
    Create a `QtQml.QQmlComponent` from an url.

    :param url: The url containing the QML source.
    :param initial_properties: dict containing the initial properties for the QML Item.
    :param engine: A `QtQml.QQmlEngine` instance.
    """
    component = create_qml_component(url, engine)
    item = component.createWithInitialProperties(initial_properties)
    check_qml_errors(component, url)
    return item


def get_qml_engine():
    """
    Get the QQmlEngine that was created in C++. This engine contains the Font
    Awesome image provider plugin.
    """
    app = QtWidgets.QApplication.instance()
    engine = app.findChild(QtQml.QQmlEngine, 'cpp_qml_engine')
    return engine

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

def get_crud_signal_handler():
    """
    Get the CRUD signal handler singleton instance.
    """
    app = QtWidgets.QApplication.instance()
    crud_signal_handler = app.findChild(QtCore.QObject, 'cpp_crud_signal_handler')
    return crud_signal_handler

def get_dgc_client():
    """
    Get the distributed grabage collection client singleton instance.
    """
    app = QtWidgets.QApplication.instance()
    dgc_client = app.findChild(QtCore.QObject, 'cpp_dgc_client')
    return dgc_client

def is_cpp_gui_context_name(gui_context_name):
    """
    Check if a GUI context name was created in C++. This is the case when the name starts with 'cpp_gui_context'.
    """
    if not len(gui_context_name):
        return False
    return gui_context_name[0] == 'cpp_gui_context'

def is_cpp_gui_context(gui_context):
    """
    Check if a GUI context's name was created in C++. This is the case when the name starts with 'cpp_gui_context'.
    """
    if gui_context is None:
        return False
    if gui_context.gui_context_name is None:
        return False
    return is_cpp_gui_context_name(gui_context.gui_context_name)


# FIXME: add timeout + keep-alive on client
class QmlActionDispatch(QtCore.QObject):

    def __init__(self, parent=None):
        super().__init__(parent)
        root_backend = get_qml_root_backend()
        if root_backend is not None:
            root_backend.runAction.connect(self.run_action)

    def run_action(self, gui_context_name, route, args, model_context_name):
        LOGGER.info('QmlActionDispatch.run_action({}, {}, {}, {})'.format(gui_context_name, route, jsonvalue_to_py(args), model_context_name))
        action_runner = ActionRunner(
            tuple(route), tuple(gui_context_name), tuple(model_context_name), args
        )
        action_runner.exec()

qml_action_dispatch = QmlActionDispatch()


def qml_action_step(gui_context_name, name, step=QtCore.QByteArray(), props={}):
    backend = get_qml_root_backend()
    response = backend.actionStep(gui_context_name, name, step, props)
    return json.loads(response.data())

class LiveRef(QtCore.QObject):

    def __init__(self, name, parent=None):
        super().__init__(parent)
        self.setProperty('name', name)
        get_dgc_client().registerRef(self)
