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

from ...core.backend import get_root_backend
from ...core.qt import QtCore, QtWidgets
from ..art import Pixmap

working_pixmap = Pixmap( 'process-working.png' )

class BusyWidget(QtWidgets.QLabel):
    """A widget indicating the application is performing some background task.
    The widget acts as an overlay of its parent widget and displays animating
    orbs"""

    def __init__(self, parent = None):
        super( BusyWidget, self ).__init__( parent )
        pixmap = working_pixmap.getQPixmap()
        rows = 4
        self.cols = 8
        self.frame_height = pixmap.height() / rows
        self.frame_width = pixmap.width() / self.cols
        self.orbs = rows * self.cols
        self.highlighted_orb = 0
        self.timer = None
        self.setSizePolicy( QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Expanding )
        get_root_backend().action_runner().busy.connect(self.set_busy)

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
        if busy_state and self.timer is None:
            self.timer = self.startTimer( 200 )
        else:
            if self.timer:
                self.killTimer(self.timer)
                self.timer = None
            self.highlighted_orb = 0
        self.update_pixmap()

    def timerEvent(self, event):
        """custom timer event, updating the animation"""
        self.update_pixmap()
        self.highlighted_orb += 1
        if self.highlighted_orb >= self.orbs:
            self.highlighted_orb = 1
    
    def update_pixmap(self):
        pixmap = working_pixmap.getQPixmap()
        row, col = divmod(self.highlighted_orb, self.cols)
        self.setPixmap(pixmap.copy(
            self.frame_width * col,
            self.frame_height * row,
            self.frame_width,self.frame_height
        ))



