from camelot.core.qt import QtCore
from camelot.view.qml_view import get_qml_window

class ItemViewProxy(QtCore.QObject):
    """
    proxy to handle the difference between a classic Qt item view and,
    a qml ListView item.
    """

    def __init__(self, backend):
        super().__init__()
        self._backend = backend

    def model(self):
        return self._backend.property('model')

    def selectionModel(self):
        return self._backend.property('selectionModel')

    def currentIndex(self):
        selection_model = self.selectionModel()
        if selection_model is not None:
            return selection_model.property('currentIndex')
        model = self.model()
        return model.index(-1, 0)

    def window(self):
        return get_qml_window()

    def close_editor(self):
        pass

    def clearSelection(self):
        pass
