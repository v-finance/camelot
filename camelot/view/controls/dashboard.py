from PyQt4.QtGui import QApplication, QFrame, QPalette, QLabel, QPixmap
from PyQt4.QtCore import Qt, QRect, SIGNAL


class BareFrame(QFrame):

    def __init__(self, parent=None):
        super(BareFrame, self).__init__(parent)
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setFrameShadow(QFrame.Plain)
        self.setFrameShape(QFrame.Box)
        self.setLineWidth(1)

    def setBGColor(self, color):
        from PyQt4.QtCore import QCoreApplication
        pal = QCoreApplication.instance().palette()
        pal.setColor(QPalette.Window, color)
        self.setPalette(pal)


class CloseMark(QLabel):

    WIDTH  = 31
    HEIGHT = 31
    MARGIN = 10

    def __init__(self, pixmap, parent=None):
        super(CloseMark, self).__init__(parent)
        self.setPixmap(pixmap)
        self.toParentTopRight()
        
    def mousePressEvent(self, event):
        self.parent().close()

    def toParentTopRight(self):
        parent = self.parent()
        x = parent.width() - CloseMark.MARGIN - CloseMark.WIDTH
        y = CloseMark.MARGIN
        w = CloseMark.WIDTH
        h = CloseMark.HEIGHT
        self.setGeometry(QRect(x, y, w, h))


class Dashboard(BareFrame):
    
    WIDTH  = 830
    HEIGHT = 560

    def __init__(self, parent=None):
        super(Dashboard, self).__init__(parent)
        self.resize(Dashboard.WIDTH, Dashboard.HEIGHT)
        self.closemark = CloseMark(QPixmap('close-mark.png'), self)
        self.setBGColor(Qt.white)


if __name__ == '__main__':
    import sys
    app = QApplication(sys.argv)
    board = Dashboard()
    board.show()
    sys.exit(app.exec_())
