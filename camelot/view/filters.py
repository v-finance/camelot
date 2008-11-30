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

"""
Python structures to represent filters.
These structures can be transformed to QT forms.
"""

def structure_to_filter(structure):
  """Convert a python data structure to a filter, using the following rules :
  
  if structure is an instance of Filter, return structure
  else create a GroupBoxFilter from the structure
  """
  if isinstance(structure, Filter):
    return structure
  return GroupBoxFilter(structure)

class Filter(object):
  """Base class for filters"""
  
  def __init__(self, attribute):
    """@param attribute: the attribute on which to filter, this attribute
    may contain dots to indicate relationships that need to be followed, 
    eg.  'person.groups.name'"""
    self.attribute = attribute
     
  def render(self, parent, name, options):
    """Render this filter as a qt object
    @param parent: its parent widget
    @param name: the name of the filter
    @param options: the options that can be selected, where each option is a list
    of tuples containting (option_name, query_decorator)  
    
    The name and the list of options can be fetched with get_name_and_options"""
    raise NotImplementedException()
    
  def get_name_and_options(self, admin):
    """return a tuple of the name of the filter and a list of options that can be selected. 
    Each option is a tuple of the name of the option, and a filter function to
    decorate a query
    @return:  (filter_name, [(option_name, query_decorator), ...)
    """
    from sqlalchemy.sql import select
    from elixir import session
    #session.bind = self.entity.table.metadata.bind
    filter_names = []
    joins = []
    table = admin.entity.table
    for field_name in self.attribute.split('.'):
      attributes = admin.getFieldAttributes(field_name)
      filter_names.append(attributes['name'])
      if attributes['widget'] in ('one2many', 'many2many', 'many2one'):
        admin = attributes['admin']
        joins.append(field_name)
        if attributes['widget'] in ('many2one'):
          table = admin.entity.table.join(table)
        else:
          table = admin.entity.table
        

    col = getattr(admin.entity, field_name)

    query = select([col], distinct=True, order_by=col.asc()).select_from(table)
      
    def create_decorator(col, value, joins):
      
      def decorator(q):
        if joins:
          q = q.join(joins, aliased=True)
        return q.filter(col==value)
      
      return decorator

    options = [(value[0], create_decorator(col, value[0], joins))
               for value in session.execute(query)]
    return (filter_names[0],[('All', lambda q: q)] + options)
    
class GroupBoxFilter(Filter):
  """Filter where the items are displayed in a QGroupBox"""
  
  def render(self, parent, name, options):
    
    from PyQt4 import QtCore, QtGui
    
    class FilterWidget(QtGui.QGroupBox):
      """A box containing a filter that can be applied on a table view, this filter is
      based on the distinct values in a certain column"""
    
      def __init__(self, name, choices, parent):
        QtGui.QGroupBox.__init__(self, name, parent)
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
          button = QtGui.QRadioButton(name)
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
              
#      def apply_filter(self, query):
#        '''Apply this FilterBox's filter on a query, if All is selected, no
#        filter is applied at all.
#        @return the modified query
#        '''
#        selected_value = self.unique_values[self.get_selection()]
#        if selected_value==FilterBox.all:
#          return query
#        if isinstance(self.col.type, Float):
#          delta = 0.1**self.col.type.precision
#          return query.filter(and_(self.col>=selected_value-delta, self.col<=selected_value+delta))
#        return query.filter(self.col==selected_value)
        
    return FilterWidget(name, options, parent)
  
class ComboBoxFilter(Filter):
  """Filter where the items are displayed in a QComboBox"""
  
  def render(self, parent, name, options):
    
    from PyQt4 import QtCore, QtGui
    
    class FilterWidget(QtGui.QGroupBox):
      
      def __init__(self, name, choices, parent):
        super(FilterWidget, self).__init__(name, parent)
        layout = QtGui.QVBoxLayout()
        self.choices = choices
        combobox = QtGui.QComboBox(self)
        for i,(name,decorator) in enumerate(choices):
          combobox.insertItem(i, unicode(name), QtCore.QVariant(decorator))
        layout.addWidget(combobox)
        self.setLayout(layout)
        self.current_index = 0
        self.connect(combobox, QtCore.SIGNAL('currentIndexChanged(int)'), self.emit_filter_changed)
            
      def emit_filter_changed(self, index):
        self.current_index = index
        self.emit(QtCore.SIGNAL('filter_changed'))
        
      def decorate_query(self, query):
        if self.current_index>=0:
          return self.choices[self.current_index][1](query)
        return query
      
    return FilterWidget(name, options, parent)