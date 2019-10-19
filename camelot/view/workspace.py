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

"""Convenience functions and classes to present views to the user"""

import six

import logging
logger = logging.getLogger('camelot.view.workspace')

from ..core import constants
from ..core.qt import QtCore, QtGui, QtWidgets
from camelot.admin.action import ApplicationActionGuiContext
from camelot.view.model_thread import object_thread


class DesktopTabbar(QtWidgets.QTabBar):

    def tabSizeHint(self, index):
        originalSizeHint = super(DesktopTabbar, self).tabSizeHint(index)
        minimumWidth = max(160, originalSizeHint.width())
        return QtCore.QSize(minimumWidth, originalSizeHint.height())

class DesktopWorkspace(QtWidgets.QWidget):
    """
    A tab based workspace that can be used by views to display themselves.

    In essence this is a wrapper around QTabWidget to do some initial setup
    and provide it with a background widget.
    This was originallly implemented using the QMdiArea, but the QMdiArea has
    too many drawbacks, like not being able to add close buttons to the tabs
    in a decent way.

    .. attribute:: background

    The widget class to be used as the view for the uncloseable 'Start' tab.
    """

    view_activated_signal = QtCore.qt_signal(QtWidgets.QWidget)

    def __init__(self, app_admin, parent):
        super(DesktopWorkspace, self).__init__(parent)
        self.gui_context = ApplicationActionGuiContext()
        self.gui_context.admin = app_admin
        self.gui_context.workspace = self

        layout = QtWidgets.QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Setup the tab widget
        self._tab_widget = QtWidgets.QTabWidget( self )
        tab_bar = DesktopTabbar(self._tab_widget)
        self._tab_widget.setTabBar(tab_bar)
        self._tab_widget.setDocumentMode(True)
        self._tab_widget.setTabsClosable(True)
        self._tab_widget.tabCloseRequested.connect(self._tab_close_request)
        self._tab_widget.currentChanged.connect(self._tab_changed)
        layout.addWidget(self._tab_widget)
        self.setLayout(layout)

    @QtCore.qt_slot(int)
    def _tab_close_request(self, index):
        """
        Handle the request for the removal of a tab at index.

        Note that only at-runtime added tabs are being closed, implying
        the immortality of the 'Start' tab.
        """
        view = self._tab_widget.widget(index)
        if view is not None:
            # it's not enough to simply remove the tab, because this
            # would keep the underlying view widget alive
            view.deleteLater()
            self._tab_widget.removeTab(index)

    @QtCore.qt_slot(int)
    def _tab_changed(self, _index):
        """
        The active tab has changed, emit the view_activated signal.
        """
        self.view_activated_signal.emit(self.active_view())

    def active_view(self):
        """
        :return: The currently active view or None in case of the 'Start' tab.
        """
        i = self._tab_widget.currentIndex()
        return self._tab_widget.widget(i)

    @QtCore.qt_slot(six.text_type)
    def change_title(self, new_title):
        """
        Slot to be called when the tile of a view needs to change.
        """
        sender = self.sender()
        if sender is not None:
            index = self._tab_widget.indexOf(sender)
            self._tab_widget.setTabText(index, new_title)

    @QtCore.qt_slot(QtGui.QIcon)
    def change_icon(self, new_icon):
        """
        Slot to be called when the icon of a view needs to change.
        """
        sender = self.sender()
        if sender is not None:
            index = self._tab_widget.indexOf(sender)
            self._tab_widget.setTabIcon(index, new_icon)

    def set_view(self, view, icon = None, title = '...'):
        """
        Remove the currently active view and replace it with a new view.
        """
        index = self._tab_widget.currentIndex()
        current_view = self._tab_widget.widget(index)
        if (current_view is None) or (current_view.close() == False):
            self.add_view(view, icon, title)
        else:
            self._tab_close_request(index)
            view.title_changed_signal.connect(self.change_title)
            view.icon_changed_signal.connect(self.change_icon)
            if icon:
                index = self._tab_widget.insertTab(index, view, icon, title)
            else:
                index = self._tab_widget.insertTab(index, view, title)
            self._tab_widget.setCurrentIndex(index)

    def add_view(self, view, icon = None, title = '...'):
        """
        Add a Widget implementing AbstractView to the workspace.
        """
        assert object_thread(self)
        view.title_changed_signal.connect(self.change_title)
        view.icon_changed_signal.connect(self.change_icon)
        if icon:
            index = self._tab_widget.addTab(view, icon, title)
        else:
            index = self._tab_widget.addTab(view, title)
        self._tab_widget.setCurrentIndex(index)

    def refresh(self):
        """Refresh all views on the desktop"""
        for i in range( self._tab_widget.count() ):
            self._tab_widget.widget(i).refresh()

    def close_all_views(self):
        """
        Remove all views, except the 'Start' tab, from the workspace.
        """
        # NOTE: will call removeTab until tab widget is cleared
        # but removeTab does not really delete the page objects
        #self._tab_widget.clear()
        max_index = self._tab_widget.count()

        while max_index > 0:
            self._tab_widget.tabCloseRequested.emit(max_index)
            max_index -= 1

