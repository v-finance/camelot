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

'''
Created on May 22, 2010

@author: tw55413
'''

from PyQt4 import QtGui
from PyQt4 import QtCore

from camelot.admin.action.form_action import FormActionGuiContext
from camelot.view.model_thread import post

class AbstractActionWidget( object ):

    def __init__( self, action, gui_context ):
        """Helper class to construct widget that when triggered run an action.
        This class exists as a base class for custom ActionButton implementations.
        """
        from camelot.admin.action import State
        self.action = action
        self.gui_context = gui_context
        self.state = State()
        if isinstance( gui_context, FormActionGuiContext ):
            gui_context.widget_mapper.model().dataChanged.connect( self.data_changed )
            gui_context.widget_mapper.currentIndexChanged.connect( self.current_row_changed )
        post( action.get_state, self.set_state, args = (self.gui_context.create_model_context(),) )

    def set_state( self, state ):
        self.state = state
        self.setEnabled( state.enabled )
        self.setVisible( state.visible )
        
    def current_row_changed( self, current_row ):
        post( self.action.get_state, 
              self.set_state, 
              args = (self.gui_context.create_model_context(),) )
        
    def data_changed( self, index1, index2 ):
        self.current_row_changed( index1.row() )
        
    def run_action( self, mode=None ):
        gui_context = self.gui_context.copy()
        gui_context.mode = mode
        self.action.gui_run( gui_context )

HOVER_ANIMATION_DISTANCE = 20
NOTIFICATION_ANIMATION_DISTANCE = 8

class ActionLabel( QtGui.QLabel, AbstractActionWidget ):
    
    entered = QtCore.pyqtSignal()
    left = QtCore.pyqtSignal()    
    
    """
    A custom interactive desktop button for the desktop. Each 'button' is 
    actually an animated label.
    """
    def __init__( self, action, gui_context, parent ):
        QtGui.QLabel.__init__( self, parent )
        AbstractActionWidget.__init__( self, action, gui_context )
        
        self.setObjectName('ActionButton')
        self.setMouseTracking(True)
        
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
        self.setMaximumHeight(160)
        
        opacityEffect = QtGui.QGraphicsOpacityEffect(parent = self)
        opacityEffect.setOpacity(1.0)
        self.setGraphicsEffect(opacityEffect)
    
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

    def set_state( self, state ):
        AbstractActionWidget.set_state( self, state )
        if state.icon:
            self.setPixmap( state.icon.getQPixmap() )
            self.resize( self.pixmap().width(), self.pixmap().height() )
        if state.notification:
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
            notificationAnimation.finished.connect( notificationAnimationTimer.start )
        self.resetLayout()
        
    def startHoverAnimation(self):
        hoverAnimationPart1 = self.findChild(QtCore.QPropertyAnimation, 'hoverAnimationPart1')
        if hoverAnimationPart1 is not None:
            hoverAnimationPart1.setStartValue(self.originalPosition)
            hoverAnimationPart1.setEndValue(self.originalPosition + QtCore.QPoint(0, -HOVER_ANIMATION_DISTANCE))
    
        hoverAnimationPart2 = self.findChild(QtCore.QPropertyAnimation, 'hoverAnimationPart2')
        if hoverAnimationPart2 is not None:
            hoverAnimationPart2.setStartValue(self.originalPosition + QtCore.QPoint(0, -HOVER_ANIMATION_DISTANCE))
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
        if self.state.notification:
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
            selectionAnimationPart1.setEndValue(self.originalPosition + QtCore.QPoint(-HOVER_ANIMATION_DISTANCE, -HOVER_ANIMATION_DISTANCE))

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
            self.run_action()
            self.resetLayout()

    def resetLayout(self):
        if self.state.notification:
            self.stopNotificationAnimation()
        
        if self.sender() and self.originalPosition:
            self.move(self.originalPosition)

        self.setScaledContents(False)
        if self.pixmap():
            self.resize(self.pixmap().width(), self.pixmap().height())
        self.graphicsEffect().setOpacity(1.0)
        
        if self.state.notification and self.originalPosition:
            self.startNotificationAnimation()
        
    def setInteractive(self, interactive):
        self.interactive = interactive
        
        self.originalPosition = self.mapToParent(QtCore.QPoint(0, 0))# + QtCore.QPoint(NOTIFICATION_ANIMATION_DISTANCE, HOVER_ANIMATION_DISTANCE)
        
        if self.state.notification:
            self.startNotificationAnimation()

    def enterEvent(self, event):
        if self.interactive:
            if self.state.notification:
                self.stopNotificationAnimation()
                
            self.startHoverAnimation()
            
            self.entered.emit()

        event.ignore()
    
    def leaveEvent(self, event):
        if self.interactive:
            self.stopHoverAnimation()
            
            if self.state.notification:
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
            notificationAnimationPart1.setEndValue(self.originalPosition + QtCore.QPoint(-NOTIFICATION_ANIMATION_DISTANCE, 0))

        notificationAnimationPart2 = self.findChild(QtCore.QPropertyAnimation, 'notificationAnimationPart2')
        if notificationAnimationPart2 is not None:
            notificationAnimationPart2.setStartValue(self.originalPosition + QtCore.QPoint(-NOTIFICATION_ANIMATION_DISTANCE, 0))
            notificationAnimationPart2.setEndValue(self.originalPosition + QtCore.QPoint(NOTIFICATION_ANIMATION_DISTANCE, 0))
        
        notificationAnimationPart3 = self.findChild(QtCore.QPropertyAnimation, 'notificationAnimationPart3')
        if notificationAnimationPart3 is not None:
            notificationAnimationPart3.setStartValue(self.originalPosition + QtCore.QPoint(NOTIFICATION_ANIMATION_DISTANCE, 0))
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
        
