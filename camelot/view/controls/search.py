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

from PyQt4 import QtCore, QtGui
from camelot.view.art import Icon
from camelot.core.utils import ugettext as _

class SimpleSearchControl(QtGui.QWidget):
    """A control that displays a single text field in which search keywords can
  be typed

  emits a search and a cancel signal if the user starts or cancels the search
  """

    def __init__(self, parent):
        QtGui.QWidget.__init__(self, parent)
        layout = QtGui.QHBoxLayout()
        layout.setSpacing(0)
        layout.setMargin(3)

        # Search button
        self.search_button = QtGui.QToolButton()
        icon = Icon('tango/16x16/actions/system-search.png').getQIcon()
        self.search_button.setIcon(icon)
        self.search_button.setIconSize(QtCore.QSize(14, 14))
        self.search_button.setAutoRaise(True)
        self.connect(self.search_button,
                     QtCore.SIGNAL('clicked()'),
                     self.emit_search)

        # Search input
        self.search_input = QtGui.QLineEdit()
        self.search_input.setToolTip(_('type words to search for'))
        #self.search_input.setStyleSheet('QLineEdit{ border-radius: 0.25em;}')
        self.connect(self.search_input,
                     QtCore.SIGNAL('returnPressed()'),
                     self.emit_search)
        self.connect(self.search_input,
                     QtCore.SIGNAL('textEdited(const QString&)'),
                     self.emit_search)

        # Cancel button
        self.cancel_button = QtGui.QToolButton()
        icon = Icon('tango/16x16/actions/edit-clear.png').getQIcon()
        self.cancel_button.setIcon(icon)
        self.cancel_button.setIconSize(QtCore.QSize(14, 14))
        self.cancel_button.setAutoRaise(True)
        self.connect(self.cancel_button,
                     QtCore.SIGNAL('clicked()'),
                     self.emit_cancel)

        # Setup layout
        layout.addWidget(self.search_button)
        layout.addWidget(self.search_input)
        layout.addWidget(self.cancel_button)
        self.setLayout(layout)

    def search(self, search_text):
        """Start searching for search_text"""
        self.search_input.setText(search_text)
        self.emit_search()

    def emit_search(self):
        text = str(self.search_input.text())
        self.emit(QtCore.SIGNAL('search'), text)

    def emit_cancel(self):
        self.search_input.setText('')
        self.emit(QtCore.SIGNAL('cancel'))
