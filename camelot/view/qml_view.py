from camelot.core.qt import QtWidgets, QtQuick, QtCore
from camelot.view.controls.view import AbstractView


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
        self.quick_view.setResizeMode(QtQuick.QQuickView.SizeRootObjectToView)
        container = QtWidgets.QWidget.createWindowContainer(self.quick_view)
        layout = QtWidgets.QBoxLayout(QtWidgets.QBoxLayout.BottomToTop)
        layout.addWidget(container)
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)

    @QtCore.qt_slot()
    def close(self):
        return False

    def refresh(self):
        pass
