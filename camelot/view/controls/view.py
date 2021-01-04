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

from ...admin.action import RenderHint
from ...core.qt import QtCore, QtGui, QtWidgets
from .action_widget import ActionAction, ActionPushButton, ActionLabel
from .filter_widget import ComboBoxFilterWidget, GroupBoxFilterWidget
from .search import SimpleSearchControl

class AbstractView(QtWidgets.QWidget):
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


    def render_action(self, action, parent):
        if action.render_hint == RenderHint.TOOL_BUTTON:
            return ActionAction(action, self.gui_context, parent)
        elif action.render_hint == RenderHint.COMBO_BOX:
            return ComboBoxFilterWidget(action, self.gui_context, parent)
        elif action.render_hint == RenderHint.GROUP_BOX:
            return GroupBoxFilterWidget(action, self.gui_context, parent)
        elif action.render_hint == RenderHint.SEARCH_BUTTON:
            return SimpleSearchControl(action, self.gui_context, parent)
        elif action.render_hint == RenderHint.PUSH_BUTTON:
            return ActionPushButton(action, self.gui_context, parent)
        elif action.render_hint == RenderHint.LABEL:
            return ActionLabel(action, self.gui_context, parent)
        raise Exception('Unhandled render hint {} for {}'.format(action.render_hint, type(action)))