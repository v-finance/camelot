#  ============================================================================
#
#  Copyright (C) 2007-2013 Conceptive Engineering bvba. All rights reserved.
#  www.conceptive.be / info@conceptive.be
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
#  visit www.python-camelot.com or contact info@conceptive.be
#
#  This file is provided AS IS with NO WARRANTY OF ANY KIND, INCLUDING THE
#  WARRANTY OF DESIGN, MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE.
#
#  For use of this library in commercial applications, please contact
#  info@conceptive.be
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

    def __init__(self, parent=None, editable=True, field_name='color', **kwargs):
        CustomEditor.__init__(self, parent)
        self.setSizePolicy( QtGui.QSizePolicy.Preferred,
                            QtGui.QSizePolicy.Fixed )        
        self.setObjectName( field_name )
        layout = QtWidgets.QVBoxLayout(self)
        layout.setSpacing(0)
        layout.setContentsMargins( 0, 0, 0, 0)
        self.color_button = QtWidgets.QPushButton(parent)
        self.color_button.setMaximumSize(QtCore.QSize(20, 20))
        layout.addWidget(self.color_button)
        if editable:
            self.color_button.clicked.connect(self.buttonClicked)
        self.setLayout(layout)
        self._color = None

    def get_value(self):
        color = self.getColor()
        if color:
            value = (color.red(), color.green(), color.blue(), color.alpha())
        else:
            value = None
        return CustomEditor.get_value(self) or value

    def set_value(self, value):
        value = CustomEditor.set_value(self, value)
        if value:
            color = QtGui.QColor()
            color.setRgb(*value)
            self.setColor(color)
        else:
            self.setColor(value)

    def getColor(self):
        return self._color

    def set_enabled(self, editable=True):
        self.color_button.setEnabled(editable)

    def setColor(self, color):
        pixmap = QtGui.QPixmap(16, 16)
        if color is not None:
            pixmap.fill(color)
        else:
            pixmap.fill(Qt.transparent)
        self.color_button.setIcon(QtGui.QIcon(pixmap))
        self._color = color

    def buttonClicked(self, raised):
        options = QtGui.QColorDialog.ShowAlphaChannel
        if self._color is None:
            color = Qt.white
        else:
            color = self._color
        color = QtGui.QColorDialog.getColor(
            color, self.parent(), ugettext('Select Color'),
            options,
        )
        if color.isValid():
            # transparant colors become None
            if color.alpha() == 0:
                self.setColor(None)
            else:
                self.setColor(color)
        self.editingFinished.emit()




