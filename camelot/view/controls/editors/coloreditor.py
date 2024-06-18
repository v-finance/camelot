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

from ....core.utils import ugettext
from ....core.qt import QtGui, QtCore, QtWidgets, Qt
from .customeditor import CustomEditor

class ColorEditor(CustomEditor):
    """
    This editor alows the user to select a color.  When the selected color is
    completely transparent, the value of the editor will be None.
    """

    def __init__(self, parent=None, field_name='color'):
        CustomEditor.__init__(self, parent)
        self.setSizePolicy(
            QtWidgets.QSizePolicy.Policy.Preferred,
            QtWidgets.QSizePolicy.Policy.Fixed
        )
        self.setObjectName(field_name)
        layout = QtWidgets.QVBoxLayout(self)
        layout.setSpacing(0)
        layout.setContentsMargins( 0, 0, 0, 0)
        color_button = QtWidgets.QPushButton(parent=self)
        color_button.setMaximumSize(QtCore.QSize(20, 20))
        color_button.setObjectName('color_button')
        layout.addWidget(color_button)
        color_button.clicked.connect(self.buttonClicked)
        self.setLayout(layout)
        self._color = None
        self._editable = None

    @classmethod
    def to_qcolor(self, value, invalid):
        if isinstance(value, QtGui.QColor):
            return value
        if (value is not None) and QtGui.QColor.isValidColor(value):
            return QtGui.QColor(value)
        return QtGui.QColor(invalid)

    def get_value(self):
        return self._color

    def set_value(self, value):
        if value != self._color:
            self._color = value
            pixmap = QtGui.QPixmap(16, 16)
            color = self.to_qcolor(value, Qt.GlobalColor.transparent)
            pixmap.fill(color)
            color_button = self.findChild(QtWidgets.QPushButton, 'color_button')
            if color_button is not None:
                color_button.setIcon(QtGui.QIcon(pixmap))

    def set_editable(self, editable):
        self._editable = editable

    @QtCore.qt_slot(bool)
    def buttonClicked(self, raised):
        if self._editable != True:
            return
        options = QtWidgets.QColorDialog.ColorDialogOption.ShowAlphaChannel
        qcolor = self.to_qcolor(self.get_value(), 'white')
        qcolor = QtWidgets.QColorDialog.getColor(
            qcolor, self.parent(), ugettext('Select Color'), options,
        )
        if qcolor.isValid():
            # transparant colors become None
            if qcolor.alpha() == 0:
                self.set_value(None)
            else:
                self.set_value(qcolor.name())
        self.editingFinished.emit()
