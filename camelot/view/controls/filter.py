#  ==================================================================================
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
#  ==================================================================================

"""Controls to filter data"""
import logging

logger = logging.getLogger('controls.filter')
logger.setLevel(logging.DEBUG)

from PyQt4 import QtCore, QtGui

_ = lambda x:x

class FilterBox(QtGui.QGroupBox):
  """A box containing a filter that can be applied on a table view, this filter is
  based on the distinct values in a certain column"""

  def __init__(self, name, choices, parent):
    QtGui.QGroupBox.__init__(self, _(name), parent)
    self.group = QtGui.QButtonGroup()
    self.item = name
    self.unique_values = []
    self.choices = None
    self.setChoices(choices)
     
  def emit_filter_changed(self, state):
    self.emit(QtCore.SIGNAL('filter_changed'))

  def setChoices(self, choices):
    self.choices = choices
    layout = QtGui.QVBoxLayout()
    for i,name in enumerate([unicode(c[0]) for c in choices]):
      button = QtGui.QRadioButton(_(name))
      layout.addWidget(button)
      self.group.addButton(button, i)
      if i==0:
        button.setChecked(True)
      self.connect(button, QtCore.SIGNAL('toggled(bool)'), self.emit_filter_changed)
    layout.addStretch()
    self.setLayout(layout)

  def decorate_query(self, query):
    checked = self.group.checkedId()
    if checked>=0:
      return self.choices[checked][1](query)
    return query
          
  def apply_filter(self, query):
    '''Apply this FilterBox's filter on a query, if All is selected, no
    filter is applied at all.
    @return the modified query
    '''
    selected_value = self.unique_values[self.get_selection()]
    if selected_value==FilterBox.all:
      return query
    if isinstance(self.col.type, Float):
      delta = 0.1**self.col.type.precision
      return query.filter(and_(self.col>=selected_value-delta, self.col<=selected_value+delta))
    return query.filter(self.col==selected_value)
  
  def __del__(self):
    logger.debug('delete filter box')
      
class FilterList(QtGui.QScrollArea):
  """A list with filters that can be applied on a query in the 
  tableview"""
  def __init__(self, items, parent):
    """@param item list of tubles (name, choices) for constructing the
    different filterboxes"""
    QtGui.QScrollArea.__init__(self, parent)
    self.widget = QtGui.QWidget()
    layout = QtGui.QVBoxLayout()
    self.filters = []
    layout.addWidget(QtGui.QLabel(_('Filter'), self))
    
    for filter,(name,options) in items:
      widget = filter.render(self, name, options)
      layout.addWidget(widget)
      self.filters.append(widget)
      self.connect(widget, QtCore.SIGNAL('filter_changed'), self.emit_filters_changed)

    layout.addStretch()
    self.widget.setLayout(layout)
    self.setWidget(self.widget)
    self.setMaximumWidth(self.widget.width() + 30)
    if len(self.filters) == 0:
      self.setMaximumWidth(0)

  def decorate_query(self, query):
    for filter in self.filters:
      query = filter.decorate_query(query)
    return query
  
  def emit_filters_changed(self):
    logger.debug('filters changed')
    self.emit(QtCore.SIGNAL('filters_changed'))
    
  def __del__(self):
    logger.debug('delete filter list')