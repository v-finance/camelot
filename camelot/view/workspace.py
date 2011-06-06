#  ============================================================================
#
#  Copyright (C) 2007-2011 Conceptive Engineering bvba. All rights reserved.
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

from camelot.core.utils import ugettext as _
from camelot.view.model_thread import gui_function, post

from camelot.view.art import Icon

class DesktopBackground(QtGui.QWidget):
    """
    A custom background widget for the desktop. This widget is contained
    by the first tab ('Start' tab) of the desktop workspace.
    """
    
    def __init__(self, parent = None):
        super(DesktopBackground, self).__init__(parent)
        
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
        for actionButton in self.findChildren(ActionButton):
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
                actionButton = ActionButton(actions[position], self)
                actionButton.entered.connect(self.onActionButtonEntered)
                actionButton.left.connect(self.onActionButtonLeft)
                actionButtonsLayout.addWidget(ActionButtonContainer(actionButton), 0, position, Qt.AlignCenter)

            for position in xrange(actionButtonsLayoutMaxItemsPerRowCount, len(actions)):
                actionButton = ActionButton(actions[position], self)                
                actionButton.entered.connect(self.onActionButtonEntered)
                actionButton.left.connect(self.onActionButtonLeft)
                actionButtonsLayout.addWidget(ActionButtonContainer(actionButton), 1, position % actionButtonsLayoutMaxItemsPerRowCount, Qt.AlignCenter)
            
    @QtCore.pyqtSlot()
    def onActionButtonEntered(self):
        actionButton = self.sender()
        actionButtonInfoWidget = self.findChild(QtGui.QWidget, 'actionButtonInfoWidget')
        if actionButtonInfoWidget is not None:
            actionButtonInfoWidget.setInfoFromAction(actionButton.getAction())
       
    @QtCore.pyqtSlot()
    def onActionButtonLeft(self):
        actionButtonInfoWidget = self.findChild(QtGui.QWidget, 'actionButtonInfoWidget')
        if actionButtonInfoWidget is not None:
            actionButtonInfoWidget.resetInfo()
        
    # This custom event handler makes sure that the action buttons aren't
    # drawn in the wrong position on this widget after the screen has been
    # e.g. maximized or resized by using the window handles.
    
    def resizeEvent(self, event):
        for actionButton in self.findChildren(ActionButton):
            actionButton.resetLayout()

        event.ignore()

    # This slot is called after the navpane's animation has finished. During 
    # this sliding animation, all action buttons are linearly moved to the right,
    # giving the user a small window in which he or she may cause visual problems
    # by already hovering the action buttons. This switch assures that the user 
    # cannot perform mouse interaction with the action buttons until they're
    # static.
    @QtCore.pyqtSlot()
    def makeInteractive(self):
        for actionButton in self.findChildren(ActionButton):
            actionButton.setInteractive(True)
            
class ActionButtonContainer(QtGui.QWidget):
    def __init__(self, actionButton, parent = None):
        super(ActionButtonContainer, self).__init__(parent)
        
        mainLayout = QtGui.QHBoxLayout()
        # Set some margins to avoid the ActionButton being visually clipped
        # when performing the hoverAnimation.
        mainLayout.setContentsMargins(20, 20, 20, 20)
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

    @QtCore.pyqtSlot()
    def setInfoFromAction(self, action):
        actionNameLabel = self.findChild(QtGui.QLabel, 'actionNameLabel')
        if actionNameLabel is not None:
            actionNameLabel.setText(action.get_verbose_name())
        
        actionDescriptionLabel = self.findChild(QtGui.QLabel, 'actionDescriptionLabel')
        if actionDescriptionLabel is not None:
            actionDescriptionLabel.setText(action.get_description())
            if action.get_description():
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
    
