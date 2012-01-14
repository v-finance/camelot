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

"""Controls related to visualizing object hierarchy"""

import logging
logger = logging.getLogger( 'camelot.view.controls.inheritance' )

from PyQt4 import QtGui
from PyQt4 import QtCore

from camelot.view.model_thread import post
from camelot.view.controls.modeltree import ModelTree
from camelot.view.controls.modeltree import ModelItem

QT_MAJOR_VERSION = float('.'.join(str(QtCore.QT_VERSION_STR).split('.')[0:2]))


class SubclassItem(ModelItem):
    def __init__(self, parent, admin):
        ModelItem.__init__(self, parent, [admin.get_verbose_name()], None)
        self.admin = admin

class SubclassTree( ModelTree ):
    """Widget to select subclasses of a certain entity, where the subclasses
    are represented in a tree

    emits subclassClicked when a subclass has been selected
    """

    subclass_clicked_signal = QtCore.pyqtSignal(object)
    
    def __init__(self, admin, parent):
        header_labels = ['Types']
        ModelTree.__init__(self, header_labels, parent)
        self.admin = admin
        self.subclasses = []
        post(self.admin.get_subclass_tree, self.setSubclasses)
        self.setSizePolicy(
            QtGui.QSizePolicy.Minimum,
            QtGui.QSizePolicy.Expanding
        )
        self.clicked.connect( self.emit_subclass_clicked )

    def setSubclasses(self, subclasses):
        logger.debug('setting subclass tree')
        self.subclasses = subclasses

        def append_subclasses(class_item, subclasses):
            for subclass_admin, subsubclasses in subclasses:
                subclass_item = SubclassItem(class_item, subclass_admin)
                self.modelitems.append(subclass_item)
                append_subclasses(subclass_item, subsubclasses)

        if len(subclasses):
            self.clear_model_items()
            top_level_item = SubclassItem(self, self.admin)
            self.modelitems.append(top_level_item)
            append_subclasses(top_level_item, subclasses)
            top_level_item.setExpanded(True)
            self.setMaximumWidth(self.fontMetrics().width(' ')*70)
        else:
            self.setMaximumWidth(0)

    @QtCore.pyqtSlot(QtCore.QModelIndex)
    def emit_subclass_clicked(self, index):
        logger.debug('subclass clicked at position %s' % index.row())
        item = self.itemFromIndex(index)
        self.subclass_clicked_signal.emit( item.admin )

class SubclassDialog(QtGui.QDialog):
    """A dialog requesting the user to select a subclass"""
    
    def __init__(self, parent, admin):
        QtGui.QDialog.__init__(self, parent)
        subclass_tree = SubclassTree(admin, self)

        layout = QtGui.QVBoxLayout()
        layout.addWidget(subclass_tree)
        layout.addStretch(1)
        self.setLayout(layout)

        self.selected_subclass = None
        subclass_tree.subclass_clicked_signal.connect( self._subclass_clicked )

    @QtCore.pyqtSlot(object)
    def _subclass_clicked(self, admin):
        self.selected_subclass = admin
        self.accept()



