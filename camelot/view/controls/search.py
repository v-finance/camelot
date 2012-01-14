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

from PyQt4 import QtCore, QtGui

from camelot.view.art import Icon
from camelot.core.utils import ugettext as _
from camelot.view.controls.abstract_widget import AbstractSearchWidget

class SimpleSearchControl(AbstractSearchWidget):
    """A control that displays a single text field in which search keywords can
    be typed

    emits a search and a cancel signal if the user starts or cancels the search
    """

    def __init__(self, parent):
        QtGui.QWidget.__init__(self, parent)
        layout = QtGui.QHBoxLayout()
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
        self.search_button = QtGui.QToolButton()
        icon = Icon('tango/16x16/actions/system-search.png').getQIcon()
        self.search_button.setIcon(icon)
        self.search_button.setIconSize(QtCore.QSize(14, 14))
        self.search_button.setAutoRaise(True)
        self.search_button.setToolTip(_('Expand or collapse search options'))
        self.search_button.clicked.connect( self.emit_expand_search_options )

        # Search input
        from camelot.view.controls.decorated_line_edit import DecoratedLineEdit
        self.search_input = DecoratedLineEdit(self)
        self.search_input.set_background_text(_('Search...'))
        #self.search_input.setStyleSheet('QLineEdit{ border-radius: 0.25em;}')
        self.search_input.returnPressed.connect( self.emit_search )
        self.search_input.textEdited.connect( self._start_search_timer )
        self.search_input.arrow_down_key_pressed.connect(self.on_arrow_down_key_pressed)

        self.setFocusProxy( self.search_input )

        # Cancel button
        self.cancel_button = QtGui.QToolButton()
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

    @QtCore.pyqtSlot()
    @QtCore.pyqtSlot(str)
    def _start_search_timer(self, str=''):
        timer = self.findChild( QtCore.QTimer, 'timer' )
        if timer:
            timer.stop()
            timer.start()
        
    @QtCore.pyqtSlot()
    def emit_expand_search_options(self):
        self.expand_search_options_signal.emit()

    @QtCore.pyqtSlot()
    @QtCore.pyqtSlot(str)
    def emit_search(self, str=''):
        timer = self.findChild( QtCore.QTimer, 'timer' )
        if timer:
            timer.stop()
        text = unicode(self.search_input.user_input())
        self.search_signal.emit( text )

    @QtCore.pyqtSlot()
    def emit_cancel(self):
        timer = self.findChild( QtCore.QTimer, 'timer' )
        if timer:
            timer.stop()
        self.search_input.setText('')
        self.cancel_signal.emit()

    @QtCore.pyqtSlot()
    def on_arrow_down_key_pressed(self):
        self.on_arrow_down_signal.emit()

