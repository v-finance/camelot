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

class DesktopBackground(QtGui.QWidget):
    """
    A custom background widget for the desktop. This widget is contained
    by the first tab ('Start' tab) of the desktop workspace.
    """
    
    def __init__(self, parent=None):
        super(DesktopBackground, self).__init__(parent)
        
        self.actionButtonsMainLayout = QtGui.QVBoxLayout()
        self.actionButtonsMainLayout.setContentsMargins(200, 50, 200, 50)
        
        self.actionButtonsRow1Layout = QtGui.QHBoxLayout()
        self.actionButtonsRow2Layout = QtGui.QHBoxLayout()

        self.actionButtonsMainLayout.addLayout(self.actionButtonsRow1Layout)
        self.actionButtonsMainLayout.addLayout(self.actionButtonsRow2Layout)
        self.setLayout(self.actionButtonsMainLayout)
        
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
        
        # Make sure that the action buttons aren't visually split
        # up in two rows when there are e.g. only 3 of them.
        # So:
        #  <= 3 action buttons: 1 row and 1, 2 or 3 columns;
        #  >= 4 action buttons: 2 rows and 2, 3, 4 or 5 columns.
        self.actionButtonsLayoutMaxItemsPerRowCount = max((len(actions) + 1) / 2, 3)
        
        for position in xrange(0, min( len(actions), self.actionButtonsLayoutMaxItemsPerRowCount) ):
            actionButton = ActionButton(actions[position], self)
            self.actionButtonsRow1Layout.addWidget(actionButton, 0, Qt.AlignHCenter or Qt.AlignBottom)
        
        for position in xrange(self.actionButtonsLayoutMaxItemsPerRowCount, len(actions)):
            actionButton = ActionButton(actions[position], self)
            self.actionButtonsRow2Layout.addWidget(actionButton, 0, Qt.AlignHCenter or Qt.AlignBottom)
            
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
        
        self.show()
    
class ActionButton(QtGui.QWidget):
    """
    A custom interactive desktop button for the desktop. Each 'button' is 
    actually a vbox containing two labels: the upper one displays an animated
    icon, the lower one a hideable string which represents the actions name.
    """
    def __init__(self, action, parent = None):
        super(ActionButton, self).__init__(parent)
        
        self.action = action
        
        # This property holds if this button reacts to mouse events.
        self.interactive = False
        
        # The animated upper label.   
        animatedLabel = ActionButtonLabel(action, self)
        animatedLabel.setObjectName('animatedLabel')
        
        # The static lower label. 
        staticLabel = QtGui.QLabel(action.get_verbose_name())
        staticLabel.setObjectName('staticLabel')
        staticLabelFont = QtGui.QApplication.font()
        staticLabelFont.setPointSize(14)
        staticLabel.setFont(staticLabelFont)
        staticLabel.adjustSize()
        staticLabelOpacityEffect = QtGui.QGraphicsOpacityEffect(parent=self)
        staticLabelOpacityEffect.setObjectName('staticLabelOpacityEffect')
        staticLabelOpacityEffect.setOpacity(0)
        staticLabel.setGraphicsEffect(staticLabelOpacityEffect)

        mainLayout = QtGui.QVBoxLayout()
        mainLayout.setObjectName('mainLayout')
        mainLayout.setContentsMargins(0, 20, 0, 20)
        mainLayout.addWidget(animatedLabel, 1, Qt.AlignCenter)
        mainLayout.addWidget(staticLabel, 0, Qt.AlignHCenter or Qt.AlignTop)
        

        self.setMouseTracking(True)
        self.setMinimumHeight(min(animatedLabel.height() + staticLabel.height(), 160))
        self.setMaximumHeight(160)
        self.setMinimumWidth(max(animatedLabel.width(), staticLabel.width()))
        self.setLayout(mainLayout)
                
    def resetLayout(self):
        animatedLabel = self.findChild(QtGui.QLabel, 'animatedLabel')
        if animatedLabel is not None:
            animatedLabel.resetLayout()
        
    def setInteractive(self, interactive):
        self.interactive = interactive

    def enterEvent(self, event):
        if self.interactive and event.type() == QtCore.QEvent.Enter:
            staticLabelOpacityEffect = self.findChild(QtCore.QObject, 'staticLabelOpacityEffect')
            if staticLabelOpacityEffect is not None:
                staticLabelOpacityEffect.setOpacity(1)
            if not self.action.is_notification():
                animatedLabel = self.findChild(QtGui.QLabel, 'animatedLabel')
                if animatedLabel is not None:
                    animatedLabel.startHoverAnimation()
        event.ignore()
    
    def leaveEvent(self, event):
        if self.interactive and event.type() == QtCore.QEvent.Leave:
            if not self.action.is_notification():
                animatedLabel = self.findChild(QtCore.QObject, 'animatedLabel')
                if animatedLabel is not None:
                    animatedLabel.stopHoverAnimation()
            staticLabelOpacityEffect = self.findChild(QtCore.QObject, 'staticLabelOpacityEffect')
            if staticLabelOpacityEffect is not None:
                staticLabelOpacityEffect.setOpacity(0)
        event.ignore()

    def mousePressEvent(self, event):
        if self.interactive:
            animatedLabel = self.findChild(QtCore.QObject, 'animatedLabel')
            if animatedLabel is not None:
                animatedLabel.startSelectionAnimation()
        event.ignore()
        
