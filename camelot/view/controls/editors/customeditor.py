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

from PyQt4 import QtGui
from PyQt4 import QtCore

from camelot.view.proxy import ValueLoading

def set_background_color_palette(widget, background_color):
    """
    Set the palette of a widget to have a cerain background color.
    :param widget: a QWidget
    :param background_color: a QColor
    """
    #
    # WARNING : Changing this code requires extensive testing of all editors
    # in all states on all platforms (Mac, Linux, Win XP, Win Vista, Win 7)
    #
    if background_color not in (None, ValueLoading):
        palette = QtGui.QPalette( widget.palette() )
        for x in [QtGui.QPalette.Active, QtGui.QPalette.Inactive, QtGui.QPalette.Disabled]:
            # 
            # backgroundRole : role that is used to render the background, If role is QPalette.NoRole, 
            #                  then the widget inherits its parent's background role
            # Window : general background color
            # Base : background color for text entry widgets
            #
            for y in [widget.backgroundRole(), QtGui.QPalette.Window, QtGui.QPalette.Base]:
                palette.setColor(x, y, background_color)
        widget.setPalette( palette )
    else:
        widget.setPalette( QtGui.QApplication.palette() )
        
def draw_tooltip_visualization(widget):
    """
    Draws a small visual indication in the top-left corner of a widget.
    :param widget: a QWidget
    """
    painter = QtGui.QPainter(widget)
    painter.drawPixmap(QtCore.QPoint(0, 0), QtGui.QPixmap(':/tooltip_visualization_7x7_glow.png'))    
        
class AbstractCustomEditor(object):
    """
    Helper class to be used to build custom editors.
    This class provides functionality to store and retrieve 
    `ValueLoading` as an editor's value.

    Guidelines for implementing CustomEditors :

    * When an editor consists of multiple widgets, one widget must be the focusProxy
      of the editor, to have that widget immediately activated when the user single
      clicks in the table view.
    
    * When an editor has widgets that should not get selected when the user tabs
      through the editor, setFocusPolicy(Qt.ClickFocus) should be called on those
      widgets.
    """

    def __init__(self):
        self._value_loading = True
        self.value_is_none = False

    def set_value(self, value):
        if value == ValueLoading:
            self._value_loading = True
            return None
        else:
            self._value_loading = False
            if value is None:
                self.value_is_none = True
            else:
                self.value_is_none = False
            return value

    def get_value(self):
        if self._value_loading:
            return ValueLoading
        return None

    def set_field_attributes(self, editable = True,
                                   background_color = None,
                                   tooltip = '', **kwargs):
        self.set_background_color(background_color)

    """
    Get the 'standard' height for a cell
    """
    def get_height(self):
        height = [QtGui.QLineEdit().sizeHint().height(),
               QtGui.QDateEdit().sizeHint().height(),
               QtGui.QDateTimeEdit().sizeHint().height(),
               QtGui.QSpinBox().sizeHint().height(),
               QtGui.QDateEdit().sizeHint().height(),
               QtGui.QComboBox().sizeHint().height()]

        finalHeight = max(height)

        return finalHeight

    def set_background_color(self, background_color):
        set_background_color_palette( self, background_color )

class CustomEditor(QtGui.QWidget, AbstractCustomEditor):
    """
    Base class for implementing custom editor widgets.
    This class provides dual state functionality.  Each 
    editor should have the posibility to have `ValueLoading`
    as its value, specifying that no value has been set yet.
    """

    editingFinished = QtCore.pyqtSignal()
    valueChanged = QtCore.pyqtSignal()

    def __init__(self, parent):
        QtGui.QWidget.__init__(self, parent)
        AbstractCustomEditor.__init__(self)
        
    def paintEvent(self, event):
        super(CustomEditor, self).paintEvent(event)        
        if self.toolTip():
            draw_tooltip_visualization(self)

