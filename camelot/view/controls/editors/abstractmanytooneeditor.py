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

from PyQt4 import QtGui
from PyQt4 import QtCore

from camelot.core.utils import ugettext as _

class AbstractManyToOneEditor(object):
    """Helper functions for implementing a `ManyToOneEditor`, to be used in the
    `ManyToOneEditor` and in the `ManyToManyEditor`"""

    def createSelectView(self):
        #search_text = unicode(self.search_input.text())
        search_text = ''
        admin = self.admin
        query = self.admin.entity.query

        class SelectDialog(QtGui.QDialog):
            
            entity_selected_signal = QtCore.pyqtSignal(object)
            
            def __init__(self, parent):
                super(SelectDialog, self).__init__(None)
                layout = QtGui.QVBoxLayout()
                layout.setContentsMargins( 0, 0, 0, 0)
                layout.setSpacing(0)
                self.setWindowTitle( _('Select %s') % admin.get_verbose_name())
                self.select = admin.create_select_view(
                    query,
                    parent=parent,
                    search_text=search_text
                )
                layout.addWidget(self.select)
                self.setLayout(layout)
                self.select.entity_selected_signal.connect( self.selectEntity )
                
            @QtCore.pyqtSlot(object)
            def selectEntity(self, entity_instance_getter):
                self.entity_selected_signal.emit( entity_instance_getter )
                self.close()

        self.selectDialog = SelectDialog(self)
        self.selectDialog.entity_selected_signal.connect( self.selectEntity )
        #self.selectDialog.show()
        self.selectDialog.exec_()

    def selectEntity(self, entity_instance_getter):
        #raise Exception('Not implemented')
        raise NotImplementedError


