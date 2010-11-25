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

from PyQt4 import QtCore
from PyQt4.QtGui import QIcon
from PyQt4.QtGui import QFrame
from PyQt4.QtGui import QWidget
from PyQt4.QtGui import QToolBox
from PyQt4.QtGui import QDockWidget
from PyQt4.QtGui import QTreeWidget

from camelot.view import art
from camelot.view.model_thread import post
from camelot.view.controls.modeltree import ModelItem
from camelot.view.controls.modeltree import ModelTree


class NavigationPane(QDockWidget):

    def __init__(self, app_admin, workspace, parent):
        super(QDockWidget, self).__init__(parent)

        self.workspace = workspace
        self.app_admin = app_admin

        self._tree_items = None
        self._toolbox = self.get_toolbox()
        self._shared_tree_widget = self.get_tree_widget()

        # hack for removing the dock title bar
        self.setTitleBarWidget(QWidget())
        self.titleBarWidget().hide()
        self.setWidget(self._toolbox)

        self.setFeatures(QDockWidget.NoDockWidgetFeatures)

        self.setStyleSheet(art.read('stylesheet/navpane2_office2007_blue.qss'))

        self.app_admin.sections_changed_signal.connect(self.auth_update)
        self.auth_update()

    @QtCore.pyqtSlot()
    def auth_update(self):
        post(self.app_admin.get_sections, self.set_sections)

    def get_toolbox(self):
        #tb_item_0_tree = QTreeWidget(tb_item_0)
        #tb_item_0_tree.setFrameShape(QFrame.NoFrame)
        #tb_item_0_tree.setFrameShadow(QFrame.Plain)
        #tb_item_0_tree.setLineWidth(0)
        #tb_item_0_tree.setHeaderHidden(True)

        tb = QToolBox()
        tb.layout().setSpacing(1)
        return tb

    def get_tree_widget(self):
        # constructor needs a list of header labels
        # tree will be reparented
        tw = ModelTree([''], self)
        return tw

    def get_sections(self):
        return self._sections

    def set_sections(self, sections):
        logger.debug('setting navpane sections')
        self._sections = sections
        self._buttons = [(
            index,
            section.get_verbose_name(),
            section.get_icon().getQPixmap(),
        ) for index, section in enumerate(sections)]

        for i, name, pixm in self._buttons:
            # TODO: old navpane used translation here
            name = unicode(name)
            self._toolbox.addItem(QWidget(), QIcon(pixm), name)

        self._toolbox.currentChanged.connect(self.change_current)
        self._toolbox.setCurrentIndex(0)

    @QtCore.pyqtSlot(int, unicode)
    def change_current(self, index):
        logger.debug('set current to index %s' % index)

        def get_models_for_tree():
            """Return pairs of (Admin, query) classes for items in the tree"""
            if index < len(self._sections):
                section = self._sections[index]
                return section.get_items()
            return []

        post(get_models_for_tree, self.set_items_in_tree)

    def set_items_in_tree(self, items):
        self._shared_tree_widget.clear()
        self._shared_tree_widget.clear_model_items()
        self._shared_tree_widget.setParent(self._toolbox.currentWidget())
        self._tree_items = items

        if not items: return

        for item in items:
            model_item = ModelItem(
                self._shared_tree_widget,
                [item.get_verbose_name()]
            )
            self._shared_tree_widget.modelitems.append(model_item)

        self._shared_tree_widget.update()
