#  ============================================================================
#
#  Copyright (C) 2007-2010 Conceptive Engineering bvba. All rights reserved.
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

import datetime

from PyQt4 import QtCore, QtGui
from camelot.view.controls.filterlist import filter_changed_signal
from camelot.view.controls.editors import DateEditor, editingFinished
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
    
    def __init__(self, attribute, value_to_string=unicode):
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
         
    @QtCore.pyqtSlot(bool)
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
            button.toggled.connect( self.emit_filter_changed )
        layout.addStretch()
        self.setLayout(layout)
    
    def decorate_query(self, query):
        checked = self.group.checkedId()
        if checked>=0:
            return self.choices[checked][1](query)
        return query
                    
class GroupBoxFilter(Filter):
    """Filter where the items are displayed in a QGroupBox"""
    
    @gui_function
    def render(self, parent, name, options):
        return FilterWidget(name, options, parent)
      
class GroupBoxFilterWidget(QtGui.QGroupBox):
    """Flter widget based on a QGroupBox"""
  
    def __init__(self, name, choices, parent):
        QtGui.QGroupBox.__init__(self, unicode(name), parent)
        layout = QtGui.QVBoxLayout()
        self.choices = choices
        combobox = QtGui.QComboBox(self)
        for i,(name,decorator) in enumerate(choices):
            combobox.insertItem(i, unicode(name), QtCore.QVariant(decorator))
        layout.addWidget(combobox)
        self.setLayout(layout)
        self.current_index = 0
        combobox.currentIndexChanged.connect( self.emit_filter_changed )
            
    @QtCore.pyqtSlot(int)
    def emit_filter_changed(self, index):
        self.current_index = index
        self.emit(filter_changed_signal)
        
    def decorate_query(self, query):
        if self.current_index>=0:
            return self.choices[self.current_index][1](query)
        return query

class ComboBoxFilter(Filter):
    """Filter where the items are displayed in a QComboBox"""
    
    @gui_function
    def render(self, parent, name, options):
        return GroupBoxFilterWidget(name, options, parent)
    
class EditorFilter(Filter):
    """Filter that presents the user with an editor, allowing the user to enter
    a value on which to filter, and at the same time to show 'All' or 'None'
    """
    
    def __init__(self, field_name, verbose_name=None):
        """:param field: the name of the field on which to filter"""
        super(EditorFilter, self).__init__(field_name)
        self._field_name = field_name
        self._verbose_name = verbose_name
        
    def render(self, parent, name, options):
        from camelot.view.controls.filter_operator import FilterOperator
        entity, field_name, field_attributes = options
        return FilterOperator(entity, field_name, field_attributes, parent)
    
    def get_name_and_options(self, admin):
        field_attributes = admin.get_field_attributes(self._field_name)
        name = self._verbose_name or field_attributes['name']
        return name, (admin.entity, self._field_name, field_attributes)
        
class DateFilterWidget(QtGui.QGroupBox):
    """Filter widget based on a DateEditor"""
  
    def __init__(self, name, query_decorator, parent):
        QtGui.QGroupBox.__init__(self, unicode(name), parent)
        layout = QtGui.QVBoxLayout()
        self.date_editor = DateEditor(parent=self, nullable=True)
        self.date_editor.set_value(datetime.date.today())
        self.query_decorator = query_decorator
        layout.addWidget(self.date_editor)
        self.setLayout(layout)
        self.connect(self.date_editor, editingFinished, self.emit_filter_changed)
            
    def emit_filter_changed(self):
        self.emit(filter_changed_signal)
        
    def decorate_query(self, query):
        return self.query_decorator(query, self.date_editor.get_value())
            
class ValidDateFilter(Filter):
    """Filters entities that are valid a certain date.  This filter will present
    a date to the user and filter the entities that have their from date before this
    date and their end date after this date.  If no date is given, all entities will
    be shown"""

    def __init__(self, from_attribute='from_date', 
                 thru_attribute='thru_date', 
                 verbose_name=_('Valid at')):
        """
        :param from_attribute: the name of the attribute representing the from date
        :param thru_attribute: the name of the attribute representing the thru date
        :param verbose_name: the displayed name of the filter"""
        super(ValidDateFilter, self).__init__(None, None)
        self._from_attribute = from_attribute
        self._thru_attribute = thru_attribute
        self._verbose_name = verbose_name
        
    def render(self, parent, name, options):
        return DateFilterWidget(name, options, parent)
        
    def get_name_and_options(self, admin):
        from sqlalchemy.sql import and_
        
        def query_decorator(query, date):
            e = admin.entity
            if date:
                return query.filter(and_(getattr(e, self._from_attribute)<=date,
                                         getattr(e, self._thru_attribute)>=date))
            return query
        
        return (self._verbose_name, query_decorator)