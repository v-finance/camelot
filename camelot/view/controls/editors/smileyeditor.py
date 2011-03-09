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

class SmileyEditor(CustomEditor):

    def __init__(self, parent, img='face-plain', editable=True, **kwargs):
        CustomEditor.__init__(self, parent)
        self.box = QtGui.QComboBox()
        self.box.setFrame(True)
        self.box.setEditable(False)
        self.allSmileys = []

        self.allSmileys.append('face-angel')
        self.allSmileys.append('face-crying')
        self.allSmileys.append('face-devilish')
        self.allSmileys.append('face-glasses')
        self.allSmileys.append('face-grin')
        self.allSmileys.append('face-kiss')
        self.allSmileys.append('face-monkey')
        self.allSmileys.append('face-plain')
        self.allSmileys.append('face-sad')
        self.allSmileys.append('face-smile')
        self.allSmileys.append('face-smile-big')
        self.allSmileys.append('face-surprise')
        self.allSmileys.append('face-wink')

        for i, value in enumerate(self.allSmileys):
            imgPath = 'tango/16x16/emotes/' + value + '.png'
            icon = Icon(imgPath).getQIcon()

            self.box.addItem(icon, '')
            self.box.setFixedHeight(self.get_height())

            if value == 'face-plain':
                self.box.setCurrentIndex(i)


        self.setFocusPolicy(Qt.StrongFocus)
        layout = QtGui.QHBoxLayout(self)
        layout.setMargin(0)
        layout.setSpacing(0)
        self.img = img
        self.imgPath = 'tango/16x16/emotes/' + img + '.png'
        self.Icon = Icon(self.imgPath).getQIcon()
        self.setAutoFillBackground(True)
        #self.starCount = maximum
        if not editable:
            self.box.setEnabled(False)
        else:
            self.box.setEnabled(True)
        self.box.currentIndexChanged.connect(self.smiley_changed)

        layout.addWidget(self.box)
        layout.addStretch()
        self.setLayout(layout)

    def get_value(self):
        imgIndex = self.box.currentIndex()

        for i, emot in enumerate(self.allSmileys):
            if imgIndex == i:
                imgName = emot

        return CustomEditor.get_value(self) or imgName


    def set_enabled(self, editable=True):
        self.box.setEnabled(editable)

    def smiley_changed(self):
        self.editingFinished.emit()

    def set_value(self, value):
        value = CustomEditor.set_value(self, value) or 'face-plain'
        self.img = value
        #self.imgPath = 'tango/16x16/emotes/' + self.img + '.png'

        for i, smiley in enumerate(self.allSmileys):
            if smiley == self.img:
                self.box.setCurrentIndex(i)

