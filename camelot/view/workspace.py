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

"""Convenience functions and classes to present views to the user"""

from PyQt4 import QtGui
from PyQt4 import QtCore

import logging
LOGGER = logging.getLogger('camelot.view.workspace')

from camelot.view.model_thread import gui_function
from camelot.view.controls.view import AbstractView

class DesktopWorkspace(QtGui.QTabWidget):
    """A tab based workspace that can be used by views
    to display themselves. In essence this is A wrapper around the QTabWidget to
    do some initial setup.  This was implemented first using the QMdiArea, but
    the QMdiArea has too many drawbacks, like not being able to add close buttons
    to the tabs in a decent way"""

    view_activated_signal = QtCore.SIGNAL('view_activated')
    
    @gui_function
    def __init__(self, parent):
        super(DesktopWorkspace, self).__init__(parent)
        self.setDocumentMode( True )
        self.setMovable( True )
        self.setTabsClosable( True )
        self.connect( self, 
                      QtCore.SIGNAL('tabCloseRequested(int)'), 
                      self._tab_close_request)
        self.connect( self, 
                      QtCore.SIGNAL('currentChanged(int)'), 
                      self._tab_changed)


    def _tab_close_request(self, index):
        """request the removal of the tab at index"""
        self.removeTab( index )

    def _tab_changed(self, index):
        """the active tab has changed, emit the view_activated signal"""
        self.emit( self.view_activated_signal, self.active_view() )
        
    def active_view(self):
        """:return: the currently active view or None"""
        i = self.currentIndex()
        if i < 0:
            return None
        return self.widget( i ) 

    def change_title(self, new_title):
        """slot to be called when the tile of a view needs to
        change"""
        sender = self.sender()
        if sender:
            index = self.indexOf( sender )
            if index >= 0:
                self.setTabText( index, new_title )
        
    def set_view(self, view, title='...'):
        """Remove the currently active view and replace it with a new
        view"""
        index = self.currentIndex()
        if index < 0:
            self.add_view( view, title )
        else:
            self.connect(
                view,
                AbstractView.title_changed_signal,
                self.change_title,
            ) 
            self.removeTab( index )
            self.insertTab( index, view, title )
            
    @gui_function
    def add_view(self, view, title='...'):
        """add a Widget implementing AbstractView to the workspace"""
        self.connect(
            view,
            AbstractView.title_changed_signal,
            self.change_title,
        )        
        index = self.addTab( view, title )
        self.setCurrentIndex( index )

def show_top_level(view, parent):
    """Show a widget as a top level window
    :param view: the widget extend AbstractView
    :param parent: the widget with regard to which the top level
    window will be placed.
     """
    from camelot.view.controls.view import AbstractView
    view.setParent( parent )
    view.setWindowFlags(QtCore.Qt.Window)
    view.connect(
        view,
        AbstractView.title_changed_signal,
        view.setWindowTitle
    )
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