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

"""Functionality common to TableViews and FormViews"""

import itertools
import logging

from ...admin.action import RenderHint
from ...core.backend import get_root_backend
from ...core.qt import QtCore, QtGui, QtWidgets
from .action_widget import AbstractActionWidget

LOGGER = logging.getLogger(__name__)

class ViewWithActionsMixin(object):

    _rendered_action_counter = itertools.count()

    @classmethod
    def _register_rendered_action(cls, qobject):
        next_rendered_action = cls._rendered_action_counter.__next__()
        rendered_action_name = 'rendered_action_{}'.format(next_rendered_action)
        qobject.setObjectName(rendered_action_name)
        return rendered_action_name

    def render_action(self, render_hint, action_route, gui_context, parent):
        if render_hint in (RenderHint.TOOL_BUTTON, RenderHint.CLOSE_BUTTON):
            qobject = QtWidgets.QToolButton(parent)
            if render_hint == RenderHint.TOOL_BUTTON:
                qobject.clicked.connect(self.button_clicked)
            else:
                qobject.clicked.connect(self.validate_close)
        elif render_hint == RenderHint.COMBO_BOX:
            qobject = QtWidgets.QComboBox(parent)
            qobject.activated.connect(self.combobox_activated)
        elif render_hint == RenderHint.PUSH_BUTTON:
            qobject = QtWidgets.QPushButton(parent)
            qobject.clicked.connect(self.button_clicked)
        elif render_hint == RenderHint.LABEL:
            qobject = QtWidgets.QLabel(parent)
        else:
            raise Exception('Unhandled render hint {} for {}'.format(
                render_hint, action_route
            ))
        qobject.setProperty('action_route', action_route)
        rendered_action_name = self._register_rendered_action(qobject)
        gui_context.action_routes[action_route] = rendered_action_name
        return qobject

    def set_action_state(self, parent, action_route, action_state):
        for action_widget in parent.findChildren(QtWidgets.QPushButton):
            if action_widget.property('action_route') == action_route:
                AbstractActionWidget.set_pushbutton_state(
                    action_widget, action_state, parent, self.menu_triggered
                )
                return
        for action_widget in parent.findChildren(QtWidgets.QToolButton):
            if action_widget.property('action_route') == action_route:
                AbstractActionWidget.set_toolbutton_state(
                    action_widget, action_state, self.menu_triggered
                )
                return
        for action_widget in parent.findChildren(QtWidgets.QLabel):
            if action_widget.property('action_route') == action_route:
                AbstractActionWidget.set_label_state(action_widget, action_state)
                return
        for action_widget in parent.findChildren(QtWidgets.QComboBox):
            if action_widget.property('action_route') == action_route:
                AbstractActionWidget.set_combobox_state(action_widget, action_state)
                return
        LOGGER.warn('No widget found with action route {}'.format(action_route))

    def run_action(self, action_widget, gui_context_name, model_context_name, mode):
        action_name = tuple(action_widget.property('action_route') or [])
        if len(action_name):
            root_backend = get_root_backend()
            root_backend.run_action(
                gui_context_name, action_name, model_context_name, mode
            )


class AbstractView(QtWidgets.QWidget, ViewWithActionsMixin):
    """A string used to format the title of the view ::
    title_format = 'Movie rental overview'

    .. attribute:: header_widget

    The widget class to be used as a header in the table view::

    header_widget = None
    """

    title_format = ''
    header_widget = None

    title_changed_signal = QtCore.qt_signal(str)
    icon_changed_signal = QtCore.qt_signal(QtGui.QIcon)
    close_clicked_signal = QtCore.qt_signal()

    @property
    def view(self):
        return self

    @QtCore.qt_slot()
    def validate_close(self):
        return True

    @QtCore.qt_slot()
    def refresh(self):
        """Refresh the data in the current view"""
        pass

    @QtCore.qt_slot(object)
    def change_title(self, new_title):
        """Will emit the title_changed_signal"""
        #import sip
        #if not sip.isdeleted(self):
        self.title_changed_signal.emit(str(new_title))
        
    @QtCore.qt_slot(object)
    def change_icon(self, new_icon):
        self.icon_changed_signal.emit(new_icon)
