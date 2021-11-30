import logging
import itertools

from camelot.core.qt import QtWidgets, QtQuick, QtCore, QtQml
from camelot.core.exception import UserException
from camelot.view.controls.view import AbstractView
from camelot.admin.admin_route import AdminRoute, Route

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

# FIXME: add timeout + keep-alive on client
class QmlActionDispatch(QtCore.QObject):

    _context_ids = itertools.count()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.gui_contexts = {}
        root_backend = get_qml_root_backend()
        root_backend.runAction.connect(self.run_action)


    def register(self, gui_context):
        print('register_context:', gui_context)
        #if gui_context.context_id is not None:
        #    return gui_context.context_id
        context_id = self._context_ids.__next__()
        print('    id -->', context_id)
        self.gui_contexts[context_id] = gui_context
        gui_context.context_id = context_id
        return context_id

    def has_context(self, gui_context):
        if gui_context.context_id is None:
            return False
        return gui_context.context_id in self.gui_contexts

    def run_action(self, context_id, route, args):
        LOGGER.info('QmlActionDispatch.run_action({}, {}, {})'.format(context_id, route, args))
        if context_id not in self.gui_contexts:
            raise UserException(
                'Could not find gui_context for context id: {}'.format(context_id),
                detail='run_action({}, {})'.format(route, args)
            )
        action = AdminRoute.action_for(tuple(route.split('/')))

        gui_context = self.gui_contexts[context_id].copy()

        if isinstance(args, QtQml.QJSValue):
            mode = variant_to_py(mode.toVariant())
        if isinstance(args, list):
            action.gui_run( gui_context, args )
        else:
            gui_context.mode_name = args
            action.gui_run( gui_context )


qml_action_dispatch = QmlActionDispatch()


def qml_action_step(gui_context, name, step):
    """
    Register the gui_context and execute the action step by specifying a name and serialized action step.
    """
    global qml_action_dispatch
    context_id = qml_action_dispatch.register(gui_context)
    backend = get_qml_root_backend()
    backend.actionStep(context_id, name, step)

def qml_action_step_item(gui_context, qml_item):
    """
    Register the gui_context and execute the action step by specifying a QQuickItem.
    """
    global qml_action_dispatch
    context_id = qml_action_dispatch.register(gui_context)
    backend = get_qml_root_backend()
    backend.actionStepItem(context_id, qml_item)


class QmlView(AbstractView):
    """
    A QML view.

    This creates the main QML widget to which all QML items should be added.
    """

    def __init__(self, gui_context, url, initial_properties={}):
        super().__init__()
        self.setObjectName('qml_view')
        self.gui_context = gui_context
        engine = get_qml_engine()
        self.quick_view = QtQuick.QQuickView(engine, None)
        self.quick_view.engine().addImportPath(':/')
        self.quick_view.setInitialProperties(initial_properties)
        self.quick_view.setSource(url)
        check_qml_errors(self.quick_view, url)
        self.quick_view.setResizeMode(QtQuick.QQuickView.ResizeMode.SizeRootObjectToView)
        container = QtWidgets.QWidget.createWindowContainer(self.quick_view)
        layout = QtWidgets.QBoxLayout(QtWidgets.QBoxLayout.Direction.BottomToTop)
        layout.addWidget(container)
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)

    @QtCore.qt_slot()
    def close(self):
        return False

    def refresh(self):
        pass
