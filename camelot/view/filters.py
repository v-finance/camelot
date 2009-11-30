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

from camelot.view.model_thread import gui_function
from camelot.core.utils import ugettext_lazy as _

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
    
    def __init__(self, attribute, value_to_string=lambda x:unicode(x)):
        """
        @param attribute: the attribute on which to filter, this attribute
        may contain dots to indicate relationships that need to be followed, 
        eg.  'person.groups.name'
        @param value_to_string: function that converts a value of the attribute to
        a string that will be displayed in the filter 
        """
        self.attribute = attribute
        self._value_to_string = value_to_string
    
    @gui_function     
    def render(self, parent, name, options):
        """Render this filter as a qt object
        @param parent: its parent widget
        @param name: the name of the filter
        @param options: the options that can be selected, where each option is a list
        of tuples containting (option_name, query_decorator)  
        
        The name and the list of options can be fetched with get_name_and_options"""
        raise NotImplementedError()
        
    def get_name_and_options(self, admin):
        """return a tuple of the name of the filter and a list of options that can be selected. 
        Each option is a tuple of the name of the option, and a filter function to
        decorate a query
        @return:  (filter_name, [(option_name, query_decorator), ...)
        """
        from sqlalchemy.sql import select
        from sqlalchemy import orm
        from elixir import session
        filter_names = []
        joins = []
        table = admin.entity.table
        path = self.attribute.split('.')
        for field_name in path:
            attributes = admin.get_field_attributes(field_name)
            filter_names.append(attributes['name'])
            # @todo: if the filter is not on an attribute of the relation, but on the relation itselves
            if 'target' in attributes:
                admin = attributes['admin']
                joins.append(field_name)
                if attributes['direction'] == orm.interfaces.MANYTOONE:
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
      
        options = [(self._value_to_string(value[0]), create_decorator(col, value[0], joins))
                   for value in session.execute(query)]
    
        return (filter_names[0],[(_('all'), lambda q: q)] + options)
        
class GroupBoxFilter(Filter):
    """Filter where the items are displayed in a QGroupBox"""
    
    @gui_function
    def render(self, parent, name, options):
      
        from PyQt4 import QtCore, QtGui
        from camelot.view.controls.filterlist import filter_changed_signal
        
        class FilterWidget(QtGui.QGroupBox):
            """A box containing a filter that can be applied on a table view, this filter is
            based on the distinct values in a certain column"""
          
            def __init__(self, name, choices, parent):
                QtGui.QGroupBox.__init__(self, unicode(name), parent)
                self.group = QtGui.QButtonGroup(self)
                self.item = name
                self.unique_values = []
                self.choices = None
                self.setChoices(choices)
                 
            def emit_filter_changed(self, state):
                self.emit(filter_changed_signal)
            
            def setChoices(self, choices):
                self.choices = choices
                layout = QtGui.QVBoxLayout()
                for i,name in enumerate([unicode(c[0]) for c in choices]):
                    button = QtGui.QRadioButton(name, self)
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
                
        return FilterWidget(name, options, parent)
      
class ComboBoxFilter(Filter):
    """Filter where the items are displayed in a QComboBox"""
    
    @gui_function
    def render(self, parent, name, options):
      
        from PyQt4 import QtCore, QtGui
        from camelot.view.controls.filterlist import filter_changed_signal
        
        class FilterWidget(QtGui.QGroupBox):
          
            def __init__(self, name, choices, parent):
                QtGui.QGroupBox.__init__(self, name, parent)
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
                self.emit(filter_changed_signal)
                
            def decorate_query(self, query):
                if self.current_index>=0:
                    return self.choices[self.current_index][1](query)
                return query
              
        return FilterWidget(name, options, parent)
    
class ValidDateFilter(Filter):
    """Filters entities that are valid a certain date.  This filter will present
    a date to the user and filter the entities that have their from date before this
    date and their end date after this date.  If no date is given, all entities will
    be shown"""

    def __init__(self, from_attribute, thru_attribute, verbose_name):
        """
        :param from_attribute: the name of the attribute representing the from date
        :param thru_attribute: the name of the attribute representing the thru date
        :param verbose_name: the displayed name of the filter"""
        self._from_attribute = from_attribute
        self._thru_attribute = thru_attribute
        self._verbose_name = verbose_name
        
    def render(self, parent, name, options):
        
        from datetime import date
        from PyQt4 import QtGui, QtCore
        from camelot.view.controls.filterlist import filter_changed_signal
        from camelot.view.controls.editors import DateEditor, editingFinished
        
        class FilterWidget(QtGui.QGroupBox):
          
            def __init__(self, name, query_decorator, parent):
                QtGui.QGroupBox.__init__(self, name, parent)
                layout = QtGui.QVBoxLayout()
                self.date_editor = DateEditor(parent=self, nullable=True)
                self.date_editor.set_value(date.today())
                self.query_decorator = query_decorator
                layout.addWidget(self.date_editor)
                self.setLayout(layout)
                self.connect(self.date_editor, editingFinished, self.emit_filter_changed)
                    
            def emit_filter_changed(self):
                self.emit(filter_changed_signal)
                
            def decorate_query(self, query):
                return self.query_decorator(query, self.date_editor.get_value())
              
        return FilterWidget(name, options, parent)
        
    def get_name_and_options(self, admin):
        from sqlalchemy.sql import and_
        
        def query_decorator(query, date):
            e = admin.entity
            if date:
                print 'filter on', date
                return query.filter(and_(getattr(e, self._from_attribute)<=date,
                                         getattr(e, self._thru_attribute)>=date))
            return query
        
        return (self._verbose_name, query_decorator)