class ActionButton(QtGui.QLabel):
    entered = QtCore.pyqtSignal()
    left = QtCore.pyqtSignal()    
    
    """
    A custom interactive desktop button for the desktop. Each 'button' is 
    actually an animated label.
    """
    def __init__(self, action, parent = None):
        super(ActionButton, self).__init__(parent)
        
        self.setObjectName('ActionButton')
        self.setMouseTracking(True)

        self.action = action
        
        # This property holds if this button reacts to mouse events.
        self.interactive = False
        
        # This property is used to store the original position of this label
        # so it can be visually reset when the user leaves before the ongoing
        # animation has finished.
        self.originalPosition = None

        # This property holds the state of the selection animation. Since this
        # animation is only created inside startSelectionAnimation() (to avoid
        # the increasing amount of performAction() invocations), this variable is 
        # used to continuously store the state of that animation.
        self.selectionAnimationState = QtCore.QAbstractAnimation.Stopped

        self.setPixmap(action.get_icon().getQPixmap())
        self.resize(self.pixmap().width(), self.pixmap().height())
        self.setMaximumHeight(160)
        
        opacityEffect = QtGui.QGraphicsOpacityEffect(parent = self)
        opacityEffect.setOpacity(1.0)
        self.setGraphicsEffect(opacityEffect)

        if action.is_notification():
            # Shake animation #
            notificationAnimationPart1 = QtCore.QPropertyAnimation(self, 'pos')
            notificationAnimationPart1.setObjectName('notificationAnimationPart1')
            notificationAnimationPart1.setDuration(50)
            notificationAnimationPart1.setEasingCurve(QtCore.QEasingCurve.Linear)
            
            notificationAnimationPart2 = QtCore.QPropertyAnimation(self, 'pos')
            notificationAnimationPart2.setObjectName('notificationAnimationPart2')
            notificationAnimationPart2.setDuration(50)
            notificationAnimationPart2.setEasingCurve(QtCore.QEasingCurve.Linear)
            
            notificationAnimationPart3 = QtCore.QPropertyAnimation(self, 'pos')
            notificationAnimationPart3.setObjectName('notificationAnimationPart3')
            notificationAnimationPart3.setDuration(50)
            notificationAnimationPart3.setEasingCurve(QtCore.QEasingCurve.Linear)
            
            notificationAnimation = QtCore.QSequentialAnimationGroup(parent = self)
            notificationAnimation.setObjectName('notificationAnimation')
            notificationAnimation.setLoopCount(10)
            notificationAnimation.addAnimation(notificationAnimationPart1)
            notificationAnimation.addAnimation(notificationAnimationPart2)
            notificationAnimation.addAnimation(notificationAnimationPart3)

            # Timer is used to simulate a pausing effect of the animation.
            notificationAnimationTimer = QtCore.QTimer(parent = self)
            notificationAnimationTimer.setObjectName('notificationAnimationTimer')
            notificationAnimationTimer.setInterval(1500)
            notificationAnimationTimer.setSingleShot(True)
            notificationAnimationTimer.timeout.connect(notificationAnimation.start)
            notificationAnimation.finished.connect(notificationAnimationTimer.start)
            ###################

    
        # Bounce animation #
        hoverAnimationPart1 = QtCore.QPropertyAnimation(self, 'pos')
        hoverAnimationPart1.setObjectName('hoverAnimationPart1')
        hoverAnimationPart1.setDuration(500)
        hoverAnimationPart1.setEasingCurve(QtCore.QEasingCurve.Linear)
        
        hoverAnimationPart2 = QtCore.QPropertyAnimation(self, 'pos')
        hoverAnimationPart2.setObjectName('hoverAnimationPart2')
        hoverAnimationPart2.setDuration(1500)
        hoverAnimationPart2.setEasingCurve(QtCore.QEasingCurve.OutElastic)
        
        hoverAnimation = QtCore.QSequentialAnimationGroup(parent = self)
        hoverAnimation.setObjectName('hoverAnimation')
        hoverAnimation.setLoopCount(-1) # Infinite
        hoverAnimation.addAnimation(hoverAnimationPart1)
        hoverAnimation.addAnimation(hoverAnimationPart2)
        ####################
        
        # Selection animation #
        selectionAnimationPart1 = QtCore.QPropertyAnimation(self, 'pos')
        selectionAnimationPart1.setObjectName('selectionAnimationPart1')
        selectionAnimationPart1.setDuration(200)
        selectionAnimationPart1.setEasingCurve(QtCore.QEasingCurve.Linear)
        
        selectionAnimationPart2 = QtCore.QPropertyAnimation(self, 'size')
        selectionAnimationPart2.setObjectName('selectionAnimationPart2')
        selectionAnimationPart2.setDuration(200)
        selectionAnimationPart2.setEasingCurve(QtCore.QEasingCurve.OutCubic)
        
        selectionAnimationPart3 = QtCore.QPropertyAnimation(self.graphicsEffect(), 'opacity')
        selectionAnimationPart3.setObjectName('selectionAnimationPart3')
        selectionAnimationPart3.setDuration(200)
        selectionAnimationPart3.setEasingCurve(QtCore.QEasingCurve.Linear)
        
        selectionAnimation = QtCore.QParallelAnimationGroup(parent = self)
        selectionAnimation.setObjectName('selectionAnimation')
        selectionAnimation.addAnimation(selectionAnimationPart1)
        selectionAnimation.addAnimation(selectionAnimationPart2)
        selectionAnimation.addAnimation(selectionAnimationPart3)
        # Not working when clicking the white area underneath the ActionButton image.
        #selectionAnimation.finished.connect(self.resetLayout)
        #selectionAnimation.finished.connect(self.performAction)
        selectionAnimation.stateChanged.connect(self.updateSelectionAnimationState)
        #######################

    def startHoverAnimation(self):
        hoverAnimationPart1 = self.findChild(QtCore.QPropertyAnimation, 'hoverAnimationPart1')
        if hoverAnimationPart1 is not None:
            hoverAnimationPart1.setStartValue(self.originalPosition)
            hoverAnimationPart1.setEndValue(self.originalPosition + QtCore.QPoint(0, -20))
    
        hoverAnimationPart2 = self.findChild(QtCore.QPropertyAnimation, 'hoverAnimationPart2')
        if hoverAnimationPart2 is not None:
            hoverAnimationPart2.setStartValue(self.originalPosition + QtCore.QPoint(0, -20))
            hoverAnimationPart2.setEndValue(self.originalPosition)
        
        hoverAnimation = self.findChild(QtCore.QSequentialAnimationGroup, 'hoverAnimation')
        if hoverAnimation is not None:
            hoverAnimation.start()

    def stopHoverAnimation(self):
        hoverAnimation = self.findChild(QtCore.QSequentialAnimationGroup, 'hoverAnimation')
        if hoverAnimation is not None:
            hoverAnimation.stop()
        if self.originalPosition is not None:
            self.move(self.originalPosition)
            
        self.resetLayout()

    def startSelectionAnimation(self):
        if self.action.is_notification():
            notificationAnimation = self.findChild(QtCore.QSequentialAnimationGroup, 'notificationAnimation')            
            if notificationAnimation is not None:
                notificationAnimation.stop()
        else:
            hoverAnimation = self.findChild(QtCore.QSequentialAnimationGroup, 'hoverAnimation')
            if hoverAnimation is not None:
                hoverAnimation.stop()

        self.move(self.originalPosition)
        
        # Selection animation when clicked #
        selectionAnimationPart1 = self.findChild(QtCore.QPropertyAnimation, 'selectionAnimationPart1')
        selectionAnimationPart2 = self.findChild(QtCore.QPropertyAnimation, 'selectionAnimationPart2')
        selectionAnimationPart3 = self.findChild(QtCore.QPropertyAnimation, 'selectionAnimationPart3')
        selectionAnimation = self.findChild(QtCore.QParallelAnimationGroup, 'selectionAnimation')
        if None not in (selectionAnimationPart1, selectionAnimationPart2, 
                        selectionAnimationPart3, selectionAnimation):
            selectionAnimationPart1.setStartValue(self.originalPosition)
            selectionAnimationPart1.setEndValue(self.originalPosition + QtCore.QPoint(-20, -20))

            selectionAnimationPart2.setStartValue(self.size())
            selectionAnimationPart2.setEndValue(self.size() + QtCore.QSize(40, 40))

            selectionAnimationPart3.setStartValue(1.0)
            selectionAnimationPart3.setEndValue(0.1)
        
            self.setScaledContents(True)
            
            selectionAnimation.start()

    def updateSelectionAnimationState(self, newState, oldState):
        self.selectionAnimationState = newState
        
        # Simulate finished signal (see comment in animation buildup code).
        if oldState == QtCore.QAbstractAnimation.Running and newState == QtCore.QAbstractAnimation.Stopped:
            self.performAction()
            self.resetLayout()

    def performAction(self):
        self.action.run(self.parentWidget())

    def getAction(self):
        return self.action

    def resetLayout(self):
        if self.action.is_notification():
            self.stopNotificationAnimation()
        
        if self.sender() and self.originalPosition:
            self.move(self.originalPosition)

        self.setScaledContents(False)
        self.resize(self.pixmap().width(), self.pixmap().height())
        self.graphicsEffect().setOpacity(1.0)
        
        if self.action.is_notification() and self.originalPosition:
            self.startNotificationAnimation()
        
    def setInteractive(self, interactive):
        self.interactive = interactive
        
        self.originalPosition = self.mapToParent(QtCore.QPoint(0, 0))

        if self.action.is_notification():
            self.startNotificationAnimation()

    def enterEvent(self, event):
        if self.interactive:
            if self.action.is_notification():
                self.stopNotificationAnimation()
                
            self.startHoverAnimation()
            
            self.entered.emit()

        event.ignore()
    
    def leaveEvent(self, event):
        if self.interactive:
            self.stopHoverAnimation()
            
            if self.action.is_notification():
                self.startNotificationAnimation()
            
            self.left.emit()

        event.ignore()

    def onContainerMousePressEvent(self, event):
        # Second part blocks fast consecutive clicks.
        if self.interactive and self.selectionAnimationState == QtCore.QAbstractAnimation.Stopped:
            self.startSelectionAnimation()

        event.ignore()
        
    def startNotificationAnimation(self):
        notificationAnimationPart1 = self.findChild(QtCore.QPropertyAnimation, 'notificationAnimationPart1')
        if notificationAnimationPart1 is not None:
            notificationAnimationPart1.setStartValue(self.originalPosition)
            notificationAnimationPart1.setEndValue(self.originalPosition + QtCore.QPoint(-8, 0))

        notificationAnimationPart2 = self.findChild(QtCore.QPropertyAnimation, 'notificationAnimationPart2')
        if notificationAnimationPart2 is not None:
            notificationAnimationPart2.setStartValue(self.originalPosition + QtCore.QPoint(-8, 0))
            notificationAnimationPart2.setEndValue(self.originalPosition + QtCore.QPoint(8, 0))
        
        notificationAnimationPart3 = self.findChild(QtCore.QPropertyAnimation, 'notificationAnimationPart3')
        if notificationAnimationPart3 is not None:
            notificationAnimationPart3.setStartValue(self.originalPosition + QtCore.QPoint(8, 0))
            notificationAnimationPart3.setEndValue(self.originalPosition)
        
        notificationAnimation = self.findChild(QtCore.QSequentialAnimationGroup, 'notificationAnimation')
        notificationAnimationTimer = self.findChild(QtCore.QTimer, 'notificationAnimationTimer')
        if notificationAnimation is not None and notificationAnimationTimer is not None:
            notificationAnimationTimer.start()
            notificationAnimation.start()

    def stopNotificationAnimation(self):
        notificationAnimation = self.findChild(QtCore.QSequentialAnimationGroup, 'notificationAnimation')
        notificationAnimationTimer = self.findChild(QtCore.QTimer, 'notificationAnimationTimer')
        
        if notificationAnimation is not None and notificationAnimationTimer is not None:
            notificationAnimationTimer.stop()
            notificationAnimation.stop()

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

    @gui_function
    def __init__(self, app_admin, parent):
        super(DesktopWorkspace, self).__init__(parent)
        
        self._app_admin = app_admin
        
        layout = QtGui.QHBoxLayout()
        layout.setMargin(0)
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
        self._background_widget = DesktopBackground(self)
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
            self._tab_widget.removeTab(index)
            
            view.title_changed_signal.connect(self.change_title)
            view.icon_changed_signal.connect(self.change_icon)
            if icon:
                index = self._tab_widget.insertTab(index, view, icon, title)
            else:
                index = self._tab_widget.insertTab(index, view, title)
            self._tab_widget.setCurrentIndex(index)

    @gui_function
    def add_view(self, view, icon = None, title = '...'):
        """
        Add a Widget implementing AbstractView to the workspace.
        """
        view.title_changed_signal.connect(self.change_title)
        view.icon_changed_signal.connect(self.change_icon)
        if icon:
            index = self._tab_widget.addTab(view, icon, title)
        else:
            index = self._tab_widget.addTab(view, title)
        self._tab_widget.setCurrentIndex(index)

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


