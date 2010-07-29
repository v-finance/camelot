#  ============================================================================
#
#  Copyright (C) 2007-2010 Conceptive Engineering bvba. All rights reserved.
#  www.conceptive.be / project-camelot@conceptive.be
#
#  This file is part of the Camelot Library.
#
#  This file may be used under the terms of the GNU General Public
#  License version 2.0 as published by the Free Software Foundation
#  and appearing in the file LICENSE.GPL included in the packaging of
#  this file.  Please review the following information to ensure GNU
#  General Public Licensing requirements will be met:
#  http://www.trolltech.com/products/qt/opensource.html
#
#  If you are unsure which license is appropriate for your use, please
#  review the following information:
#  http://www.trolltech.com/products/qt/licensing.html or contact
#  project-camelot@conceptive.be.
#
#  This file is provided AS IS with NO WARRANTY OF ANY KIND, INCLUDING THE
#  WARRANTY OF DESIGN, MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE.
#
#  For use of this library in commercial applications, please contact
#  project-camelot@conceptive.be
#
#  ============================================================================

"""This module provides a singleton workspace that can be used by views
and widget to create new windows or raise existing ones"""

from PyQt4 import QtGui
from PyQt4 import QtCore

import logging
logger = logging.getLogger('camelot.view.workspace')

from camelot.view.model_thread import gui_function


class DesktopWorkspace(QtGui.QMdiArea):

    @gui_function
    def __init__(self, *args):
        QtGui.QMdiArea.__init__(self, *args)
        self.setOption(QtGui.QMdiArea.DontMaximizeSubWindowOnActivation)
        self.setBackground(QtGui.QBrush(QtGui.QColor('white')))
        self.setActivationOrder(QtGui.QMdiArea.ActivationHistoryOrder)

    @gui_function
    def addSubWindow(self, widget, *args):
        from camelot.view.controls.view import AbstractView
        subwindow = QtGui.QMdiArea.addSubWindow(self, widget, *args)
        if hasattr(widget, 'closeAfterValidation'):
            subwindow.connect(widget, widget.closeAfterValidation, subwindow, QtCore.SLOT("close()"))

        def create_set_window_title(subwindow):

            def set_window_title(new_title):
                subwindow.setWindowTitle(new_title)

            return set_window_title

        self.connect(widget, AbstractView.title_changed_signal, create_set_window_title(subwindow))
        logger.debug('in workspace addSubWindow')
        return subwindow

class NoDesktopWorkspace(QtCore.QObject):
    def __init__(self):
        QtCore.QObject.__init__(self)
        self._windowlist = []

    @gui_function
    def addSubWindow(self, widget, *args):
        self.widget = widget
        self.widget.setParent(None)
        self.widget.show()
        self._windowlist.append(self.widget)
        self.connect(widget, QtCore.SIGNAL('WidgetClosed()'), self.removeWidgetFromWorkspace)

    @gui_function
    def subWindowList(self):
        return self._windowlist

    @gui_function
    def removeWidgetFromWorkspace(self):
        self._windowlist.remove(self.widget)

_workspace_ = []

@gui_function
def construct_workspace(*args, **kwargs):
    _workspace_.append(DesktopWorkspace())
    return _workspace_[0]

@gui_function
def construct_no_desktop_workspace(*args, **kwargs):
    _workspace_.append(NoDesktopWorkspace())
    return _workspace_[0]

@gui_function
def get_workspace():
    return _workspace_[0]

@gui_function
def has_workspace():
    return len(_workspace_) > 0
