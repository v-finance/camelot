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

"""left navigation pane"""

import logging
logger = logging.getLogger('camelot.view.controls.navpane2')

from PyQt4 import QtCore, QtGui
from PyQt4.QtCore import Qt
from PyQt4.QtGui import QMenu
from PyQt4.QtGui import QFrame
from PyQt4.QtGui import QWidget
from PyQt4.QtGui import QToolBox
from PyQt4.QtGui import QDockWidget
from PyQt4.QtGui import QVBoxLayout

from camelot.view.action import ActionFactory
from camelot.view.model_thread import post
from camelot.view.controls.modeltree import ModelItem
from camelot.view.controls.modeltree import ModelTree

class PaneSection(QWidget):

    def __init__(self, parent, section, workspace):
        super(PaneSection, self).__init__(parent)
        self._items = []
        self._workspace = workspace
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        section_tree = ModelTree(parent=self)
        # i hate the sunken frame style
        section_tree.setFrameShape(QFrame.NoFrame)
        section_tree.setFrameShadow(QFrame.Plain)
        section_tree.contextmenu = QMenu(self)
        act = ActionFactory.new_tab(self, self.open_in_new_view)
        act.setIconVisibleInMenu(False)
        section_tree.contextmenu.addAction( act )
        section_tree.setContextMenuPolicy(Qt.CustomContextMenu)
        section_tree.customContextMenuRequested.connect(self.create_context_menu)
        section_tree.setObjectName( 'SectionTree' )
        section_tree.itemClicked.connect( self.open_in_current_view )
        section_tree.setWordWrap( False )
        layout.addWidget( section_tree )
        self.setLayout(layout)
        post( section.get_items, self.set_items )

    @QtCore.pyqtSlot(object)
    def set_items(self, items):
        logger.debug('setting items for current navpane section')
        section_tree = self.findChild(QtGui.QWidget, 'SectionTree')
        self._items = items
        if section_tree:
            section_tree.clear()
            section_tree.clear_model_items()
    
            if not items: return
    
            for item in items:
                label = item.get_verbose_name()
                icon = item.get_icon()
                model_item = ModelItem(section_tree, [label])
                if icon:
                    model_item.set_icon(icon.getQIcon())
                section_tree.modelitems.append(model_item)
            section_tree.resizeColumnToContents( 0 )

    def create_context_menu(self, point):
        logger.debug('creating context menu')
        section_tree = self.findChild(QtGui.QWidget, 'SectionTree')
        if section_tree:
            item = section_tree.itemAt(point)
            if item:
                section_tree.setCurrentItem(item)
                section_tree.contextmenu.popup(section_tree.mapToGlobal(point))

    @QtCore.pyqtSlot(QtGui.QTreeWidgetItem, int)
    def open_in_current_view(self, item, _column):
        """pops a model window in parent's workspace"""
        logger.debug('poping a window in parent')
        section_tree = self.findChild(QtGui.QWidget, 'SectionTree')
        if section_tree:
            item = section_tree.currentItem()
            index = section_tree.indexFromItem(item)
            section_item = self._items[index.row()]
            new_view = section_item.get_action().run(self._workspace)
            icon = section_item.get_action().get_icon()
            if new_view:
                if icon:
                    self._workspace.set_view(new_view, icon = icon.getQIcon())
                else:
                    self._workspace.set_view(new_view)

    @QtCore.pyqtSlot()
    def open_in_new_view(self):
        """pops a model window in parent's workspace"""
        logger.debug('poping a window in parent')
        section_tree = self.findChild(QtGui.QWidget, 'SectionTree')
        if section_tree:
            item = section_tree.currentItem()
            index = section_tree.indexFromItem(item)
            section_item = self._items[index.row()]
            new_view = section_item.get_action().run(self._workspace)
            icon = section_item.get_action().get_icon()
            if new_view:
                if icon:
                    self._workspace.add_view(new_view, icon = icon.getQIcon())
                else:
                    self._workspace.add_view(new_view)
                        
class NavigationPane(QDockWidget):

    def __init__(self, app_admin, workspace, parent):
        super(NavigationPane, self).__init__(parent)

        self._workspace = workspace
        self.app_admin = app_admin
        
        tb = QToolBox()
        tb.setFrameShape(QFrame.NoFrame)
        tb.layout().setContentsMargins(0,0,0,0)
        tb.layout().setSpacing(1)
        tb.setObjectName('toolbox')
        tb.setMouseTracking(True)
        
        # hack for removing the dock title bar
        self.setTitleBarWidget(QWidget())
        self.setWidget(tb)
        self.setFeatures(QDockWidget.NoDockWidgetFeatures)

        self.app_admin.sections_changed_signal.connect(self.update_sections)
        self.update_sections()

    def wheelEvent(self, wheel_event):
        steps = -1 * wheel_event.delta() / (8 * 15)
        toolbox = self.findChild(QtGui.QWidget, 'toolbox')
        if steps and toolbox:
            current_index = toolbox.currentIndex()
            toolbox.setCurrentIndex( max( 0, min( current_index + steps, toolbox.count() ) ) )
        
    @QtCore.pyqtSlot()
    def update_sections(self):
        post(self.app_admin.get_sections, self.set_sections)

    def get_sections(self):
        return self._sections

    @QtCore.pyqtSlot(object)
    def set_sections(self, sections):
        logger.debug('setting navpane sections')
        toolbox = self.findChild(QtGui.QWidget, 'toolbox')
        animation = QtCore.QPropertyAnimation(toolbox, 'minimumWidth', self)
        animation.setDuration( 500 )
        animation.setStartValue( 0 )
        animation.setEndValue( 220 )
        animation.start()
        if self._workspace:
            animation.finished.connect(self._workspace._background_widget.makeInteractive)

        # performs QToolBox clean up
        # QToolbox won't delete items we have to do it explicitly
        count = toolbox.count()
        while count:
            item = toolbox.widget(count-1)
            toolbox.removeItem(count-1)
            item.deleteLater()
            count -= 1
            
        for section in sections:
            # TODO: old navpane used translation here
            name = unicode( section.get_verbose_name() )
            icon = section.get_icon().getQIcon()
            pwdg = PaneSection(toolbox, section, self._workspace)
            toolbox.addItem(pwdg, icon, name)

        toolbox.setCurrentIndex(0)
        # WARNING: hardcoded width
        #self._toolbox.setMinimumWidth(220)

