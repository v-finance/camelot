#  ============================================================================
#
#  Copyright (C) 2007-2008 Conceptive Engineering bvba. All rights reserved.
#  www.conceptive.be / project-camelot@conceptive.be
#
#  This file is part of the Camelot Library.
#
#  This file may be used under the terms of the GNU General Public
#  License version 2.0 as published by the Free Software Foundation
#  and appearing in the file LICENSE.GPL included in the packaging of
#  this file.  Please review the following information to ensure GNU
#  General Public Licensing requirements will be met:
#  http://www.trolltech.com/products/qt/opensource.html
#
#  If you are unsure which license is appropriate for your use, please
#  review the following information:
#  http://www.trolltech.com/products/qt/licensing.html or contact
#  project-camelot@conceptive.be.
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

_ = lambda x:x

filter_changed_signal = QtCore.SIGNAL('filter_changed')

class FilterList(QtGui.QScrollArea):
    """A list with filters that can be applied on a query in the tableview"""

    def __init__(self, items, parent):
        """
    :param items: list of tubles (name, choices) for constructing the different filterboxes
    """
        QtGui.QScrollArea.__init__(self, parent)
        widget = QtGui.QWidget(self)
        self.setFrameStyle(QtGui.QFrame.NoFrame)
        layout = QtGui.QVBoxLayout()

        for filter,(name,options) in items:
            filter_widget = filter.render(widget, name, options)
            layout.addWidget(filter_widget)
            self.connect(filter_widget,
                         filter_changed_signal,
                         self.emit_filters_changed)

        layout.addStretch()
        widget.setLayout(layout)
        self.setWidget(widget)
        #self.setMaximumWidth(self.fontMetrics().width( ' ' )*70)
        if len(items) == 0:
            self.setMaximumWidth(0)
        else:
            self.setSizePolicy( QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding )

    def decorate_query(self, query):
        for i in range(self.widget().layout().count()):
            if self.widget().layout().itemAt(i).widget():
                query = self.widget().layout().itemAt(i).widget().decorate_query(query)
        return query

    def emit_filters_changed(self):
        logger.debug('filters changed')
        self.emit(QtCore.SIGNAL('filters_changed'))
