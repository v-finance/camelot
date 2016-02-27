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

from ....core.qt import QtGui, QtCore, Qt, QtWidgets
from .customeditor import CustomEditor
from camelot.view.art import Icon

default_icon_names = [
    'face-angel',
    'face-crying',
    'face-devilish',
    'face-glasses',
    'face-grin',
    'face-kiss',
    'face-monkey',
    'face-plain',
    'face-sad',
    'face-smile',
    'face-smile-big',
    'face-surprise',
    'face-wink',
]

default_icons = list( (icon_name, Icon('tango/16x16/emotes/%s.png'%icon_name)) for icon_name in default_icon_names)

class SmileyEditor(CustomEditor):

    def __init__(self, 
                 parent, 
                 editable = True, 
                 icons = default_icons, 
                 field_name = 'icons',
                 **kwargs):
        CustomEditor.__init__(self, parent)
        self.setSizePolicy( QtGui.QSizePolicy.Preferred,
                            QtGui.QSizePolicy.Fixed )        
        self.setObjectName( field_name )
        self.box = QtWidgets.QComboBox()
        self.box.setFrame(True)
        self.box.setEditable(False)
        self.name_by_position = {0:None}
        self.position_by_name = {None:0}

        self.box.addItem('')
        for i,(icon_name, icon) in enumerate(icons):
            self.name_by_position[i+1] = icon_name
            self.position_by_name[icon_name] = i+1
            self.box.addItem(icon.getQIcon(), '')
            self.box.setFixedHeight(self.get_height())

        self.setFocusPolicy(Qt.StrongFocus)
        layout = QtWidgets.QHBoxLayout(self)
        layout.setContentsMargins( 0, 0, 0, 0)
        layout.setSpacing(0)
        self.setAutoFillBackground(True)
        if not editable:
            self.box.setEnabled(False)
        else:
            self.box.setEnabled(True)

        self.box.activated.connect( self.smiley_changed )
        layout.addWidget(self.box)
        layout.addStretch()
        self.setLayout(layout)

    def get_value(self):
        position = self.box.currentIndex()
        return CustomEditor.get_value(self) or self.name_by_position[position]

    def set_enabled(self, editable=True):
        self.box.setEnabled(editable)

    @QtCore.qt_slot( int )
    def smiley_changed(self, _index ):
        self.editingFinished.emit()

    def set_value(self, value):
        name = CustomEditor.set_value(self, value)
        self.box.setCurrentIndex( self.position_by_name[name] )


