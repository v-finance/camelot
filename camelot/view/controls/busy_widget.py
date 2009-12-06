#  ============================================================================
#
#  Copyright (C) 2007-2008 Conceptive Engineering bvba. All rights reserved.
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

from PyQt4 import QtGui
from PyQt4.QtCore import Qt

class BusyWidget(QtGui.QWidget):
    """A widget indicating the application is performing some background task.  The widget acts
    as an overlay of its parent widget and displays animating orbs"""

    def __init__(self, parent = None):
        QtGui.QWidget.__init__(self, parent)
        palette = QtGui.QPalette(self.palette())
        palette.setColor(palette.Background, Qt.transparent)
        self.setPalette(palette)
        self.setAttribute(Qt.WA_TransparentForMouseEvents)
        self.orbs = 5
        self.highlighted_orb = self.orbs
        self.timer = None
        
    def set_busy(self, busy_state):
        """start/stop the animation
        :arg busy_state: True or False
        """
        if busy_state:
            self.timer = self.startTimer(200)
            self.counter = 0
            self.show()
        else:
            if self.timer:
                self.killTimer(self.timer)
                self.timer = None
            self.hide()

    def paintEvent(self, event):
        """custom paint, painting the orbs"""
        painter = QtGui.QPainter()
        painter.begin(self)
        painter.setRenderHint(QtGui.QPainter.Antialiasing)
        painter.setPen(QtGui.QPen(Qt.NoPen))
        width = self.width()
        height = self.height()
        radius = (min(width, height)/4)
        for i in range(self.orbs):
            if i!=self.highlighted_orb:
                painter.setBrush(QtGui.QBrush(QtGui.QColor(180, 180, 180)))
            else:
                painter.setBrush(QtGui.QBrush(QtGui.QColor(127, 127, 127)))
            center_x = width  - (3*i+2)*radius
            center_y = height / 2
            painter.drawEllipse(center_x - radius, 
                                center_y - radius,
                                2*radius, 
                                2*radius)
        painter.end()

    def timerEvent(self, event):
        """custom timer event, updating the animation"""
        self.update()
        self.counter += 1
        self.highlighted_orb -= 1
        if self.highlighted_orb < 0:
            self.highlighted_orb = self.orbs