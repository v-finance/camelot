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

from ....core.qt import QtGui, QtCore, QtWidgets, variant_to_py

from camelot.admin.action import FieldActionGuiContext
from camelot.view.proxy import ValueLoading
from ...model_thread import post
from ..action_widget import ActionToolbutton

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
        widget.setPalette( QtWidgets.QApplication.palette() )

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

    * Editor should set their size policy, for most editor this means their
      vertical size policy should be  `QtGui.QSizePolicy.Fixed`

    """

    def __init__(self):
        self.setProperty('value_loading', True)
        self.field_attributes = {}
        self.field_label = None

    def set_label(self, label):
        self.field_label = label

    def set_value(self, value):
        if value is ValueLoading:
            self.setProperty('value_loading', True)
            return None
        else:
            self.setProperty('value_loading', False)
            return value

    def get_value(self):
        if variant_to_py(self.property('value_loading')):
            return ValueLoading
        return None

    def get_field_attributes(self):
        return self.field_attributes
    
    def set_field_attributes(self, **kwargs):
        self.set_background_color(kwargs.get('background_color', None))
        self.field_attributes = kwargs
        if self.field_label is not None:
            self.field_label.set_field_attributes(**kwargs)

    """
    Get the 'standard' height for a cell
    """
    def get_height(self):
        height = [QtWidgets.QLineEdit().sizeHint().height(),
               QtGui.QDateEdit().sizeHint().height(),
               QtGui.QDateTimeEdit().sizeHint().height(),
               QtGui.QSpinBox().sizeHint().height(),
               QtGui.QDateEdit().sizeHint().height(),
               QtWidgets.QComboBox().sizeHint().height()]

        finalHeight = max(height)

        return finalHeight

    def set_background_color(self, background_color):
        set_background_color_palette( self, background_color )

class CustomEditor(QtWidgets.QWidget, AbstractCustomEditor):
    """
    Base class for implementing custom editor widgets.
    This class provides dual state functionality.  Each
    editor should have the posibility to have `ValueLoading`
    as its value, specifying that no value has been set yet.
    """

    editingFinished = QtCore.qt_signal()
    valueChanged = QtCore.qt_signal()

    def __init__(self, parent):
        QtWidgets.QWidget.__init__(self, parent)
        AbstractCustomEditor.__init__(self)
        self.gui_context = FieldActionGuiContext()
        self.gui_context.editor = self

    def paintEvent(self, event):
        super(CustomEditor, self).paintEvent(event)
        if self.toolTip():
            draw_tooltip_visualization(self)

    def add_actions(self, actions, layout):
        for action in actions:
            action_widget = action.render(self.gui_context, self)
            action_widget.setFixedHeight(self.get_height())
            layout.addWidget(action_widget)

    def update_actions(self):
        model_context = self.gui_context.create_model_context()
        for action_action in self.findChildren(ActionToolbutton):
            post(action_action.action.get_state, action_action.set_state,
                 args=(model_context,))
