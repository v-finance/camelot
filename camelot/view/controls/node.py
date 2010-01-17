from PyQt4.QtCore import Qt, QRectF, QPointF
from PyQt4.QtGui import QApplication, QGraphicsItem, QPainterPath, QPen


class Node(QGraphicsItem):

    PEN = QPen(Qt.black, 1.0)
    BRUSH_COLOR = Qt.lightGray

    def __init__(self, text, parent=None):
        super(Node, self).__init__(parent)
        self.setZValue(10)
        self.text = text
        
        # pre-calculate bounding rect
        metrics = QApplication.fontMetrics()
        self.rect = QRectF(metrics.boundingRect(text))
        self.rect.moveCenter(QPointF(0.0, 0.0))
        # adjust margin
        self.rect.adjust(-10.0, -10.0, 10.0, 10.0)
    
    def type(self):
        return QGraphicsItem.UserType + 1

    def boundingRect(self):
        hpw = 0.5 # half pen width
        return self.rect.adjusted(-hpw, -hpw, hpw, hpw)

    def shape(self):
        path = QPainterPath()
        path.addEllipse(self.rect)
        return path

    def paint(self, painter, options, widget):
        painter.setPen(Node.PEN)
        painter.setBrush(Node.BRUSH_COLOR)
        painter.drawEllipse(self.rect)
        painter.drawText(self.rect, Qt.AlignCenter, self.text)
