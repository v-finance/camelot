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
from camelot.view.model_thread import get_model_thread

working_pixmap = Pixmap( 'tango/32x32/animations/process-working.png' )

class BusyWidget( QtWidgets.QLabel ):
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

    @QtCore.qt_slot(bool)
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


