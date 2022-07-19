import logging
import itertools
import json
import inspect

from camelot.core.qt import QtWidgets, QtQuick, QtCore, QtQml, is_deleted
from camelot.core.exception import UserException
from camelot.core.naming import initial_naming_context, NameNotFoundException
from camelot.admin.action.application_action import ApplicationActionGuiContext
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
    if gui_context.gui_context_name is None:
        return False
    return is_cpp_gui_context_name(gui_context.gui_context_name)


# FIXME: add timeout + keep-alive on client
class QmlActionDispatch(QtCore.QObject):

    _gui_naming_context = initial_naming_context.bind_new_context(
        'gui_context', immutable=True
    )
    _gui_naming_context_ids = itertools.count()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.models = {}
        root_backend = get_qml_root_backend()
        if root_backend is not None:
            root_backend.runAction.connect(self.run_action)
            root_backend.releaseContext.connect(self.unregister)
        # register None gui_context as with ['gui_context', '0']
        self.register(None)

    def register(self, gui_context, model=None):
        if gui_context is None:
            gui_context_id = self._gui_naming_context_ids.__next__()
            gui_context_name = self._gui_naming_context.bind(str(gui_context_id), gui_context)
            return gui_context_name
        assert not is_cpp_gui_context(gui_context)
        if gui_context.gui_context_name is not None:
            if id(initial_naming_context.resolve(gui_context.gui_context_name)) == id(gui_context):
                return gui_context.gui_context_name
        gui_context_id = self._gui_naming_context_ids.__next__()
        gui_context_name = self._gui_naming_context.bind(str(gui_context_id), gui_context)
        if model is not None:
            self.models[gui_context_name] = model
            model.destroyed.connect(self.remove_model)
        gui_context.gui_context_name = gui_context_name
        return gui_context_name

    def unregister(self, gui_context_name):
        if not is_cpp_gui_context_name(gui_context_name):
            initial_naming_context.unbind(tuple(gui_context_name))

    @QtCore.qt_slot(QtCore.QObject)
    def remove_model(self):
        for gui_context_name, model in list(self.models.items()):
            if is_deleted(model):
                del self.models[gui_context_name]

    def has_context(self, gui_context):
        if gui_context is None:
            return True
        if gui_context.gui_context_name is None:
            return False
        try:
            initial_naming_context.resolve(gui_context.gui_context_name)
            return True
        except NameNotFoundException:
            return False

    def get_context(self, gui_context_name):
        return initial_naming_context.resolve(tuple(gui_context_name))

    def get_model(self, gui_context_name):
        return self.models.get(gui_context_name)

    def run_action(self, gui_context_name, route, args, model_context_name):
        LOGGER.info('QmlActionDispatch.run_action({}, {}, {}, {})'.format(gui_context_name, route, args, model_context_name))
        model = self.get_model(tuple(gui_context_name))
        if model is not None:
            model.timeout_slot()

        class DummyGuiContext(ApplicationActionGuiContext):

            def __init__(self, gui_context_name, model_context_name):
                super().__init__()
                self.admin_route = None
                self.gui_context_name = gui_context_name
                self.model_context_name = model_context_name

            def create_model_context(self):
                try:
                    return initial_naming_context.resolve(tuple(self.model_context_name))
                except NameNotFoundException:
                    # FIXME: DGCClient always uses ['model_context, '1'] for the unbind action which is not available in the tests
                    LOGGER.error('Could not create model context, no binding for name: {}'.format(self.model_context_name))

        gui_context = DummyGuiContext(gui_context_name, model_context_name)
        action_runner = ActionRunner(tuple(route), gui_context, args)
        action_runner.exec()

qml_action_dispatch = QmlActionDispatch()


# FIXME: rename to cpp_action_step?
def qml_action_step(gui_context, name, step=QtCore.QByteArray(), props={}, model=None):
    """
    Register the gui_context and execute the action step by specifying a name and serialized action step.
    """
    global qml_action_dispatch
    if isinstance(gui_context, list):
        gui_context_name = gui_context
    else:
        if gui_context is None:
            gui_context_name = ('gui_context', '0')
        elif gui_context.gui_context_name is None:
            gui_context_name = qml_action_dispatch.register(gui_context, model)
        else:
            gui_context_name = gui_context.gui_context_name
    backend = get_qml_root_backend()
    response = backend.actionStep(gui_context_name, name, step, props)
    return json.loads(response.data())
