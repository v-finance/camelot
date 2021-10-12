from camelot.core.qt import QtQml, QtCore

class ItemViewProxy(QtCore.QObject):
    """
    proxy to handle the difference between a classic Qt item view and,
    a qml ListView item.
    """

    def __init__(self, qml_item):
        super().__init__()
        self._qml_item = qml_item
        selection_model = QtCore.QItemSelectionModel(self.model(), qml_item)
        selection_model.setObjectName('selection_model')
        qml_item.activated.connect(self._update_current_index)

    @QtCore.qt_slot()
    def _update_current_index(self):
        selection_model = self.selectionModel()
        selection_model.setCurrentIndex(
            self.currentIndex(), QtCore.QItemSelectionModel.SelectCurrent
        )

    def model(self):
        return self._qml_item.property('model')

    def currentIndex(self):
        model = self.model()
        qml_property = QtQml.QQmlProperty(self._qml_item, 'currentIndex')
        view_index = qml_property.read()
        return model.index(view_index, 0)

    def selectionModel(self):
        selection_model = self._qml_item.findChild(
            QtCore.QItemSelectionModel, 'selection_model'
        )
        return selection_model

    def window(self):
        return self._qml_item.window()

    def close_editor(self):
        pass

    def clearSelection(self):
        pass