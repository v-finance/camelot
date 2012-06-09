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

from PyQt4 import QtGui, QtCore
from PyQt4.QtCore import Qt

from camelot.view.art import Pixmap
from camelot.view.model_thread import get_model_thread

working_pixmap = Pixmap( 'tango/32x32/animations/process-working.png' )

class BusyWidget( QtGui.QLabel ):
    """A widget indicating the application is performing some background task.
    The widget acts as an overlay of its parent widget and displays animating
    orbs"""

    def __init__(self, parent = None):
        super( BusyWidget, self ).__init__( parent )
        palette = QtGui.QPalette( self.palette() )
        palette.setColor( palette.Background, Qt.transparent )
        self.setPalette( palette )
        self.setAttribute( Qt.WA_TransparentForMouseEvents )
        pixmap = working_pixmap.getQPixmap()
        rows = 4
        self.cols = 8
        self.frame_height = pixmap.height() / rows
        self.frame_width = pixmap.width() / self.cols
        self.orbs = rows * self.cols
        self.highlighted_orb = 0
        self.timer = None
        self.setSizePolicy( QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Expanding )
        mt = get_model_thread()
        mt.thread_busy_signal.connect( self.set_busy )
        # the model thread might already be busy before we connected to it
        self.set_busy( mt.busy() )

    @QtCore.pyqtSlot(bool)
    def set_busy(self, busy_state):
        """start/stop the animation
        :arg busy_state: True or False
        """
        #
        # the set_busy method might get called multiple times with 
        # busy_state=True before calls with busy_state=False,
        # so a check on self.timer is needed to prevent multiple timers
        # from being started
        #
        if busy_state and self.timer==None:
            self.timer = self.startTimer( 200 )
        else:
            if self.timer:
                self.killTimer(self.timer)
                self.timer = None
            self.highlighted_orb = 0
        self.update()
    
    def paintEvent(self, event):
        """custom paint, painting the orbs"""
        painter = QtGui.QPainter()
        painter.begin( self )
        pixmap = working_pixmap.getQPixmap()
        row, col = divmod( self.highlighted_orb, self.cols )
        painter.drawPixmap( self.width() - self.frame_width, 
                            self.height() - self.frame_height, 
                            pixmap, 
                            self.frame_width * col, 
                            self.frame_height * row, 
                            self.frame_width, 
                            self.frame_height )
        painter.end()

    def timerEvent(self, event):
        """custom timer event, updating the animation"""
        self.update()
        self.highlighted_orb += 1
        if self.highlighted_orb > self.orbs:
            self.highlighted_orb = 0