class ActionAction( QtGui.QAction ):
    
    def __init__( self, action, gui_context, parent ):
        super( ActionAction, self ).__init__( parent )
        self.action = action
        if action.shortcut != None:
            self.setShortcut( action.shortcut )
        post( action.get_state, 
              self.set_state, 
              args = (gui_context.create_model_context(),) )

    @QtCore.pyqtSlot( object )
    def set_state( self, state ):
        if state.verbose_name != None:
            self.setText( unicode( state.verbose_name ) )
        else:
            self.setText( '' )
        if state.icon != None:
            self.setIcon( state.icon.getQIcon() )
        else:
            self.setIcon( QtGui.QIcon() )
        if state.tooltip != None:
            self.setToolTip( unicode( state.tooltip ) )
        else:
            self.setToolTip( '' )
        self.setEnabled( state.enabled )
        self.setVisible( state.visible )
        
class ActionPushButton( QtGui.QPushButton, AbstractActionWidget ):
    
    def __init__( self, action, gui_context, parent ):
        """A :class:`QtGui.QPushButton` that when pressed, will run an 
        action.
        
        .. image:: /_static/actionwidgets/action_push_botton_application_enabled.png
        
        """
        QtGui.QPushButton.__init__( self, parent )
        AbstractActionWidget.__init__( self, action, gui_context )
        self.clicked.connect( self.triggered )

    @QtCore.pyqtSlot()
    def triggered(self):
        self.run_action( None )
        
    @QtCore.pyqtSlot( QtCore.QModelIndex, QtCore.QModelIndex )
    def data_changed( self, index1, index2 ):
        AbstractActionWidget.data_changed( self, index1, index2 )
        
    def set_state( self, state ):
        super( ActionPushButton, self ).set_state( state )
        if state.verbose_name != None:
            self.setText( unicode( state.verbose_name ) )
        if state.icon != None:
            self.setIcon( state.icon.getQIcon() )
        else:
            self.setIcon( QtGui.QIcon() )
        if state.modes:
            menu = QtGui.QMenu( self )
            for mode in state.modes:
                menu.addAction( mode.render( menu ) )
            self.setMenu( menu )

