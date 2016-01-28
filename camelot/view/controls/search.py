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

from ...core.qt import QtCore, QtWidgets
from camelot.view.art import Icon
from camelot.core.utils import ugettext as _
from .abstract_widget import AbstractSearchWidget
from .decorated_line_edit import DecoratedLineEdit

class SimpleSearchControl(AbstractSearchWidget):
    """A control that displays a single text field in which search keywords can
    be typed

    emits a search and a cancel signal if the user starts or cancels the search
    """

    def __init__(self, parent):
        QtWidgets.QWidget.__init__(self, parent)
        layout = QtWidgets.QHBoxLayout()
        layout.setSpacing(0)
        layout.setContentsMargins(3, 3, 3, 3)
        
        #
        # The search timer reduced the number of search signals that are
        # emitted, by waiting for the next keystroke before emitting the
        # search signal
        #
        timer = QtCore.QTimer( self )
        timer.setInterval( 300 )
        timer.setSingleShot( True )
        timer.setObjectName( 'timer' )
        timer.timeout.connect( self.emit_search )

        # Search button
        self.search_button = QtWidgets.QToolButton()
        icon = Icon('tango/16x16/actions/system-search.png').getQIcon()
        self.search_button.setIcon(icon)
        self.search_button.setIconSize(QtCore.QSize(14, 14))
        self.search_button.setAutoRaise(True)
        self.search_button.setToolTip(_('Expand or collapse search options'))
        self.search_button.clicked.connect( self.emit_expand_search_options )

        # Search input
        self.search_input = DecoratedLineEdit(self)
        self.search_input.setPlaceholderText(_('Search...'))
        #self.search_input.setStyleSheet('QLineEdit{ border-radius: 0.25em;}')
        self.search_input.returnPressed.connect( self.emit_search )
        self.search_input.textEdited.connect( self._start_search_timer )
        self.search_input.arrow_down_key_pressed.connect(self.on_arrow_down_key_pressed)
        self.setFocusProxy(self.search_input)

        # Cancel button
        self.cancel_button = QtWidgets.QToolButton()
        icon = Icon('tango/16x16/actions/edit-clear.png').getQIcon()
        self.cancel_button.setIcon(icon)
        self.cancel_button.setIconSize(QtCore.QSize(14, 14))
        self.cancel_button.setAutoRaise(True)
        self.cancel_button.clicked.connect( self.emit_cancel )

        # Setup layout
        layout.addWidget(self.search_button)
        layout.addWidget(self.search_input)
        layout.addWidget(self.cancel_button)
        self.setLayout(layout)

    def search(self, search_text):
        """Start searching for search_text"""
        self.search_input.setText(search_text)
        self.emit_search()

    @QtCore.qt_slot()
    @QtCore.qt_slot(str)
    def _start_search_timer(self, str=''):
        timer = self.findChild( QtCore.QTimer, 'timer' )
        if timer is not None:
            timer.start()
        
    @QtCore.qt_slot()
    def emit_expand_search_options(self):
        self.expand_search_options_signal.emit()

    @QtCore.qt_slot()
    @QtCore.qt_slot(str)
    def emit_search(self, str=''):
        timer = self.findChild( QtCore.QTimer, 'timer' )
        if timer is not None:
            timer.stop()
        text = six.text_type(self.search_input.text())
        self.search_signal.emit( text )

    @QtCore.qt_slot()
    def emit_cancel(self):
        timer = self.findChild( QtCore.QTimer, 'timer' )
        if timer is not None:
            timer.stop()
        self.search_input.setText('')
        self.cancel_signal.emit()

    @QtCore.qt_slot()
    def on_arrow_down_key_pressed(self):
        self.on_arrow_down_signal.emit()



