#  ============================================================================
#
#  Copyright (C) 2007-2016 Conceptive Engineering bvba.
#  www.conceptive.be / info@conceptive.be
#
#  Redistribution and use in source and binary forms, with or without
#  modification, are permitted provided that the following conditions are met:
#      * Redistributions of source code must retain the above copyright
#        notice, this list of conditions and the following disclaimer.
#      * Redistributions in binary form must reproduce the above copyright
#        notice, this list of conditions and the following disclaimer in the
#        documentation and/or other materials provided with the distribution.
#      * Neither the name of Conceptive Engineering nor the
#        names of its contributors may be used to endorse or promote products
#        derived from this software without specific prior written permission.
#  
#  THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
#  ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
#  WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
#  DISCLAIMED. IN NO EVENT SHALL <COPYRIGHT HOLDER> BE LIABLE FOR ANY
#  DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
#  (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
#  LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
#  ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
#  (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
#  SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#
#  ============================================================================

from ...core.qt import QtCore, QtGui, QtWidgets, Qt
from camelot.view.art import Pixmap


def get_desktop():
    return QtCore.QCoreApplication.instance().desktop()

def get_desktop_pixmap():
    return QtGui.QPixmap.grabWindow(get_desktop().winId())

def fit_to_screen(pixmap):
    d = get_desktop()
    dh = d.height()
    dw = d.width()
    if dh < pixmap.height() or dw < pixmap.width():
        fit = .95
        return pixmap.scaled(dw * fit, dh * fit, Qt.KeepAspectRatio)
    return pixmap

class CloseMark(QtWidgets.QGraphicsPixmapItem):

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


class LiteBoxView(QtWidgets.QGraphicsView):

    ALPHA = QtGui.QColor(0, 0, 0, 192)

    closed_signal = QtCore.qt_signal()

    def __init__(self, parent=None):
        super(LiteBoxView, self).__init__(parent)
        self.setWindowFlags(Qt.Window | Qt.WindowStaysOnTopHint)
        #self.setAttribute(Qt.WA_DeleteOnClose)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setViewportUpdateMode(QtWidgets.QGraphicsView.FullViewportUpdate)
        QtGui.QShortcut( Qt.Key_Escape, self, self.close )
        self.desktopshot = None

        # will propagate to children
        self.setRenderHint(QtGui.QPainter.Antialiasing)
        self.setRenderHint(QtGui.QPainter.TextAntialiasing)

        self.scene = QtGui.QGraphicsScene()
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

    def show_fullscreen_pixmap(self, pixmap):
        """:param pixmap: a QPixmap"""
        item = QtWidgets.QGraphicsPixmapItem(pixmap)
        self.show_fullscreen_item(item)
        
    def show_fullscreen_image(self, image):
        """:param image: a QImage"""
        pixmap = QtGui.QPixmap.fromImage(image)
        self.show_fullscreen_pixmap( pixmap )

    def show_fullscreen_item(self, item):
        """:param item: a QGraphicsItem to be shown fullscreen"""
        item.setFlag(QtGui.QGraphicsItem.ItemIsFocusable, True)
        self.scene.clear()
        self.scene.addItem(item)
        CloseMark(parent=item)
        self.showFullScreen()
        self.setFocus()



