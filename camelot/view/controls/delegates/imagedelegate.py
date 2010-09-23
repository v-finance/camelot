from filedelegate import FileDelegate
from camelot.view.controls import editors

from PyQt4 import QtGui, QtCore
from PyQt4.QtCore import Qt

class ImageDelegate(FileDelegate):
    """
    .. image:: ../_static/image.png
    """
    
    editor = editors.ImageEditor
    margin = 2
    
    def paint(self, painter, option, index):
        painter.save()
        self.drawBackground(painter, option, index)
        pixmap = QtGui.QPixmap(index.model().data(index, Qt.DisplayRole))
        
        if pixmap.width() > 0 and pixmap.height() > 0:
            rect = option.rect
            w_margin = max(0, rect.width() - pixmap.width())/2 + self.margin
            h_margin = max(0, rect.height()- pixmap.height())/2 + self.margin
            rect = QtCore.QRect(rect.left() + w_margin, 
                                rect.top() + h_margin , 
                                rect.width() - w_margin * 2, 
                                rect.height() - h_margin * 2 )
            painter.drawPixmap( rect, pixmap )
            pen = QtGui.QPen(Qt.darkGray)
            pen.setWidth(3)
            painter.setPen(pen)
            painter.drawRect(rect)
        painter.restore()