#class ActionButton(QtGui.QWidget):
    #"""
    #A custom interactive desktop button for the desktop. Each 'button' is 
    #actually a vbox containing two labels: the upper one displays an animated
    #icon, the lower one a hideable string which represents the actions name.
    #"""
    #def __init__(self, action, parent = None):
        #super(ActionButton, self).__init__(parent)
        
        #self.action = action
        
        ## This property holds if this button reacts to mouse events.
        #self.interactive = False
        
        ## The animated upper label.   
        #self.animatedLabel = ActionButtonLabel(action, parent)
        
        ## The static lower label. 
        #self.staticLabel = QtGui.QLabel(action.get_verbose_name())
        #self.staticLabelFont = QtGui.QApplication.font()
        #self.staticLabelFont.setPointSize(14)
        #self.staticLabel.setFont(self.staticLabelFont)
        #self.staticLabel.adjustSize()
        #self.staticLabelOpacityEffect = QtGui.QGraphicsOpacityEffect()
        #self.staticLabelOpacityEffect.setOpacity(0)
        #self.staticLabel.setGraphicsEffect(self.staticLabelOpacityEffect)
        
        #mainLayout = QtGui.QVBoxLayout()
        #mainLayout.setContentsMargins(0, 20, 0, 20)
        #mainLayout.addWidget(self.animatedLabel, 1, Qt.AlignCenter)
        #mainLayout.addWidget(self.staticLabel, 0, Qt.AlignHCenter or Qt.AlignTop)
        
        #self.setMouseTracking(True)
        #self.setMinimumHeight(min(self.animatedLabel.height() + self.staticLabel.height(), 160))
        #self.setMaximumHeight(160)
        #self.setMinimumWidth(max(self.animatedLabel.width(), self.staticLabel.width()))
        #self.setLayout(mainLayout)
                
    #def resetLayout(self):
        #self.animatedLabel.resetLayout()
        
    #def setInteractive(self, interactive):
        #self.interactive = interactive

    #def enterEvent(self, event):
        #if self.interactive and event.type() == QtCore.QEvent.Enter:
            #self.staticLabelOpacityEffect.setOpacity(1)
            #if not self.action.is_notification():
                #self.animatedLabel.startHoverAnimation()
            
        #event.ignore()
    
    #def leaveEvent(self, event):
        #if self.interactive and event.type() == QtCore.QEvent.Leave:
            #if not self.action.is_notification():
                #self.animatedLabel.stopHoverAnimation()
            #self.staticLabelOpacityEffect.setOpacity(0)

        #event.ignore()

    #def mousePressEvent(self, event):
        #if self.interactive:
            #self.animatedLabel.startSelectionAnimation()
            
        #event.ignore()
    
