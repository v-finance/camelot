#  ============================================================================
#
#  Copyright (C) 2007-2010 Conceptive Engineering bvba. All rights reserved.
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

"""Convenience functions and classes to present views to the user"""

from PyQt4 import QtGui
from PyQt4 import QtCore
from PyQt4.QtCore import Qt

#from camelot.view.art import Pixmap

import logging
logger = logging.getLogger('camelot.view.workspace')

from camelot.core.utils import ugettext as _
from camelot.view.model_thread import gui_function, post

class DesktopBackground(QtGui.QGraphicsView):
    """A custom background widget for the desktop"""
    
    def __init__(self, parent=None):
        super(DesktopBackground, self).__init__(parent)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

#        self.scene = QtGui.QGraphicsScene()
#        self.pixitem = self.scene.addPixmap(
#            Pixmap('camelot-home.png').getQPixmap()
#        )
#        self.setAlignment(Qt.AlignBottom | Qt.AlignLeft)
#        self.setScene(self.scene)

    @QtCore.pyqtSlot(list)
    def set_actions(self, actions):
        """
        :param actions: a list of ApplicationActions
        """
        print actions

class DesktopTabbar(QtGui.QTabBar):
    
    change_view_mode_signal = QtCore.pyqtSignal()
    
    def mouseDoubleClickEvent(self, event):
        self.change_view_mode_signal.emit()
        event.accept()

class DesktopWorkspace(QtGui.QWidget):
    """A tab based workspace that can be used by views
to display themselves. In essence this is A wrapper around the QTabWidget to
do some initial setup and provide it with a background widget.  This was
implemented first using the QMdiArea, but the QMdiArea has too many
drawbacks, like not being able to add close buttons to the tabs in
a decent way.

.. attribute:: background

The widget class to be used as a background for when there are
no open tabs on the desktop.
"""

    background = DesktopBackground
    view_activated_signal = QtCore.pyqtSignal(QtGui.QWidget)
    change_view_mode_signal = QtCore.pyqtSignal()
    last_view_closed_signal = QtCore.pyqtSignal()

    @gui_function
    def __init__(self, application_admin, parent):
        super(DesktopWorkspace, self).__init__(parent)
        layout = QtGui.QHBoxLayout()
        layout.setMargin( 0 )
        layout.setSpacing( 0 )
        # setup the tab widget
        self._tab_widget = QtGui.QTabWidget( self )
        tab_bar = DesktopTabbar(self._tab_widget)
        tab_bar.setToolTip( _('Double click to (un)maximize') )
        tab_bar.change_view_mode_signal.connect( self._change_view_mode )
        self._tab_widget.setTabBar( tab_bar )
        self._tab_widget.setDocumentMode(True)
        self._tab_widget.setMovable( True )
        self._tab_widget.setTabsClosable( True )
        self._tab_widget.hide()
        self._tab_widget.tabCloseRequested.connect( self._tab_close_request )
        self._tab_widget.currentChanged.connect( self._tab_changed )
        layout.addWidget( self._tab_widget )
        # setup the background widget
        self._background_widget = self.background( self )
        self._background_widget.show()
        layout.addWidget( self._background_widget )
        self.setLayout( layout )
        post( application_admin.get_actions, self._background_widget.set_actions )

    @QtCore.pyqtSlot()
    def _change_view_mode(self):
        self.change_view_mode_signal.emit()
        
    @QtCore.pyqtSlot(int)
    def _tab_close_request(self, index):
        """request the removal of the tab at index"""
        self._tab_widget.removeTab( index )
        if self._tab_widget.currentIndex() < 0:
            self._tab_widget.hide()
            self._background_widget.show()
            self.last_view_closed_signal.emit()

    @QtCore.pyqtSlot(int)
    def _tab_changed(self, _index):
        """the active tab has changed, emit the view_activated signal"""
        self.view_activated_signal.emit( self.active_view() )

    def active_view(self):
        """:return: the currently active view or None"""
        i = self._tab_widget.currentIndex()
        if i < 0:
            return None
        return self._tab_widget.widget( i )

    @QtCore.pyqtSlot( QtCore.QString )
    def change_title(self, new_title):
        """slot to be called when the tile of a view needs to
        change"""
        # the request of the sender does not work in older pyqt versions
        # therefore, take the current index, notice this is not correct !!
        #
        # sender = self.sender()
        sender = self.active_view()
        if sender:
            index = self._tab_widget.indexOf( sender )
            if index >= 0:
                self._tab_widget.setTabText( index, new_title )

    def set_view(self, view, title='...'):
        """Remove the currently active view and replace it with a new
        view"""
        index = self._tab_widget.currentIndex()
        if index < 0:
            self.add_view( view, title )
        else:
            view.title_changed_signal.connect( self.change_title )
            self._tab_widget.removeTab( index )
            index = self._tab_widget.insertTab( index, view, title )
            self._tab_widget.setCurrentIndex( index )

    @gui_function
    def add_view(self, view, title='...'):
        """add a Widget implementing AbstractView to the workspace"""
        view.title_changed_signal.connect( self.change_title )
        index = self._tab_widget.addTab( view, title )
        self._tab_widget.setCurrentIndex( index )
        self._tab_widget.show()
        self._background_widget.hide()

    def close_all_views(self):
        """Remove all views from the workspace"""
        # NOTE: will call removeTab until tab widget is cleared
        # but removeTab does not really delete the page objects
        #self._tab_widget.clear()
        n = self._tab_widget.count()
        while n:
            self._tab_widget.tabCloseRequested.emit(n)
            n -= 1

def show_top_level(view, parent):
    """Show a widget as a top level window
    :param view: the widget extend AbstractView
    :param parent: the widget with regard to which the top level
    window will be placed.
     """
    view.setParent( parent )
    view.setWindowFlags(QtCore.Qt.Window)
    #
    # Make the window title blank to prevent the something
    # like main.py or pythonw being displayed
    #
    view.setWindowTitle( u'' )
    view.title_changed_signal.connect( view.setWindowTitle )
    view.setAttribute(QtCore.Qt.WA_DeleteOnClose)

    #
    # position the new window in the center of the same screen
    # as the parent
    #
    screen = QtGui.QApplication.desktop().screenNumber(parent)
    available = QtGui.QApplication.desktop().availableGeometry(screen)

    point = QtCore.QPoint(available.x() + available.width()/2,
                          available.y() + available.height()/2)
    point = QtCore.QPoint(point.x()-view.width()/2,
                          point.y()-view.height()/2)
    view.move( point )

    #view.setWindowModality(QtCore.Qt.WindowModal)
    view.show()

