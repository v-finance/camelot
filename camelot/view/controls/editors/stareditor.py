#  ============================================================================
#
#  Copyright (C) 2007-2010 Conceptive Engineering bvba. All rights reserved.
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

from PyQt4 import QtGui
from PyQt4.QtCore import Qt

from customeditor import CustomEditor
from camelot.view.art import Icon

class StarEditor(CustomEditor):

    def __init__(self, parent, maximum=5, editable=True, **kwargs):
        CustomEditor.__init__(self, parent)
        self.setFocusPolicy(Qt.StrongFocus)
        layout = QtGui.QHBoxLayout(self)
        layout.setMargin(0)
        layout.setSpacing(0)
        self.starIcon = Icon('tango/16x16/status/weather-clear.png').getQIcon()
        self.noStarIcon = Icon('tango/16x16/status/weather-clear-noStar.png').getQIcon()
        self.starCount = 5
        self.buttons = []
        for i in range(self.starCount):
            button = QtGui.QToolButton(self)
            button.setIcon(self.noStarIcon)
            if editable:
                button.setAutoRaise(True)
            else:
                button.setAutoRaise(True)
                button.setDisabled(True)
            button.setFixedHeight(self.get_height())
            self.buttons.append(button)

        def createStarClick(i):
            return lambda:self.starClick(i+1)

        for i in range(self.starCount):
            self.buttons[i].clicked.connect(createStarClick(i))

        for i in range(self.starCount):
            layout.addWidget(self.buttons[i])
        layout.addStretch()
        self.setLayout(layout)

    def get_value(self):
        return CustomEditor.get_value(self) or self.stars

    def set_enabled(self, editable=True):
        for button in self.buttons:
            button.setEnabled(editable)
            button.update()
        self.set_value(self.stars)

    def starClick(self, value):
        if self.stars == value:
            self.stars -= 1
        else:
            self.stars = int(value)
        for i in range(self.starCount):
            if i+1 <= self.stars:
                self.buttons[i].setIcon(self.starIcon)
            else:
                self.buttons[i].setIcon(self.noStarIcon)
        self.editingFinished.emit()

    def set_value(self, value):
        value = CustomEditor.set_value(self, value) or 0
        self.stars = int(value)
        for i in range(self.starCount):
            if i+1 <= self.stars:
                self.buttons[i].setIcon(self.starIcon)
            else:
                self.buttons[i].setIcon(self.noStarIcon)

    def set_background_color(self, background_color):
        return False

