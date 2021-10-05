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

import six

from ...core.qt import QtCore, QtWidgets, QtGui
from camelot.core.utils import ugettext as _
from .decorated_line_edit import DecoratedLineEdit
from .action_widget import AbstractActionWidget

class SimpleSearchControl(DecoratedLineEdit, AbstractActionWidget):
    """A control that displays a single text field in which search keywords can
    be typed

    emits a search and a cancel signal if the user starts or cancels the search
    """

    def __init__( self, action, gui_context, parent ):
        DecoratedLineEdit.__init__(self, parent)
        self.init(action, gui_context)
        #
        # The search timer reduced the number of search signals that are
        # emitted, by waiting for the next keystroke before emitting the
        # search signal
        #
        timer = QtCore.QTimer( self )
        timer.setInterval( 300 )
        timer.setSingleShot( True )
        timer.setObjectName( 'timer' )
        timer.timeout.connect(self.start_search)
        self.setPlaceholderText(_('Search...'))
        self.returnPressed.connect(self.start_search)
        self.textEdited.connect(self._start_search_timer)
        shortcut = QtWidgets.QShortcut(
            QtGui.QKeySequence(QtGui.QKeySequence.Find), self
        )
        shortcut.activated.connect(self.activate_search)

    @QtCore.qt_slot()
    def activate_search(self):
        self.setFocus(QtCore.Qt.ShortcutFocusReason)

    @QtCore.qt_slot()
    @QtCore.qt_slot(str)
    def _start_search_timer(self, str=''):
        timer = self.findChild( QtCore.QTimer, 'timer' )
        if timer is not None:
            timer.start()

    @QtCore.qt_slot()
    @QtCore.qt_slot(str)
    def start_search(self, str=''):
        timer = self.findChild( QtCore.QTimer, 'timer' )
        if timer is not None:
            timer.stop()
        text = six.text_type(self.text())
        self.run_action(text)
