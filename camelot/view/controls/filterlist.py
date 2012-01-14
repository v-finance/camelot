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

"""Controls to filter data"""

import logging
logger = logging.getLogger('camelot.view.controls.filter')

from PyQt4 import QtGui, QtCore

class FilterList( QtGui.QWidget ):
    """A list with filters that can be applied on a query in the tableview"""

    filters_changed_signal = QtCore.pyqtSignal()
    
    def __init__(self, items, parent):
        """
    :param items: list of tuples (filter, (name, choices)) for constructing the different filterboxes
    """
        super(FilterList, self).__init__(parent)
        #self.setFrameStyle(QtGui.QFrame.NoFrame)
        layout = QtGui.QVBoxLayout()
        layout.setSpacing( 4 )
        for filter, filter_data in items:
            filter_widget = filter.render( filter_data, parent = self )
            layout.addWidget(filter_widget)
            filter_widget.filter_changed_signal.connect( self.emit_filters_changed )
        layout.addStretch()
        self.setLayout(layout)
        if len(items) == 0:
            self.setMaximumWidth(0)
        else:
            self.setSizePolicy( QtGui.QSizePolicy.MinimumExpanding, 
                                QtGui.QSizePolicy.Expanding )

    def decorate_query(self, query):
        for i in range(self.layout().count()):
            if self.layout().itemAt(i).widget():
                query = self.layout().itemAt(i).widget().decorate_query(query)
        return query

    @QtCore.pyqtSlot()
    def emit_filters_changed(self):
        logger.debug('filters changed')
        self.filters_changed_signal.emit()

