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

"""custom tree and tree-items widgets"""

import logging
logger = logging.getLogger('camelot.view.controls.modeltree')

from ...core.qt import Qt, QtWidgets

from camelot.core.utils import ugettext as _

class ModelItem(QtWidgets.QTreeWidgetItem):
    """Custom tree item widget"""

    def __init__(self, parent, columns_names, section_item):
        logger.debug('creating new modelitem')
        super(ModelItem, self).__init__(parent, columns_names)
        
        self.textColumn = 0
        self.iconColumn = 1
        self.section_item = section_item

        for column in (self.textColumn, self.iconColumn):
            self.setToolTip(column, _('Right click to open in New Tab'))

    def _underline(self, enable=False):
        font = self.font(self.textColumn)
        font.setUnderline(enable)
        self.setFont(self.textColumn, font)

    def set_icon(self, icon):
        self.setIcon(self.iconColumn, icon)
        
class ModelTree(QtWidgets.QTreeWidget):
    """Custom tree widget"""

    def __init__(self, header_labels=[''], parent=None):
        logger.debug('creating new modeltree')
        super(ModelTree, self).__init__(parent)
        # we don't select entire rows
        self.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectItems)
        
        # we track mouse movement when no button is pressed
        self.setMouseTracking(True)
        self.header_labels = header_labels
        
        self.setColumnCount(2)
        self.setColumnWidth(0, 160)
        self.setColumnWidth(1, 18)
        self.setHorizontalScrollBarPolicy( Qt.ScrollBarAlwaysOff )
        self.setSelectionBehavior( self.SelectRows )
        
        self.clear_model_items()
        self.clear_section_items()
        self.fix_header_labels()

    def resizeEvent(self, event):
        self.setColumnWidth(0, self.width()  - 30 )
        
    def fix_header_labels(self):
        self.setHeaderHidden(True)

    def clear_section_items(self):
        self.section_items = []
        
    def clear_model_items(self):
        self.modelitems = []

    def mousePressEvent(self, event):
        """Custom context menu"""
        if event.button() == Qt.RightButton:
            self.customContextMenuRequested.emit( event.pos() )
            event.accept()
        else:
            QtWidgets.QTreeWidget.mousePressEvent(self, event)

    def leaveEvent(self, event):
        if not self.modelitems: return
        for item in self.modelitems: item._underline(False)

    def mouseMoveEvent(self, event):
        if not self.modelitems: return
        for item in self.modelitems: item._underline(False)

        item = self.itemAt(self.mapFromGlobal(self.cursor().pos()))
        if item:
            item._underline(True)