top_level_windows = []

def apply_form_state(view, parent, state):
    #
    # position the new window in the center of the same screen
    # as the parent.
    # That parent might be a QWidget or a QWindow
    if isinstance(parent, QtWidgets.QWidget):
        screen = QtWidgets.QApplication.desktop().screenNumber(parent)
    else:
        screen = 0
    geometry = QtWidgets.QApplication.desktop().availableGeometry(screen)
    decoration_width, decoration_height = 0, 0
    if parent is not None:
        # here we use the incorrect assumption that we can use the size of
        # the decorations of the parent window to know the size of the
        # decorations of the new window
        #
        # http://doc.qt.io/qt-4.8/application-windows.html#window-geometry
        parent_geometry = parent.geometry()
        parent_frame = parent.frameGeometry()
        decoration_width = parent_frame.width() - parent_geometry.width()
        decoration_height = parent_frame.height() - parent_geometry.height()
    if state == constants.MAXIMIZED:
        view.setWindowState(QtCore.Qt.WindowMaximized)
    elif state == constants.MINIMIZED:
        view.setWindowState(QtCore.Qt.WindowMinimized)
    elif state == constants.RIGHT:
        geometry.setLeft(geometry.center().x())
        view.resize(geometry.width()-decoration_width, geometry.height()-decoration_height)
        view.move(geometry.topLeft())
    elif state == constants.LEFT:
        geometry.setRight(geometry.center().x())
        view.resize(geometry.width()-decoration_width, geometry.height()-decoration_height)
        view.move(geometry.topLeft())
    else:
        point = QtCore.QPoint(geometry.x() + geometry.width()/2,
                              geometry.y() + geometry.height()/2)
        point = QtCore.QPoint(point.x()-view.width()/2,
                              point.y()-view.height()/2)
        view.move(point)

def show_top_level(view, parent, state=None):
    """Show a widget as a top level window.  If a parent window is given, the new
    window will have the same modality as the parent.

    :param view: the widget extend AbstractView
    :param parent: the widget with regard to which the top level
        window will be placed.
    :param state: the state of the form, 'maximized', or 'left' or 'right', ...
     """
    from camelot.view.register import register
    #
    # Register the view with reference to itself.  This will keep
    # the Python object alive as long as the Qt object is not
    # destroyed.  Hence Python will not trigger the deletion of the
    # view as long as the window is not closed
    #
    register( view, view )
    #
    # asset the parent is None to avoid the window being destructed
    # once the parent gets destructed, do not set the parent itself here,
    # nor the window flags, as this might cause windows to hide themselves
    # again after being shown in Qt5
    #
    assert view.parent() is None
    #
    # Make the window title blank to prevent the something
    # like main.py or pythonw being displayed
    #
    view.setWindowTitle( u' ' )
    view.title_changed_signal.connect( view.setWindowTitle )
    view.icon_changed_signal.connect( view.setWindowIcon )
    view.setAttribute(QtCore.Qt.WA_DeleteOnClose)
    # parent might be a QWidget or a QWindow
    # the modality should be set before showing the window
    if isinstance(parent, QtWidgets.QWidget):
        view.setWindowModality(parent.windowModality())
    #
    # There is a bug in certain versions of Qt5 (QTBUG-57882), that causes
    # view.show() to unmax/min the window.
    # Therefor show the window before moving/resizing it to its final position
    #
    view.show()
    apply_form_state(view, parent, state)

