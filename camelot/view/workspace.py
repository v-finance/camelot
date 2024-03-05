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



import logging
logger = logging.getLogger('camelot.view.workspace')

from ..core import constants
from ..core.qt import QtCore, QtWidgets, transferto
from ..core.backend import is_cpp_gui_context_name, get_window
from . import gui_naming_context


top_level_windows = []

def apply_form_state(view, parent, state):
    # make sure all window events are processed before starting to move,
    # and resize the window, in a possibly futile attempt to have consistent
    # application of the form state.
    QtCore.QCoreApplication.instance().processEvents()
    #
    # position the new window in the center of the same screen
    # as the parent.
    # That parent might be a QWidget or a QWindow
    decoration_width, decoration_height = 0, 0
    if parent is not None:
        screen = parent.screen()
        # here we use the incorrect assumption that we can use the size of
        # the decorations of the parent window to know the size of the
        # decorations of the new window
        #
        # http://doc.qt.io/qt-4.8/application-windows.html#window-geometry
        parent_geometry = parent.geometry()
        parent_frame = parent.frameGeometry()
        decoration_width = parent_frame.width() - parent_geometry.width()
        decoration_height = parent_frame.height() - parent_geometry.height()
    else:
        screen = QtCore.QCoreApplication.instance().primaryScreen()

    geometry = screen.availableGeometry()
    if state == constants.MAXIMIZED:
        view.setWindowState(QtCore.Qt.WindowState.WindowMaximized)
    elif state == constants.MINIMIZED:
        view.setWindowState(QtCore.Qt.WindowState.WindowMinimized)
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

def show_top_level(view, gui_context_name, state=None):
    """Show a widget as a top level window.  If a parent window is given, the new
    window will have the same modality as the parent.

    :param view: the widget extend AbstractView
    :param parent: the widget with regard to which the top level
        window will be placed.
    :param state: the state of the form, 'maximized', or 'left' or 'right', ...
     """
    if is_cpp_gui_context_name(gui_context_name):
        parent = get_window()
    else:
        gui_context = gui_naming_context.resolve(gui_context_name)
        parent = gui_context.get_window()
    #
    # assert the view has an objectname, so it can be retrieved later
    # by this object name, since a top level view might have no references
    # from other objects.
    #
    assert len(view.objectName())
    #
    # assert the parent is None to avoid the window being destructed
    # once the parent gets destructed, do not set the parent itself here,
    # nor the window flags, as this might cause windows to hide themselves
    # again after being shown in Qt5
    #
    assert view.parent() is None
    #
    # Register the view with reference to itself.  This will keep
    # the Python object alive as long as the Qt object is not
    # destroyed.  Hence Python will not trigger the deletion of the
    # view as long as the window is not closed
    #
    transferto(view, view)
    #
    # Make the window title blank to prevent the something
    # like main.py or pythonw being displayed
    #
    view.setWindowTitle(' ')
    view.title_changed_signal.connect( view.setWindowTitle )
    view.icon_changed_signal.connect( view.setWindowIcon )
    view.setAttribute(QtCore.Qt.WidgetAttribute.WA_DeleteOnClose)
    # parent might be a QWidget or a QWindow
    # the modality should be set before showing the window
    if isinstance(parent, QtWidgets.QWidget):
        view.setWindowModality(parent.windowModality())
    #
    # There is a bug in certain versions of Qt5 (QTBUG-57882), that causes
    # view.show() to unmax/min the window. This is supposed to be fixed in Qt6
    # No longer show the window before moving/resizing it to its final position
    #
    apply_form_state(view, parent, state)
    view.show()


