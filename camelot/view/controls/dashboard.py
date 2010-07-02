from PyQt4.QtGui import QApplication, QFrame, QPalette, QLabel, QPixmap
from PyQt4.QtCore import Qt, QRect, SIGNAL, QCoreApplication


class BareFrame(QFrame):

    def __init__(self, parent=None):
        super(BareFrame, self).__init__(parent)
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setFrameShadow(QFrame.Plain)
        self.setFrameShape(QFrame.Box)
        self.setLineWidth(1)

    def setBGColor(self, color):
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
    
    SCALE  = .85

    def __init__(self, parent=None):
        from camelot.view.controls.busy_widget import BusyWidget
        from camelot.view.model_thread import get_model_thread
        super(Dashboard, self).__init__(parent)
        desktop = QCoreApplication.instance().desktop()
        self.resize(desktop.width() * Dashboard.SCALE, desktop.height() * Dashboard.SCALE)
        self.closemark = CloseMark(QPixmap('close-mark.png'), self)
        self.setBGColor(Qt.white)
        busy_widget = BusyWidget(self)
        busy_widget.setMinimumSize( desktop.width() * Dashboard.SCALE, desktop.height() * Dashboard.SCALE )
        #self.addPermanentWidget(busy_widget, 0)
        mt = get_model_thread()
        self.connect(mt, mt.thread_busy_signal, busy_widget.set_busy)
        busy_widget.set_busy(mt.busy())
        


if __name__ == '__main__':
    import sys
    app = QApplication(sys.argv)
    board = Dashboard()
    board.show()
    sys.exit(app.exec_())