class ActionButtonLabel(QtGui.QLabel):
    """
    This class provides an animated QLabel and is used by the ActionButton class.
    Given the intention of the respresented action (notification or a regular
    action), a different animation is applied to this label (respectively a fast
    shaking and a bouncing one).
    """
    def __init__(self, action, parent = None):
        super(ActionButtonLabel, self).__init__(parent)
        self.action = action
        
        # This property is used to store the original position of this label
        # so it can be visually reset when the user leaves before the ongoing
        # animation has finished.
        self.originalPosition = None
        
        self.setPixmap(action.get_icon().getQPixmap())
        self.setMinimumSize(self.pixmap().width(), self.pixmap().height())
        
        self.opacityEffect = QtGui.QGraphicsOpacityEffect()
        self.opacityEffect.setOpacity(1.0)
        self.setGraphicsEffect(self.opacityEffect)
        
        if action.is_notification():
            # Shake animation #
            self.notificationAnimationPart1 = QtCore.QPropertyAnimation(self, 'pos')
            self.notificationAnimationPart1.setDuration(50)
            self.notificationAnimationPart1.setEasingCurve(QtCore.QEasingCurve.Linear)
            
            self.notificationAnimationPart2 = QtCore.QPropertyAnimation(self, 'pos')
            self.notificationAnimationPart2.setDuration(50)
            self.notificationAnimationPart2.setEasingCurve(QtCore.QEasingCurve.Linear)
            
            self.notificationAnimationPart3 = QtCore.QPropertyAnimation(self, 'pos')
            self.notificationAnimationPart3.setDuration(50)
            self.notificationAnimationPart3.setEasingCurve(QtCore.QEasingCurve.Linear)
            
            self.notificationAnimation = QtCore.QSequentialAnimationGroup()
            self.notificationAnimation.setLoopCount(10)
            self.notificationAnimation.addAnimation(self.notificationAnimationPart1)
            self.notificationAnimation.addAnimation(self.notificationAnimationPart2)
            self.notificationAnimation.addAnimation(self.notificationAnimationPart3)

            # Timer is used to simulate a pausing effect of the animation.
            self.notificationAnimationTimer = QtCore.QTimer()
            self.notificationAnimationTimer.setInterval(1500)
            self.notificationAnimationTimer.setSingleShot(True)
            self.notificationAnimationTimer.timeout.connect(self.notificationAnimation.start)
            self.notificationAnimation.finished.connect(self.notificationAnimationTimer.start)
            ###################
        else:
            # Bounce animation #
            self.hoverAnimationPart1 = QtCore.QPropertyAnimation(self, 'pos')
            self.hoverAnimationPart1.setDuration(500)
            self.hoverAnimationPart1.setEasingCurve(QtCore.QEasingCurve.Linear)
            
            self.hoverAnimationPart2 = QtCore.QPropertyAnimation(self, 'pos')
            self.hoverAnimationPart2.setDuration(1500)
            self.hoverAnimationPart2.setEasingCurve(QtCore.QEasingCurve.OutElastic)
            
            self.hoverAnimation = QtCore.QSequentialAnimationGroup()
            self.hoverAnimation.setLoopCount(-1) # Infinite
            self.hoverAnimation.addAnimation(self.hoverAnimationPart1)
            self.hoverAnimation.addAnimation(self.hoverAnimationPart2)
            ####################
        
        # Selection animation when clicking #
        # Part 1 (instant repositioning) #
        self.selectionAnimation1 = QtCore.QPropertyAnimation(self, 'pos')
        self.selectionAnimation1.setDuration(200)
        self.selectionAnimation1.setEasingCurve(QtCore.QEasingCurve.Linear)
        
        # Part 2 (quick resize and opacity effect) #
        self.selectionAnimation2 = QtCore.QPropertyAnimation(self, 'size')
        self.selectionAnimation2.setDuration(200)
        self.selectionAnimation2.setEasingCurve(QtCore.QEasingCurve.OutCubic)
        
        # Part 3 (opacity effect) #
        self.selectionAnimation3 = QtCore.QPropertyAnimation(self.opacityEffect, 'opacity')
        self.selectionAnimation3.setDuration(200)
        self.selectionAnimation3.setEasingCurve(QtCore.QEasingCurve.Linear)
        
        self.selectionAnimationGroup = QtCore.QParallelAnimationGroup()
        self.selectionAnimationGroup.addAnimation(self.selectionAnimation1)
        self.selectionAnimationGroup.addAnimation(self.selectionAnimation2)
        self.selectionAnimationGroup.addAnimation(self.selectionAnimation3)
        #####################################

    def showEvent(self, event):
        self.originalPosition = self.mapFromParent(self.mapToParent(self.pos()))

        if self.action.is_notification():        
            self.notificationAnimationPart1.setStartValue(self.originalPosition)
            self.notificationAnimationPart1.setEndValue(self.originalPosition + QtCore.QPoint(-8, 0))

            self.notificationAnimationPart2.setStartValue(self.originalPosition + QtCore.QPoint(-8, 0))
            self.notificationAnimationPart2.setEndValue(self.originalPosition + QtCore.QPoint(8, 0))
            
            self.notificationAnimationPart3.setStartValue(self.originalPosition + QtCore.QPoint(8, 0))
            self.notificationAnimationPart3.setEndValue(self.originalPosition)
            
            self.notificationAnimation.start()
            
        event.ignore()

    def startHoverAnimation(self):
        self.hoverAnimationPart1.setStartValue(self.originalPosition)
        self.hoverAnimationPart1.setEndValue(self.originalPosition + QtCore.QPoint(0, -20))
    
        self.hoverAnimationPart2.setStartValue(self.originalPosition + QtCore.QPoint(0, -20))
        self.hoverAnimationPart2.setEndValue(self.originalPosition)
        
        self.hoverAnimation.start()

    def stopHoverAnimation(self):
        self.hoverAnimation.stop()
        if self.originalPosition:
            self.move(self.originalPosition)
            
        self.resetLayout()

    def startSelectionAnimation(self):
        if self.action.is_notification():
            self.notificationAnimation.stop()
        else:
            self.hoverAnimation.stop()

        self.move(self.originalPosition)

        self.selectionAnimation1.setStartValue(self.originalPosition)
        self.selectionAnimation1.setEndValue(self.originalPosition + QtCore.QPoint(-20, -20))
        self.selectionAnimation2.setStartValue(self.size())
        self.selectionAnimation2.setEndValue(self.size() + QtCore.QSize(40, 40))
        self.selectionAnimation3.setStartValue(1.0)
        self.selectionAnimation3.setEndValue(0.1)

        # Doing 'self.selectionAnimationGroup.finished.connect(self.performAction)'
        # results somehow in invoking self.performAction multiple times.
        # So as a simple workaround, just focus on the state of the last
        # of all grouped animations.
        self.selectionAnimation3.finished.connect(self.resetLayout)
        self.selectionAnimation3.finished.connect(self.performAction)
        self.setScaledContents(True)
        self.selectionAnimationGroup.start()

    @QtCore.pyqtSlot()
    def performAction(self):
        self.action.run(self.parentWidget())
        
    @QtCore.pyqtSlot()
    def resetLayout(self):
        if self.originalPosition:
            self.move(self.originalPosition)
        self.setScaledContents(False)
        self.resize(self.pixmap().width(), self.pixmap().height())
        self.opacityEffect.setOpacity(1.0)

class DesktopTabbar(QtGui.QTabBar):
    
    change_view_mode_signal = QtCore.pyqtSignal()
    
    def mouseDoubleClickEvent(self, event):
        self.change_view_mode_signal.emit()
        event.accept()

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
        self._tab_widget.addTab(self._background_widget, _('Start'))
        
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

    def set_view(self, view, title = '...'):
        """
        Remove the currently active view and replace it with a new view.
        """
        index = self._tab_widget.currentIndex()
        
        if index == 0: # 'Start' tab
            self.add_view(view, title)
        else:
            self._tab_widget.removeTab(index)
            
            view.title_changed_signal.connect(self.change_title)            
            index = self._tab_widget.insertTab(index, view, title)
            self._tab_widget.setCurrentIndex(index)

    @gui_function
    def add_view(self, view, title = '...'):
        """
        Add a Widget implementing AbstractView to the workspace.
        """
        view.title_changed_signal.connect(self.change_title)
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

