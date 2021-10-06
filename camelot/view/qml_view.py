import logging

from camelot.core.qt import QtWidgets, QtQuick, QtCore, QtQml
from camelot.core.exception import UserException
from camelot.view.controls.view import AbstractView

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


class QmlView(AbstractView):
    """
    A QML view.

    This creates the main QML widget to which all QML items should be added.
    """

    def __init__(self, gui_context, url, initial_properties={}):
        super().__init__()
        self.setObjectName('qml_view')
        self.gui_context = gui_context
        self.quick_view = QtQuick.QQuickView()
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
