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
    """A custom background widget for the desktop"""
    
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

    @QtCore.pyqtSlot(object)
    def set_actions(self, actions):
        """
        :param actions: a list of ApplicationActions
        """
        self.actionButtonsLayoutMaxItemsPerRowCount = min(len(actions) + 1 / 2, 3)
        
        for position in xrange(0, self.actionButtonsLayoutMaxItemsPerRowCount):
            actionButton = ActionButton(actions[position], self)
            self.actionButtonsRow1Layout.addWidget(actionButton, 0, Qt.AlignHCenter or Qt.AlignBottom)
        
        for position in xrange(self.actionButtonsLayoutMaxItemsPerRowCount, len(actions)):
            actionButton = ActionButton(actions[position], self)
            self.actionButtonsRow2Layout.addWidget(actionButton, 0, Qt.AlignHCenter or Qt.AlignBottom)
            
    def resizeEvent(self, event):
        for actionButton in self.findChildren(ActionButton):
            actionButton.resetLayout()
            
        event.ignore()

    @QtCore.pyqtSlot()
    def makeInteractive(self):
        for actionButton in self.findChildren(ActionButton):
            actionButton.setInteractive(True)
        
class ActionButton(QtGui.QWidget):
    """
    A custom desktop button for the desktop.
    """
    def __init__(self, action, parent = None):
        super(ActionButton, self).__init__(parent)
        
        self.action = action        
        
        self.animatedLabel = ActionButtonLabel(action, parent)
        self.animatedLabel.enterSignal.connect(self.onEnterSignal)
        self.animatedLabel.leaveSignal.connect(self.onLeaveSignal)
        self.staticLabel = QtGui.QLabel('<font color="gray">' + action.get_verbose_name() + '<\font>')
        self.staticLabelFont = QtGui.QApplication.font()
        self.staticLabelFont.setPointSize(14)
        self.staticLabel.setFont(self.staticLabelFont)
        
        mainLayout = QtGui.QVBoxLayout()
        mainLayout.setContentsMargins(0, 20, 0, 20)
        mainLayout.addWidget(self.animatedLabel, 0, Qt.AlignCenter)
        mainLayout.addWidget(self.staticLabel, 0, Qt.AlignHCenter or Qt.AlignTop)
        
        self.setFixedSize(QtCore.QSize(120, 160))
        self.setLayout(mainLayout)
        
    def resetLayout(self):
        self.animatedLabel.resetLayout()
        
    def setInteractive(self, interactive):
        self.animatedLabel.setInteractive(interactive)
        
    @QtCore.pyqtSlot()
    def onEnterSignal(self):
        self.staticLabel.setText('<font color="black">' + self.action.get_verbose_name() + '<\font>')

    @QtCore.pyqtSlot()    
    def onLeaveSignal(self):
        self.staticLabel.setText('<font color="gray">' + self.action.get_verbose_name() + '<\font>')
    
class ActionButtonLabel(QtGui.QLabel):
    enterSignal = QtCore.pyqtSignal()
    leaveSignal = QtCore.pyqtSignal()
    
    def __init__(self, action, parent = None):
        super(ActionButtonLabel, self).__init__(parent)
        self.action = action
        
        # This property holds if this button reacts to mouse events
        self.interactive = False
        
        # This property is used to store the position of this button
        # so it can be visually reset when the user leaves in the
        # middle of an animation
        self.originalPosition = None
        
        self.setPixmap(action.get_icon().getQPixmap())
        self.setMinimumSize(70, 70)
        #self.setMaximumSize(110, 110)
        self.setToolTip(action.get_verbose_name())
        self.setMouseTracking(True)
        #self.setScaledContents(True)
        
        self.opacityEffect = QtGui.QGraphicsOpacityEffect()
        self.opacityEffect.setOpacity(1.0)
        self.setGraphicsEffect(self.opacityEffect)
        
        # Bounce animation when hovering #
        self.bounceAnimation1 = QtCore.QPropertyAnimation(self, 'pos')
        self.bounceAnimation1.setDuration(500)
        self.bounceAnimation1.setEasingCurve(QtCore.QEasingCurve.Linear)
        
        self.bounceAnimation2 = QtCore.QPropertyAnimation(self, 'pos')
        self.bounceAnimation2.setDuration(1500)
        self.bounceAnimation2.setEasingCurve(QtCore.QEasingCurve.OutElastic)
        
        self.bounceAnimationGroup = QtCore.QSequentialAnimationGroup()
        self.bounceAnimationGroup.setLoopCount(-1)
        self.bounceAnimationGroup.addAnimation(self.bounceAnimation1)
        self.bounceAnimationGroup.addAnimation(self.bounceAnimation2)
        ##################################
        
        # Selection animation when clicking #
        # Part 1 (instant repositioning) #
        self.selectionAnimation1 = QtCore.QPropertyAnimation(self, 'pos')
        self.selectionAnimation1.setDuration(50)
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

    def enterEvent(self, event):
        if self.interactive:
            if event.type() == QtCore.QEvent.Enter:
                # Store the originalPosition of this label to be able to reset the position in leaveEvent.
                if not self.originalPosition:
                    self.originalPosition = self.mapFromParent(self.mapToParent(self.pos()))
                
                self.bounceAnimation1.setStartValue(self.originalPosition)
                self.bounceAnimation1.setEndValue(self.originalPosition + QtCore.QPoint(0, -20))
                
                self.bounceAnimation2.setStartValue(self.originalPosition + QtCore.QPoint(0, -20))
                self.bounceAnimation2.setEndValue(self.originalPosition)
                
                self.bounceAnimationGroup.start()
                
                self.enterSignal.emit()

        event.ignore()
    
    def leaveEvent(self, event):
        if self.interactive:
            if event.type() == QtCore.QEvent.Leave:
                self.bounceAnimationGroup.stop()
                if self.originalPosition:
                    self.move(self.originalPosition)
                    
            self.leaveSignal.emit()
                    
            self.resetLayout()

        event.ignore()

    def mousePressEvent(self, event):
        if self.interactive:
            self.action.run(self.parentWidget())
        
            self.bounceAnimationGroup.stop()
            if self.originalPosition:
                self.move(self.originalPosition)
            else:
                self.originalPosition = self.mapFromParent(self.mapToParent(self.pos()))
    
            self.selectionAnimation1.setStartValue(self.originalPosition)
            self.selectionAnimation1.setEndValue(self.originalPosition + QtCore.QPoint(-20, -20))        
            self.selectionAnimation2.setStartValue(self.size())
            self.selectionAnimation2.setEndValue(self.size() + QtCore.QSize(40, 40))
            self.selectionAnimation3.setStartValue(1.0)
            self.selectionAnimation3.setEndValue(0.1)
            
            self.selectionAnimationGroup.start()
            self.selectionAnimationGroup.finished.connect(self.resetLayout)
            
        event.ignore()
        
    @QtCore.pyqtSlot()
    def resetLayout(self):
        if self.originalPosition:
            self.move(self.originalPosition)

        self.originalPosition = None
        self.resize(70, 70)
        self.opacityEffect.setOpacity(1.0)
        
    def setInteractive(self, interactive):
        self.interactive = interactive

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
    def __init__(self, application_admin, parent):
        super(DesktopWorkspace, self).__init__(parent)
        
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
        self._tab_widget.addTab(self._background_widget, _('Start'))
        self._background_widget.show()
        
        self.setLayout(layout)
        post(application_admin.get_actions, 
             self._background_widget.set_actions)

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
        
        if index == 0:
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

