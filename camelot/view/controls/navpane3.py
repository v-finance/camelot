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

"""left navigation pane"""

import logging
logger = logging.getLogger('camelot.view.controls.navpane3')

from PyQt4 import QtGui, QtCore

from PyQt4.QtCore import Qt

from PyQt4.QtGui import QMenu, QFrame, QLabel, QWidget, \
    QDockWidget, QVBoxLayout, QHBoxLayout, QSizePolicy

from camelot.view.action import ActionFactory
from camelot.view.model_thread import post
from camelot.view.controls.modeltree import ModelItem, ModelTree
from camelot.view.controls.user_translatable_label import UserTranslatableLabel

class PaneButton(QWidget):
    """Custom made navigation pane button"""

    width = 160
    height = 32

    pressed = QtCore.pyqtSignal(int)

    def __init__(self, text, icon_pixmap, parent=None):
        super(PaneButton, self).__init__(parent)

        button = QtGui.QPushButton(QtGui.QIcon(icon_pixmap), unicode(text), self)
        button.pressed.connect( self._button_pressed )
        #button.setFlat(True)
        layout = QHBoxLayout()
        layout.setSpacing(0)
        layout.setContentsMargins(0,0,0,0)

        #self.icon = QLabel(self)
        #self.icon.setSizePolicy(QSizePolicy(
        #    QSizePolicy.Fixed, QSizePolicy.Preferred))
        #self.icon.setPixmap(icon_pixmap)
        #self.icon.setObjectName('PaneButtonIcon')
        #layout.addWidget(self.icon)

        #self.label = UserTranslatableLabel(text, self)
        #self.label.setAlignment(Qt.AlignLeft|Qt.AlignVCenter)
        #self.label.setObjectName('PaneButtonLabel')
        layout.addWidget( button )

        self.setLayout(layout)

        self.setFixedHeight(self.height)
        self.setMinimumWidth(self.width)
        self.resize(self.width, self.height)

        self.setObjectName('PaneButton')

    def toggle_bold(self):
        pass
        #font = self.label.font()
        #font.setBold(not font.bold())
        #self.label.setFont(font)

    def layout_index(self):
        return self.parent().layout().indexOf(self)

    @QtCore.pyqtSlot()
    def _button_pressed(self):
        self.pressed.emit(self.layout_index())

