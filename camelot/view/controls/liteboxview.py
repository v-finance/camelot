# description: lightbox effect a la javascipt done with pyqt
# author: victor noagbodji

import sys
from PyQt4.QtGui import (
    QApplication,
    QColor, QPixmap, QPushButton,
    QGraphicsView, QGraphicsScene
)
from PyQt4.QtCore import Qt, QPoint


def get_desktop():
    from PyQt4.QtCore import QCoreApplication
    return QCoreApplication.instance().desktop()


def get_desktop_pixmap():
    return QPixmap.grabWindow(get_desktop().winId())


def fit_to_screen(pixmap):
    d = get_desktop()
    dh = d.height()
    dw = d.width()
    if dh < pixmap.height() or dw < pixmap.width():
        fit = .95
        return pixmap.scaled(dw * fit, dh * fit, Qt.KeepAspectRatio)
    return pixmap


class LiteBoxView(QGraphicsView):

    def __init__(self, path, parent=None):
        super(LiteBoxView, self).__init__(parent)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        self.scene = QGraphicsScene()
        self.path = path
        self.pixitem = self.scene.addPixmap(fit_to_screen(QPixmap(self.path)))
        self.setScene(self.scene)

    def mousePressEvent(self, event):
        self.close()

    def drawBackground(self, painter, rect):
        painter.drawPixmap(self.mapToScene(0, 0), get_desktop_pixmap())
        painter.setBrush(QColor(0, 0, 0, 127))
        painter.drawRect(rect)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    view = LiteBoxView('anime.jpg')
    view.showFullScreen()
    sys.exit(app.exec_())
