from camelot.core.qt import QtCore
from camelot.view.qml_view import get_qml_window

class ItemSelectionRangeProxy:

    def __init__(self, first, last):
        self.first = first
        self.last = last

    def top(self):
        return self.first

    def bottom(self):
        return self.last


class SelectionModelProxy:

    def __init__(self, backend):
        self.backend = backend

    def selection(self):
        row_ranges = self.backend.selection()
        assert len(row_ranges) % 2 == 0
        selection = []
        for i in range(len(row_ranges) // 2):
            first = row_ranges[2 * i]
            last = row_ranges[2 * i + 1]
            selection.append(ItemSelectionRangeProxy(first, last))
        return selection


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
        return SelectionModelProxy(self._backend)

    def currentIndex(self):
        return self.model().index(self._backend.property('currentRow'), 0)

    def selectRow(self, row):
        self._backend.selectRow(row, True)

    def window(self):
        return get_qml_window()

    def close_editor(self):
        pass

    def clearSelection(self):
        pass
