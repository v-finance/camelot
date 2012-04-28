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

"""Convenience functions and classes to present views to the user"""

from PyQt4 import QtGui
from PyQt4 import QtCore
from PyQt4.QtCore import Qt

import logging
logger = logging.getLogger('camelot.view.workspace')

from camelot.admin.action import ApplicationActionGuiContext
from camelot.core.utils import ugettext as _
from camelot.view.model_thread import object_thread, post
from camelot.view.controls.action_widget import ( ActionLabel, 
                                                  HOVER_ANIMATION_DISTANCE,
                                                  NOTIFICATION_ANIMATION_DISTANCE )

from camelot.view.art import Icon

class DesktopBackground(QtGui.QWidget):
    """
    A custom background widget for the desktop. This widget is contained
    by the first tab ('Start' tab) of the desktop workspace.
    """
    
    def __init__( self, gui_context, parent ):
        super(DesktopBackground, self).__init__( parent )
        self.gui_context = gui_context
        mainLayout = QtGui.QVBoxLayout()
        
        actionButtonsLayout = QtGui.QGridLayout()
        actionButtonsLayout.setObjectName('actionButtonsLayout')
        actionButtonsLayout.setContentsMargins(200, 20, 200, 20)
        
        actionButtonInfoWidget = ActionButtonInfoWidget()
        actionButtonInfoWidget.setObjectName('actionButtonInfoWidget')
                
        mainLayout.addWidget(actionButtonInfoWidget, 0, Qt.AlignCenter)
        mainLayout.addLayout(actionButtonsLayout)
        
        self.setLayout(mainLayout)
        
        # Set a white background color
        palette = self.palette()
        self.setAutoFillBackground(True)
        palette.setBrush(QtGui.QPalette.Window, Qt.white)
        self.setPalette(palette)
        
    # This method is invoked when the desktop workspace decides or gets told
    # that the actions should be updated due to the presence of to be added 
    # actions. 
    @QtCore.pyqtSlot(object)
    def set_actions(self, actions):
        """
        :param actions: a list of EntityActions
        """
        #
        # Remove old actions
        #
        for actionButton in self.findChildren(ActionLabel):
            actionButton.deleteLater()
        
        # Make sure that the action buttons aren't visually split
        # up in two rows when there are e.g. only 3 of them.
        # So:
        #  <= 3 action buttons: 1 row and 1, 2 or 3 columns;
        #  >= 4 action buttons: 2 rows and 2, 3, 4 or 5 columns.
        actionButtonsLayoutMaxItemsPerRowCount = max((len(actions) + 1) / 2, 3)
        
        actionButtonsLayout = self.findChild(QtGui.QGridLayout, 'actionButtonsLayout')
        if actionButtonsLayout is not None:
            for position in xrange(0, min( len(actions), actionButtonsLayoutMaxItemsPerRowCount) ):
                action = actions[position]
                actionButton = action.render( self.gui_context, self )
                actionButton.entered.connect(self.onActionButtonEntered)
                actionButton.left.connect(self.onActionButtonLeft)
                actionButton.setInteractive(True)
                actionButtonsLayout.addWidget(ActionButtonContainer(actionButton), 0, position, Qt.AlignCenter)

            for position in xrange(actionButtonsLayoutMaxItemsPerRowCount, len(actions)):
                action = actions[position]
                actionButton = action.render( self.gui_context, self )
                actionButton.entered.connect(self.onActionButtonEntered)
                actionButton.left.connect(self.onActionButtonLeft)
                actionButton.setInteractive(True)
                actionButtonsLayout.addWidget(ActionButtonContainer(actionButton), 1, position % actionButtonsLayoutMaxItemsPerRowCount, Qt.AlignCenter)
            
    @QtCore.pyqtSlot()
    def onActionButtonEntered(self):
        actionButton = self.sender()
        actionButtonInfoWidget = self.findChild(QtGui.QWidget, 'actionButtonInfoWidget')
        if actionButtonInfoWidget is not None:
            # @todo : get state should be called with a model context as first
            #         argument
            post( actionButton.action.get_state,
                  actionButtonInfoWidget.setInfoFromState,
                  args = (None,) )
       
    @QtCore.pyqtSlot()
    def onActionButtonLeft(self):
        actionButtonInfoWidget = self.findChild(QtGui.QWidget, 'actionButtonInfoWidget')
        if actionButtonInfoWidget is not None:
            actionButtonInfoWidget.resetInfo()
        
    # This custom event handler makes sure that the action buttons aren't
    # drawn in the wrong position on this widget after the screen has been
    # e.g. maximized or resized by using the window handles.
    
    def resizeEvent(self, event):
        for actionButton in self.findChildren(ActionLabel):
            actionButton.resetLayout()

        event.ignore()

    # This slot is called after the navpane's animation has finished. During 
    # this sliding animation, all action buttons are linearly moved to the right,
    # giving the user a small window in which he or she may cause visual problems
    # by already hovering the action buttons. This switch assures that the user 
    # cannot perform mouse interaction with the action buttons until they're
    # static.
    @QtCore.pyqtSlot()
    def makeInteractive(self, interactive=True):
        for actionButton in self.findChildren(ActionLabel):
            actionButton.setInteractive(interactive)
            
    def refresh(self):
        pass
            