class NavigationPane(QDockWidget):
    """NavigationPane made of PaneButtons and ModelTrees"""

    def __init__(self, app_admin, workspace, parent):
        super(QDockWidget, self).__init__(parent)

        self.workspace = workspace
        self.app_admin = app_admin
        self._sections = None
        self._animation = QtCore.QParallelAnimationGroup()
        self._animation.finished.connect( self.animation_finished )
        
        self._title_widget = QWidget()

        self._dock_widget = self.get_dock_widget()
        self._dock_widget.setMouseTracking(True)

        self._current_tree_widget = None

        # hack for removing the dock title bar
        self.setTitleBarWidget(self._title_widget)
        self.setWidget(self._dock_widget)

        self.setFeatures(QDockWidget.NoDockWidgetFeatures)

        self.app_admin.sections_changed_signal.connect(self.update_sections)
        self.update_sections()

    @QtCore.pyqtSlot()
    def update_sections(self):
        post(self.app_admin.get_sections, self.set_sections)
        
    @QtCore.pyqtSlot()
    def animation_finished(self):
        """Once the animation is finished, hide all non active
        section trees"""
        layout = self._dock_widget.layout()
        for i in range( layout.count() ):
            if i%2 == 1:
                section_tree = layout.itemAt( i ).widget()
                if section_tree != self._current_tree_widget:
                    section_tree.hide()
        
    def get_dock_widget(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(0,0,0,0)
        layout.setSpacing(0)

        dw = QWidget()
        dw.setLayout(layout)
        return dw

    def get_tree_widget(self):
        tw = ModelTree(parent=self)
        tw.setObjectName('PaneTree')

        # i hate the sunken frame style
        tw.setFrameShape(QFrame.NoFrame)
        tw.setFrameShadow(QFrame.Plain)

        tw.contextmenu = QMenu(self)
        act = ActionFactory.new_tab(self, self.open_in_new_view)
        tw.contextmenu.addAction(act)
        tw.setContextMenuPolicy(Qt.CustomContextMenu)
        tw.customContextMenuRequested.connect(self.create_context_menu)

        return tw

    def get_sections(self):
        return self._sections

    def set_sections(self, sections):
        logger.debug('setting navpane sections')

        animation = QtCore.QPropertyAnimation(self._dock_widget, 'minimumWidth', self)
        animation.setDuration( 500 )
        animation.setStartValue( 10 )
        animation.setEndValue( 220 )
        animation.start()
        
        self._sections = sections
        self._buttons = [(
            index,
            section.get_verbose_name(),
            section.get_icon().getQPixmap(),
        ) for index, section in enumerate(sections)]

        for index, name, pixmap in self._buttons:
            tree_widget = self.get_tree_widget()
            if index!=0:
                tree_widget.setMaximumHeight(0)

            pane_button = PaneButton(name, pixmap)
            pane_button.pressed.connect(self.change_current)

            self._dock_widget.layout().addWidget(pane_button)
            self._dock_widget.layout().addWidget(tree_widget)

            last_tree_index = self._dock_widget.layout().count() - 1

            def get_models_for_tree():
                return (last_tree_index, self._sections[index].get_items())

            post(get_models_for_tree, self.set_models_for_tree)

        self.change_current(0)

    def set_models_for_tree(self, (tree_index, items)):
        tree_widget = self._dock_widget.layout().itemAt(tree_index).widget()
        for item in items:
            label = item.get_verbose_name()
            tree_widget.section_items.append(item)
            tree_widget.modelitems.append(ModelItem(tree_widget, [label]))
            tree_widget.itemClicked.connect(self.open_in_current_view)

    @QtCore.pyqtSlot(int)
    def change_current(self, index):
        logger.debug('setting current navpane index to %s' % index)

        self._animation.stop()
        self._animation.clear()
        
        if self._current_tree_widget is not None:
            current_index = self._dock_widget.layout().indexOf(self._current_tree_widget) - 1
            if index == current_index:
                return
            self._dock_widget.layout().itemAt(current_index).widget().toggle_bold()
            hide = QtCore.QPropertyAnimation(self._current_tree_widget, 'maximumHeight')
            hide.setDuration( 150 )
            hide.setStartValue( self._current_tree_widget.height() )
            hide.setEndValue( 0 )
            self._animation.addAnimation( hide )
                    
        self._dock_widget.layout().itemAt(index).widget().toggle_bold()
        tree_widget = self._dock_widget.layout().itemAt(index+1).widget()
        tree_widget.show()
        show = QtCore.QPropertyAnimation(tree_widget, 'maximumHeight')
        show.setDuration( 150 )
        show.setStartValue( 0 )
        show.setEndValue( 1000 )
        self._animation.addAnimation( show )
        self._animation.start()
        self._current_tree_widget = tree_widget

    def get_section_item(self, item):
        index = self._current_tree_widget.indexFromItem(item)
        return self._current_tree_widget.section_items[index.row()]

    def create_context_menu(self, point):
        logger.debug('creating context menu')
        item = self._current_tree_widget.itemAt(point)
        if item:
            self._current_tree_widget.setCurrentItem(item)
            self._current_tree_widget.contextmenu.popup(
                self._current_tree_widget.mapToGlobal(point)
            )

    @QtCore.pyqtSlot(QtGui.QTreeWidgetItem, int)
    def open_in_current_view(self, item, _column):
        """pops a model window in parent's workspace"""
        logger.debug('poping a window in parent')
        item = self._current_tree_widget.currentItem()
        index = self._current_tree_widget.indexFromItem(item)
        section_item = self._current_tree_widget.section_items[index.row()]
        new_view = section_item.get_action().run(self.workspace)
        if new_view:
            self.workspace.set_view(new_view)

    @QtCore.pyqtSlot()
    def open_in_new_view(self):
        """pops a model window in parent's workspace"""
        logger.debug('poping a window in parent')
        item = self._current_tree_widget.currentItem()
        index = self._current_tree_widget.indexFromItem(item)
        section_item = self._current_tree_widget.section_items[index.row()]
        new_view = section_item.get_action().run(self.workspace)
        if new_view:
            self.workspace.add_view(new_view)
