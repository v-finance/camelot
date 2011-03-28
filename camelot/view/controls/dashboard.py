#  ============================================================================
#
#  Copyright (C) 2007-2011 Conceptive Engineering bvba. All rights reserved.
#  www.conceptive.be / project-camelot@conceptive.be
#
#  This file is part of the Camelot Library.
#
#  This file may be used under the terms of the GNU General Public
#  License version 2.0 as published by the Free Software Foundation
#  and appearing in the file license.txt included in the packaging of
#  this file.  Please review this information to ensure GNU
#  General Public Licensing requirements will be met.
#
#  If you are unsure which license is appropriate for your use, please
#  visit www.python-camelot.com or contact project-camelot@conceptive.be
#
#  This file is provided AS IS with NO WARRANTY OF ANY KIND, INCLUDING THE
#  WARRANTY OF DESIGN, MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE.
#
#  For use of this library in commercial applications, please contact
#  project-camelot@conceptive.be
#
#  ============================================================================
from PyQt4.QtGui import QApplication, QFrame, QPalette, QLabel, QPixmap
from PyQt4.QtCore import Qt, QRect, QCoreApplication


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
        mt.thread_busy_signal.connect( busy_widget.set_busy )
        busy_widget.set_busy(mt.busy())



if __name__ == '__main__':
    import sys
    app = QApplication(sys.argv)
    board = Dashboard()
    board.show()
    sys.exit(app.exec_())