class ActionButtonContainer(QtGui.QWidget):
    def __init__(self, actionButton, parent = None):
        super(ActionButtonContainer, self).__init__(parent)
        
        mainLayout = QtGui.QHBoxLayout()
        # Set some margins to avoid the ActionButton being visually clipped
        # when performing the hoverAnimation.
        mainLayout.setContentsMargins(2*NOTIFICATION_ANIMATION_DISTANCE,
                                      2*HOVER_ANIMATION_DISTANCE,
                                      2*NOTIFICATION_ANIMATION_DISTANCE,
                                      2*HOVER_ANIMATION_DISTANCE)
        mainLayout.addWidget(actionButton)
        self.setLayout(mainLayout)
        
    def mousePressEvent(self, event):
        # Send this event to the ActionButton that is contained by this widget.
        self.layout().itemAt(0).widget().onContainerMousePressEvent(event)
            
class ActionButtonInfoWidget(QtGui.QWidget):
    def __init__(self, parent = None):
        super(ActionButtonInfoWidget, self).__init__(parent)
        
        mainLayout = QtGui.QHBoxLayout()
        
        font = self.font()
        font.setPointSize(14)
        
        actionNameLabel = QtGui.QLabel()
        actionNameLabel.setFont(font)
        actionNameLabel.setFixedSize(250, 50)
        actionNameLabel.setAlignment(Qt.AlignCenter)
        actionNameLabel.setObjectName('actionNameLabel')
        
        actionDescriptionLabel = QtGui.QLabel()
        actionDescriptionLabel.setFixedSize(250, 200)
        actionDescriptionLabel.setObjectName('actionDescriptionLabel')

        mainLayout.addWidget(actionNameLabel, 0, Qt.AlignVCenter)
        mainLayout.addWidget(actionDescriptionLabel)

        self.setLayout(mainLayout)

    @QtCore.pyqtSlot( object )
    def setInfoFromState(self, state):
        actionNameLabel = self.findChild(QtGui.QLabel, 'actionNameLabel')
        if actionNameLabel is not None:
            actionNameLabel.setText( unicode( state.verbose_name ) )
        
        actionDescriptionLabel = self.findChild(QtGui.QLabel, 'actionDescriptionLabel')
        if actionDescriptionLabel is not None:
            tooltip = unicode( state.tooltip or '' )
            actionDescriptionLabel.setText(tooltip)
            if tooltip:
                # Do not use show() or hide() in this case, since it will
                # cause the actionButtons to be drawn on the wrong position.
                # Instead, just set the width of the widget to either 0 or 250.
                actionDescriptionLabel.setFixedWidth(250)
            else:
                actionDescriptionLabel.setFixedWidth(0)
            
    def resetInfo(self):
        actionNameLabel = self.findChild(QtGui.QLabel, 'actionNameLabel')
        if actionNameLabel is not None:
            actionNameLabel.setText('')
        
        actionDescriptionLabel = self.findChild(QtGui.QLabel, 'actionDescriptionLabel')
        if actionDescriptionLabel is not None:
            actionDescriptionLabel.setText('')
    
class DesktopTabbar(QtGui.QTabBar):

    change_view_mode_signal = QtCore.pyqtSignal()
    
    def mouseDoubleClickEvent(self, event):
        self.change_view_mode_signal.emit()
        event.accept()
        
    def tabSizeHint(self, index):
        originalSizeHint = super(DesktopTabbar, self).tabSizeHint(index)
        minimumWidth = max(160, originalSizeHint.width())
        
        return QtCore.QSize(minimumWidth, originalSizeHint.height())

