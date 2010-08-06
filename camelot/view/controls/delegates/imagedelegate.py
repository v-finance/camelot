from filedelegate import FileDelegate
from camelot.view.controls import editors

from PyQt4 import QtGui, QtCore
from PyQt4.QtCore import Qt

class ImageDelegate(FileDelegate):
    """
    .. image:: ../_static/image.png
    """
    
    editor = editors.ImageEditor
    
    def paint(self, painter, option, index):
        painter.save()
        self.drawBackground(painter, option, index)
        pixmap = QtGui.QPixmap(index.model().data(index, Qt.DisplayRole))
        
        if pixmap.width() > 0 and pixmap.height() > 0:
            rect = option.rect
            rect = QtCore.QRect(rect.left()+max(0, rect.width()-pixmap.width())/2, 
                                rect.top()+max(0, rect.height()-pixmap.height())/2, 
                                pixmap.width(), pixmap.height())
            QtGui.QApplication.style().drawItemPixmap(painter, rect, 1, pixmap)
            pen = QtGui.QPen(Qt.darkGray)
            pen.setWidth(3)
            painter.setPen(pen)
            painter.drawRect(rect)
        painter.restore()

