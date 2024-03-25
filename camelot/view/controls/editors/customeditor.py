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

from ....core.qt import QtGui, QtCore, QtWidgets, Qt

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
    if background_color is not None:
        palette = QtGui.QPalette(widget.palette())
        for x in [QtGui.QPalette.ColorGroup.Active, QtGui.QPalette.ColorGroup.Inactive,
                  QtGui.QPalette.ColorGroup.Disabled]:
            #
            # backgroundRole : role that is used to render the background, If
            #                  role is QPalette.ColorRole.NoRole, then the widget
            #                  inherits its parent's background role
            # Window : general background color
            # Base : background color for text entry widgets
            #
            for y in [widget.backgroundRole(), QtGui.QPalette.ColorRole.Window,
                      QtGui.QPalette.ColorRole.Base]:
                palette.setColor(x, y, background_color)
        widget.setPalette(palette)
    else:
        widget.setPalette(QtWidgets.QApplication.palette())


class AbstractCustomEditor(object):
    """
    Helper class to be used to build custom editors.

    Guidelines for implementing CustomEditors :

    * When an editor consists of multiple widgets, one widget must be the
      focusProxy of the editor, to have that widget immediately activated when
      the user single clicks in the table view.

    * When an editor has widgets that should not get selected when the user
      tabs through the editor, setFocusPolicy(Qt.FocusPolicy.ClickFocus) should be called
      on those widgets.

    * Editor should set their size policy, for most editor this means their
      vertical size policy should be  `QtWidgets.QSizePolicy.Policy.Fixed`
    """

    def __init__(self):
        # self.isVisible() is not updated directly (e.g. the ancestors are not (yet) visible)
        self._visible = True
        self.nullable = True
        self.field_label = None

    def set_label(self, label):
        self.field_label = label
        # set label might be called after a set_visible/set_nullable, so
        # immediately update the attributes of the label
        self.field_label.set_visible(self._visible)
        self.field_label.set_nullable(self.nullable)

    def set_editable(self, editable):
        pass

    def set_nullable(self, nullable):
        self.nullable = nullable
        if self.field_label is not None:
            self.field_label.set_nullable(nullable)

    def set_tooltip(self, tooltip):
        self.setToolTip(str(tooltip or ''))

    def set_visible(self, visible):
        self._visible = visible
        self.setVisible(visible)
        if self.field_label is not None:
            self.field_label.set_visible(visible)

    def set_focus_policy(self, focus_policy):
        pass

    def set_prefix(self, prefix):
        pass

    def set_suffix(self, suffix):
        pass

    def set_single_step(self, single_step):
        pass

    def set_precision(self, precision):
        pass

    def set_minimum(self, minimum):
        pass

    def set_maximum(self, maximum):
        pass

    def set_directory(self, directory):
        pass

    def set_completer_state(self, completer_state):
        pass

    def set_validator_state(self, validator_state):
        pass

    def set_background_color(self, background_color):
        set_background_color_palette(self, background_color)


class CustomEditor(QtWidgets.QWidget, AbstractCustomEditor):
    """
    Base class for implementing custom editor widgets.
    This class provides dual state functionality.
    """

    editingFinished = QtCore.qt_signal()
    valueChanged = QtCore.qt_signal()
    completionPrefixChanged = QtCore.qt_signal(str)
    actionTriggered = QtCore.qt_signal(list, object)

    _font_height = None
    _font_width = None

    def __init__(self, parent, column_width=None):
        QtWidgets.QWidget.__init__(self, parent)
        AbstractCustomEditor.__init__(self)

        if CustomEditor._font_width is None:
            font_metrics = QtGui.QFontMetrics(self.font())
            CustomEditor._font_height = font_metrics.height()
            CustomEditor._font_width = font_metrics.averageCharWidth()

        if column_width is None:
            self.size_hint_width = None
        else:
            self.size_hint_width = column_width * CustomEditor._font_width

    def get_height(self):
        """
        Get the 'standard' height for a cell
        """
        return self.contentsRect().height()

    @QtCore.qt_slot()
    def action_button_clicked(self):
        self.actionTriggered.emit(self.sender().property('action_route'), None)

    @QtCore.qt_slot(bool)
    def action_menu_triggered(self, checked):
        mode = self.sender().data()
        action_route = self.sender().property('action_route')
        self.actionTriggered.emit(action_route, mode)

    def add_actions(self, action_routes, layout):
        for action_route in action_routes:
            action_widget = QtWidgets.QToolButton(parent=self)
            action_widget.setAutoRaise(True)
            action_widget.setFocusPolicy(Qt.FocusPolicy.ClickFocus)
            action_widget.setProperty('action_route', action_route)
            action_widget.setFixedHeight(min(action_widget.height(), self.get_height()))
            action_widget.clicked.connect(self.action_button_clicked)
            layout.addWidget(action_widget)

    def sizeHint(self):
        size_hint = super(CustomEditor, self).sizeHint()
        if self.size_hint_width is not None:
            size_hint.setWidth(max(size_hint.width(), self.size_hint_width))
        return size_hint
