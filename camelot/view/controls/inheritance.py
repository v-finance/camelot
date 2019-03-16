#  ============================================================================
#
#  Copyright (C) 2007-2016 Conceptive Engineering bvba.
#  www.conceptive.be / info@conceptive.be
#
#  Redistribution and use in source and binary forms, with or without
#  modification, are permitted provided that the following conditions are met:
#      * Redistributions of source code must retain the above copyright
#        notice, this list of conditions and the following disclaimer.
#      * Redistributions in binary form must reproduce the above copyright
#        notice, this list of conditions and the following disclaimer in the
#        documentation and/or other materials provided with the distribution.
#      * Neither the name of Conceptive Engineering nor the
#        names of its contributors may be used to endorse or promote products
#        derived from this software without specific prior written permission.
#
#  THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
#  ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
#  WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
#  DISCLAIMED. IN NO EVENT SHALL <COPYRIGHT HOLDER> BE LIABLE FOR ANY
#  DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
#  (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
#  LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
#  ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
#  (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
#  SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#
#  ============================================================================

"""Controls related to visualizing object hierarchy"""

import logging
logger = logging.getLogger( 'camelot.view.controls.inheritance' )

from ...core.qt import QtCore, QtWidgets
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
            QtWidgets.QSizePolicy.Expanding,
            QtWidgets.QSizePolicy.Expanding
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





