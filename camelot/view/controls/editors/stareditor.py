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

from ....core.qt import QtGui, QtWidgets, Qt
from .customeditor import CustomEditor
from camelot.view.art import Icon

class StarEditor( CustomEditor ):

    star_icon = Icon('tango/16x16/status/weather-clear.png')
    no_star_icon = Icon('tango/16x16/status/weather-clear-noStar.png')
        
    def __init__(self, 
                 parent, 
                 maximum = 5, 
                 editable = True, 
                 field_name = 'star',
                 **kwargs):
        CustomEditor.__init__(self, parent)
        self.setSizePolicy( QtGui.QSizePolicy.Preferred,
                            QtGui.QSizePolicy.Fixed )        
        self.setObjectName( field_name )
        self.setFocusPolicy(Qt.StrongFocus)
        layout = QtWidgets.QHBoxLayout(self)
        layout.setContentsMargins( 0, 0, 0, 0)
        layout.setSpacing(0)

        self.maximum = maximum
        self.buttons = []
        for i in range(self.maximum):
            button = QtWidgets.QToolButton(self)
            button.setIcon(self.no_star_icon.getQIcon())
            button.setFocusPolicy(Qt.ClickFocus)
            if editable:
                button.setAutoRaise(True)
            else:
                button.setAutoRaise(True)
                button.setDisabled(True)
            button.setFixedHeight(self.get_height())
            self.buttons.append(button)

        def createStarClick(i):
            return lambda:self.starClick(i+1)

        for i in range(self.maximum):
            self.buttons[i].clicked.connect(createStarClick(i))

        for i in range(self.maximum):
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
        for i in range(self.maximum):
            if i+1 <= self.stars:
                self.buttons[i].setIcon(self.star_icon.getQIcon())
            else:
                self.buttons[i].setIcon(self.no_star_icon.getQIcon())
        self.editingFinished.emit()

    def set_value(self, value):
        value = CustomEditor.set_value(self, value) or 0
        self.stars = int(value)
        for i in range(self.maximum):
            if i+1 <= self.stars:
                self.buttons[i].setIcon(self.star_icon.getQIcon())
            else:
                self.buttons[i].setIcon(self.no_star_icon.getQIcon())

    def set_background_color(self, background_color):
        return False





