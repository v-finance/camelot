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

class FilterList(QtGui.QScrollArea):
  """A list with filters that can be applied on a query in the tableview"""
 
  def __init__(self, items, parent):
    """
:param items: list of tubles (name, choices) for constructing the different filterboxes
"""
    QtGui.QScrollArea.__init__(self, parent)
    self.widget = QtGui.QWidget()
    self.setFrameStyle(QtGui.QFrame.NoFrame)
    layout = QtGui.QVBoxLayout()
    self.filters = []
    
    for filter,(name,options) in items:
      widget = filter.render(self, name, options)
      layout.addWidget(widget)
      self.filters.append(widget)
      self.connect(widget,
                   QtCore.SIGNAL('filter_changed'),
                   self.emit_filters_changed)

    layout.addStretch()
    self.widget.setLayout(layout)
    self.setWidget(self.widget)
    self.setMaximumWidth(self.widget.width() + 10)
    if len(self.filters) == 0:
      self.setMaximumWidth(0)

  def decorate_query(self, query):
    for filter in self.filters:
      query = filter.decorate_query(query)
    return query

  def emit_filters_changed(self):
    logger.debug('filters changed')
    self.emit(QtCore.SIGNAL('filters_changed'))
