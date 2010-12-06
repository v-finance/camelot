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
logger = logging.getLogger('camelot.view.controls.navpane2')

from PyQt4 import QtCore, QtGui
from PyQt4.QtCore import Qt
from PyQt4.QtGui import QIcon
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

class PlainWidgetWithNoMargins(QWidget):

    def __init__(self, layout=None, parent=None):
        super(PlainWidgetWithNoMargins, self).__init__(parent)
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)

class NavigationPane(QDockWidget):

    def __init__(self, app_admin, workspace, parent):
        super(QDockWidget, self).__init__(parent)

        self.workspace = workspace
        self.app_admin = app_admin

        self._tree_items = None
        self._title_widget = QWidget()
        self._toolbox = self.get_toolbox()
        self._shared_tree_widget = None
        # hack for removing the dock title bar
        self.setTitleBarWidget(self._title_widget)
        self.setWidget(self._toolbox)

        self.setFeatures(QDockWidget.NoDockWidgetFeatures)

        # should happen at the top level
        #self.setStyleSheet(art.read('stylesheet/navpane2_office2007_blue.qss'))

        self.app_admin.sections_changed_signal.connect(self.update_sections)
        self.update_sections()

    @QtCore.pyqtSlot()
    def update_sections(self):
        post(self.app_admin.get_sections, self.set_sections)

    def get_toolbox(self):
        tb = QToolBox()
        tb.setFrameShape(QFrame.NoFrame)
        tb.layout().setContentsMargins(0,0,0,0)
        tb.layout().setSpacing(1)
        return tb

    def get_tree_widget(self):
        tw = ModelTree(parent=self)
        # i hate the sunken frame style
        tw.setFrameShape(QFrame.NoFrame)
        tw.setFrameShadow(QFrame.Plain)
        tw.contextmenu = QMenu(self)
        act = ActionFactory.new_tab(self, self.open_in_new_view)
        tw.contextmenu.addAction( act )
        tw.setContextMenuPolicy(Qt.CustomContextMenu)
        tw.customContextMenuRequested.connect(self.create_context_menu)

        return tw

    def get_sections(self):
        return self._sections

    def set_sections(self, sections):
        logger.debug('setting navpane sections')

        animation = QtCore.QPropertyAnimation(self._toolbox, "width")
        animation.setDuration( 500 )
        animation.setStartValue( 0 )
        animation.setEndValue( 220 )
        animation.start()
        
        self._sections = sections
        self._buttons = [(
            index,
            section.get_verbose_name(),
            section.get_icon().getQPixmap(),
        ) for index, section in enumerate(sections)]

        # performs QToolBox clean up
        # QToolbox won't delete items we have to do it explicitly
        count = self._toolbox.count()
        while count:
            item = self._toolbox.widget(count-1)
            self._toolbox.removeItem(count-1)
            item.deleteLater()
            count -= 1
            
        self._shared_tree_widget = self.get_tree_widget()
        self._shared_tree_widget.itemClicked.connect(self.open_in_current_view)
        self._toolbox_widgets = []

        for _i, name, pixmap in self._buttons:
            # TODO: old navpane used translation here
            name = unicode(name)
            icon = QIcon(pixmap)
            pwdg = PlainWidgetWithNoMargins(QVBoxLayout())
            self._toolbox_widgets.append(pwdg)
            self._toolbox.addItem(pwdg, icon, name)

        self._toolbox.currentChanged.connect(self.change_current)
        self._toolbox.setCurrentIndex(0)
        # setCurrentIndex does not emit currentChanged
        self.change_current(0)
        # WARNING: hardcoded width
        self._toolbox.setMinimumWidth(220)

    @QtCore.pyqtSlot(int)
    def change_current(self, index):
        logger.debug('setting current navpane index to %s' % index)

        def get_models_for_tree():
            """returns pairs of (Admin, query) classes for items in the tree"""
            if index < len(self._sections):
                section = self._sections[index]
                return section.get_items()
            return []

        post(get_models_for_tree, self.set_items_in_tree)

    def set_items_in_tree(self, items):
        logger.debug('setting items for current navpane section')
        self._shared_tree_widget.clear()
        self._shared_tree_widget.clear_model_items()
        self._toolbox.currentWidget().layout().addWidget(self._shared_tree_widget)
        self._tree_items = items

        if not items: return

        for item in items:
            label = item.get_verbose_name()
            model_item = ModelItem(self._shared_tree_widget, [label])
            self._shared_tree_widget.modelitems.append(model_item)

    def get_section_item(self, item):
        index = self._shared_tree_widget.indexFromItem(item)
        return self._tree_items[index.row()]

    def create_context_menu(self, point):
        logger.debug('creating context menu')
        item = self._shared_tree_widget.itemAt(point)
        if item:
            self._shared_tree_widget.setCurrentItem(item)
            self._shared_tree_widget.contextmenu.popup(
                self._shared_tree_widget.mapToGlobal(point)
            )
      
    @QtCore.pyqtSlot(QtGui.QTreeWidgetItem, int)
    def open_in_current_view(self, item, _column):
        """pops a model window in parent's workspace"""
        logger.debug('poping a window in parent')
        item = self._shared_tree_widget.currentItem()
        index = self._shared_tree_widget.indexFromItem(item)
        section_item = self._tree_items[index.row()]
        new_view = section_item.get_action().run(self.workspace)
        if new_view:
            self.workspace.set_view(new_view)
                  
    @QtCore.pyqtSlot()
    def open_in_new_view(self):
        """pops a model window in parent's workspace"""
        logger.debug('poping a window in parent')
        item = self._shared_tree_widget.currentItem()
        index = self._shared_tree_widget.indexFromItem(item)
        section_item = self._tree_items[index.row()]
        new_view = section_item.get_action().run(self.workspace)
        if new_view:
            self.workspace.add_view(new_view)
