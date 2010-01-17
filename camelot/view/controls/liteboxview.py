#  ============================================================================
#
#  Copyright (C) 2007-2010 Conceptive Engineering bvba. All rights reserved.
#  www.conceptive.be / project-camelot@conceptive.be
#
#  This file is part of the Camelot Library.
#
#  This file may be used under the terms of the GNU General Public
#  License version 2.0 as published by the Free Software Foundation
#  and appearing in the file LICENSE.GPL included in the packaging of
#  this file.  Please review the following information to ensure GNU
#  General Public Licensing requirements will be met:
#  http://www.trolltech.com/products/qt/opensource.html
#
#  If you are unsure which license is appropriate for your use, please
#  review the following information:
#  http://www.trolltech.com/products/qt/licensing.html or contact
#  project-camelot@conceptive.be.
#
#  This file is provided AS IS with NO WARRANTY OF ANY KIND, INCLUDING THE
#  WARRANTY OF DESIGN, MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE.
#
#  For use of this library in commercial applications, please contact
#  project-camelot@conceptive.be
#
#  ============================================================================

import sys
from PyQt4.QtGui import (
    QApplication,
    QGraphicsView,
    QGraphicsScene,     
    QColor, QPixmap,
    QWidget, QPainter,
)
from PyQt4.QtCore import Qt, QEvent

from camelot.view.controls.node import Node


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


class CloseNode(Node):

    def __init__(self, parent=None):
        super(CloseNode, self).__init__('Close', parent)

    def mousePressEvent(self, event):
        view = self.scene().views()[0]
        view.close()


class LiteBoxView(QGraphicsView):

    ALPHABLACK = QColor(0, 0, 0, 192)

    def __init__(self, parent=None):
        super(LiteBoxView, self).__init__(parent)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        
        # will propagate to children
        self.setRenderHint(QPainter.Antialiasing)
        self.setRenderHint(QPainter.TextAntialiasing)

        self.scene = QGraphicsScene()
        self.setScene(self.scene)

    def drawBackground(self, painter, rect):
        painter.drawPixmap(self.mapToScene(0, 0), get_desktop_pixmap())
        painter.setBrush(LiteBoxView.ALPHABLACK)
        painter.drawRect(rect)

    def activateOn(self, widget):
        widget.installEventFilter(self)

    def deactivateFrom(self, widget):
        widget.removeEventFilter(self)

    def eventFilter(self, object, event):
        if not object.isWidgetType():
            return False

        if event.type() != QEvent.MouseButtonDblClick:
            return False

        if event.modifiers() != Qt.NoModifier:
            return False

        if event.buttons() == Qt.LeftButton:
            pixmap = QPixmap.grabWidget(object)
            self.scene.addPixmap(fit_to_screen(pixmap))
            self.scene.addItem(CloseNode())
            self.showFullScreen()
            return True


if __name__ == '__main__':
    app = QApplication(sys.argv)
    w = QWidget()
    v = LiteBoxView()
    v.activateOn(w)
    w.show()
    sys.exit(app.exec_())
