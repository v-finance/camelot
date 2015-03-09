#  ============================================================================
#
#  Copyright (C) 2007-2013 Conceptive Engineering bvba. All rights reserved.
#  www.conceptive.be / info@conceptive.be
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
#  visit www.python-camelot.com or contact info@conceptive.be
#
#  This file is provided AS IS with NO WARRANTY OF ANY KIND, INCLUDING THE
#  WARRANTY OF DESIGN, MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE.
#
#  For use of this library in commercial applications, please contact
#  info@conceptive.be
#
#  ============================================================================

"""Controls related to visualizing object hierarchy"""

import logging
logger = logging.getLogger( 'camelot.view.controls.inheritance' )

from ...core.qt import QtCore, QtGui, QtWidgets
from camelot.view.controls.modeltree import ModelTree
from camelot.view.controls.modeltree import ModelItem


class SubclassItem(ModelItem):
    def __init__(self, parent, admin):
        ModelItem.__init__(self, parent, [admin.get_verbose_name()], None)
        self.admin = admin

class SubclassTree( ModelTree ):
    """Widget to select subclasses of a certain entity, where the subclasses
    are represented in a tree

    emits subclass_clicked_signal when a subclass has been selected
    """

    subclass_clicked_signal = QtCore.qt_signal(object)
    
    def __init__(self, admin, parent=None):
        header_labels = ['Types']
        ModelTree.__init__(self, header_labels, parent=None)
        self.admin = admin
        self.setSizePolicy(
            QtGui.QSizePolicy.Expanding,
            QtGui.QSizePolicy.Expanding
        )
        self.clicked.connect( self.emit_subclass_clicked )

    def set_subclasses(self, subclasses):

        def append_subclasses(class_item, subclasses):
            for subclass_admin, subsubclasses in subclasses:
                subclass_item = SubclassItem(class_item, subclass_admin)
                self.modelitems.append(subclass_item)
                append_subclasses(subclass_item, subsubclasses)
                
        self.clear_model_items()
        if len(subclasses):
            top_level_item = SubclassItem(self, self.admin)
            self.modelitems.append(top_level_item)
            append_subclasses(top_level_item, subclasses)
            top_level_item.setExpanded(True)

    @QtCore.qt_slot(QtCore.QModelIndex)
    def emit_subclass_clicked(self, index):
        logger.debug('subclass clicked at position %s' % index.row())
        item = self.itemFromIndex(index)
        self.subclass_clicked_signal.emit( item.admin )

class SubclassDialog(QtWidgets.QDialog):
    """A dialog requesting the user to select a subclass"""
    
    def __init__(self, admin, subclass_tree, parent=None):
        QtWidgets.QDialog.__init__(self, parent)
        tree_widget = SubclassTree(admin, self)
        tree_widget.set_subclasses(subclass_tree)
        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(tree_widget)
        self.setLayout(layout)
        self.selected_subclass = None
        tree_widget.subclass_clicked_signal.connect( self._subclass_clicked )

    @QtCore.qt_slot(object)
    def _subclass_clicked(self, admin):
        self.selected_subclass = admin
        self.accept()