class DesktopWorkspace(QtGui.QWidget):
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

    view_activated_signal = QtCore.pyqtSignal(QtGui.QWidget)
    change_view_mode_signal = QtCore.pyqtSignal()
    last_view_closed_signal = QtCore.pyqtSignal()

    def __init__(self, app_admin, parent):
        super(DesktopWorkspace, self).__init__(parent)
        self.gui_context = ApplicationActionGuiContext()
        self.gui_context.admin = app_admin
        self.gui_context.workspace = self
        self._app_admin = app_admin
        
        layout = QtGui.QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Setup the tab widget
        self._tab_widget = QtGui.QTabWidget( self )
        tab_bar = DesktopTabbar(self._tab_widget)
        tab_bar.setToolTip(_('Double click to (un)maximize'))
        tab_bar.change_view_mode_signal.connect(self._change_view_mode)
        self._tab_widget.setTabBar(tab_bar)
        self._tab_widget.setDocumentMode(True)
        self._tab_widget.setTabsClosable(True)
        self._tab_widget.tabCloseRequested.connect(self._tab_close_request)
        self._tab_widget.currentChanged.connect(self._tab_changed)
        layout.addWidget(self._tab_widget)
        
        # Setup the background widget
        self._background_widget = DesktopBackground( self.gui_context, self )
        self._app_admin.actions_changed_signal.connect(self.reload_background_widget)
        self._tab_widget.addTab(self._background_widget,
                                Icon('tango/16x16/actions/go-home.png').getQIcon(),
                                _('Home'))
        if tab_bar.tabButton(0, QtGui.QTabBar.RightSide):
            tab_bar.tabButton(0, QtGui.QTabBar.RightSide).hide()
        elif tab_bar.tabButton(0, QtGui.QTabBar.LeftSide):
            # mac for example has the close button on the left side by default
            tab_bar.tabButton(0, QtGui.QTabBar.LeftSide).hide()
        
        self.setLayout(layout)
        self.reload_background_widget()
             
    @QtCore.pyqtSlot()
    def reload_background_widget(self):
        post(self._app_admin.get_actions, self._background_widget.set_actions)

    @QtCore.pyqtSlot()
    def _change_view_mode(self):
        self.change_view_mode_signal.emit()
        
    @QtCore.pyqtSlot(int)
    def _tab_close_request(self, index):
        """
        Handle the request for the removal of a tab at index.
        
        Note that only at-runtime added tabs are being closed, implying
        the immortality of the 'Start' tab.
        """
        if index > 0:
            view = self._tab_widget.widget(index)
            if view:
                # it's not enough to simply remove the tab, because this
                # would keep the underlying view widget alive
                view.deleteLater()
                self._tab_widget.removeTab(index)

    @QtCore.pyqtSlot(int)
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
        
        if i == 0: # 'Start' tab
            return None
        
        return self._tab_widget.widget(i)

    @QtCore.pyqtSlot(QtCore.QString)
    def change_title(self, new_title):
        """
        Slot to be called when the tile of a view needs to change.
        
        Note: the title of the 'Start' tab cannot be overwritten.
        """
        # the request of the sender does not work in older pyqt versions
        # therefore, take the current index, notice this is not correct !!
        #
        # sender = self.sender()
        sender = self.active_view()
        
        if sender:
            index = self._tab_widget.indexOf(sender)
            if index > 0:
                self._tab_widget.setTabText(index, new_title)
                
    @QtCore.pyqtSlot(QtGui.QIcon)
    def change_icon(self, new_icon):
        """
        Slot to be called when the icon of a view needs to change.
        
        Note: the icon of the 'Start' tab cannot be overwritten.
        """
        # the request of the sender does not work in older pyqt versions
        # therefore, take the current index, notice this is not correct !!
        #
        # sender = self.sender()
        sender = self.active_view()
        
        if sender:
            index = self._tab_widget.indexOf(sender)
            if index > 0:
                self._tab_widget.setTabIcon(index, new_icon)

    def set_view(self, view, icon = None, title = '...'):
        """
        Remove the currently active view and replace it with a new view.
        """
        index = self._tab_widget.currentIndex()
        
        if index == 0: # 'Start' tab is currently visible.
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
        assert object_thread( self )
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

def show_top_level(view, parent):
    """Show a widget as a top level window
    :param view: the widget extend AbstractView
    :param parent: the widget with regard to which the top level
    window will be placed.
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
    # set the parent to None to avoid the window being destructed
    # once the parent gets destructed
    #
    view.setParent( None )
    view.setWindowFlags(QtCore.Qt.Window)
    #
    # Make the window title blank to prevent the something
    # like main.py or pythonw being displayed
    #
    view.setWindowTitle( u'' )
    view.title_changed_signal.connect( view.setWindowTitle )
    view.icon_changed_signal.connect( view.setWindowIcon )
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

