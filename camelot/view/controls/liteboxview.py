#  ============================================================================
#
#  Copyright (C) 2007-2012 Conceptive Engineering bvba. All rights reserved.
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

from PyQt4.QtGui import (
    QPainter,
    QGraphicsView,
    QGraphicsScene,
    QColor, QPixmap,
    QGraphicsPixmapItem,
)
from PyQt4.QtCore import Qt
from PyQt4 import QtGui, QtCore

from camelot.view.art import Pixmap


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

class CloseMark(QGraphicsPixmapItem):

    def __init__(self, pixmap=None, hover_pixmap=None, parent=None):
        super(CloseMark, self).__init__(parent)

        DEFAULT_PIXMAP = Pixmap('close_mark.png').getQPixmap()
        DEFAULT_HOVER_PIXMAP = Pixmap('close_mark_hover.png').getQPixmap()

        self._pixmap = pixmap or DEFAULT_PIXMAP
        self._hover_pixmap = hover_pixmap or DEFAULT_HOVER_PIXMAP

        self.setPixmap(self._pixmap)

        # move to top right corner
        width = self.pixmap().width()
        height = self.pixmap().height()
        parent_width = self.parentItem().boundingRect().width()
        self.setPos(-width/2 + parent_width, -height/2)

        self.setAcceptsHoverEvents(True)
        # stays on top of other items
        self.setZValue(10)

    def hoverEnterEvent(self, event):
        self.setPixmap(self._hover_pixmap)
        self.update()

    def hoverLeaveEvent(self, event):
        self.setPixmap(self._pixmap)
        self.update()

    def mousePressEvent(self, event):
        view = self.scene().views()[0]
        view.close()


class LiteBoxView(QGraphicsView):

    ALPHA = QColor(0, 0, 0, 192)

    closed_signal = QtCore.pyqtSignal()

    def __init__(self, parent=None):
        super(LiteBoxView, self).__init__(parent)
        self.setWindowFlags(Qt.Window | Qt.WindowStaysOnTopHint)
        #self.setAttribute(Qt.WA_DeleteOnClose)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setViewportUpdateMode(QGraphicsView.FullViewportUpdate)
        QtGui.QShortcut( Qt.Key_Escape, self, self.close )
        self.desktopshot = None

        # will propagate to children
        self.setRenderHint(QPainter.Antialiasing)
        self.setRenderHint(QPainter.TextAntialiasing)

        self.scene = QGraphicsScene()
        self.setScene(self.scene)

    def close(self):
        self.closed_signal.emit()
        super(LiteBoxView, self).close()

    def drawBackground(self, painter, rect):
        if self.desktopshot is None:
            self.desktopshot = get_desktop_pixmap()

        painter.drawPixmap(self.mapToScene(0, 0), self.desktopshot)
        painter.setBrush(LiteBoxView.ALPHA)
        painter.drawRect(rect)

    def show_fullscreen_svg(self, path):
        """:param path: path to an svg file"""
        from PyQt4 import QtSvg
        item = QtSvg.QGraphicsSvgItem(path)
        self.show_fullscreen_item(item)

    def show_fullscreen_pixmap(self, pixmap):
        """:param pixmap: a QPixmap"""
        item = QGraphicsPixmapItem(pixmap)
        self.show_fullscreen_item(item)
        
    def show_fullscreen_image(self, image):
        """:param image: a QImage"""
        pixmap = QPixmap.fromImage(image)
        self.show_fullscreen_pixmap( pixmap )

    def show_fullscreen_item(self, item):
        """:param item: a QGraphicsItem to be shown fullscreen"""
        item.setFlag(QtGui.QGraphicsItem.ItemIsFocusable, True)
        self.scene.clear()
        self.scene.addItem(item)
        CloseMark(parent=item)
        self.showFullScreen()
        self.setFocus()

