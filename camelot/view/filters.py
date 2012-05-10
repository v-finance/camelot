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

"""
Python structures to represent filters.
These structures can be transformed to QT forms.
"""

import collections
import datetime

from PyQt4 import QtCore, QtGui
from sqlalchemy import sql

from camelot.view.controls.editors import DateEditor
from camelot.core.utils import ugettext_lazy as _

#
# data structures to feed the filter widgets
# 
filter_data = collections.namedtuple( 'filter_data',
                                      ['name', 'options', 'default'] )

filter_option = collections.namedtuple( 'filter_option',
                                        ['name', 'value', 'decorator'] )

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
    
    class All(object):
        pass
    
    def __init__(self, attribute, default=All):
        """
        :param attribute: the attribute on which to filter, this attribute
            may contain dots to indicate relationships that need to be followed, 
            eg.  'person.name'
        :param default: the default value to filter on when the view opens,
            defaults to showing all records.
        """
        self.attribute = attribute
        self.default = default
        
    def render(self, parent, name, options):
        """Render this filter as a qt object
        @param parent: its parent widget
        @param name: the name of the filter
        @param options: the options that can be selected, where each option is a list
        of tuples containting (option_name, query_decorator)  
        
        The name and the list of options can be fetched with get_name_and_options"""
        raise NotImplementedError()
        
    def get_filter_data(self, admin):
        """
        :return:  a :class:`filter_data` object
        """
        from sqlalchemy.sql import select
        from camelot.core.orm import Session
        session = Session()
        filter_names = []
        joins = []
        #
        # in case of inheritance, use the local table to be able to join,
        # otherwise use the mapped table, to be able to filter on views
        #
        if admin.mapper!=admin.mapper.base_mapper:
            table = admin.mapper.local_table
        else:
            table = admin.mapper.mapped_table
        path = self.attribute.split('.')
        for field_name in path:
            attributes = admin.get_field_attributes(field_name)
            filter_names.append(attributes['name'])
            # @todo: if the filter is not on an attribute of the relation, but on the relation itselves
            if 'target' in attributes:
                admin = attributes['admin']
                joins.append(field_name)
                if attributes['direction'] == 'manytoone':
                    table = admin.entity.table.join( table )
                else:
                    table = admin.entity.table

        col = getattr( admin.entity, field_name )
        query = select([col], distinct=True, order_by=col.asc()).select_from(table)
          
        def create_decorator(col, attributes, value, joins):
            def decorator(q):
                if joins:
                    q = q.join( *joins, aliased=True)
                if 'precision' in attributes:
                    delta = pow( 10,  -1*attributes['precision'])
                    return q.filter( sql.and_(col < value+delta, col > value-delta) )
                return q.filter(col==value)
              
            return decorator

        options = [ filter_option( name = _('All'),
                                   value = Filter.All,
                                   decorator = lambda q:q ) ]
        
        for value in session.execute(query):
            if 'to_string' in attributes:
                option_name = attributes['to_string'](value[0])
            else:
                option_name = value[0]
            if attributes.get( 'translate_content', False ):
                option_name = _( option_name )
        
            options.append( filter_option( name = option_name,
                                           value = value[0],
                                           decorator = create_decorator(col, attributes, value[0], joins) ) )
        
        return filter_data( name = filter_names[0],
                            options = options,
                            default = self.default )

class FilterWidget( QtGui.QGroupBox ):
    """A box containing a filter that can be applied on a table view, this filter is
    based on the distinct values in a certain column"""
  
    filter_changed_signal = QtCore.pyqtSignal()
    
    def __init__(self, filter_data, parent):
        super( FilterWidget, self ).__init__( unicode( filter_data.name ), parent )
        layout = QtGui.QHBoxLayout()
        layout.setSpacing( 2 )
        self.setLayout( layout )
        self.group = QtGui.QButtonGroup(self)
        self.set_filter_data( filter_data )
         
    @QtCore.pyqtSlot(bool)
    def emit_filter_changed( self, state) :
        self.filter_changed_signal.emit()
    
    def set_filter_data( self, filter_data ):
        self.filter_data = filter_data
        layout = self.layout()
        button_layout = QtGui.QVBoxLayout()
        
        for i, choice in enumerate( filter_data.options ):
            button = QtGui.QRadioButton( unicode( choice.name ), self)
            button_layout.addWidget( button )
            self.group.addButton(button, i)
            if choice.value == filter_data.default:
                button.setChecked(True)
            button.toggled.connect( self.emit_filter_changed )
            
        layout.addLayout( button_layout )
        self.setLayout(layout)
    
    def decorate_query( self, query ):
        checked = self.group.checkedId()
        if checked>=0:
            return self.filter_data.options[checked].decorator( query )
        return query
                    
class GroupBoxFilter(Filter):
    """Filter where the items are displayed in a QGroupBox"""
    
    def render( self, filter_data, parent ):
        return FilterWidget( filter_data, parent )
      
class GroupBoxFilterWidget( QtGui.QGroupBox ):
    """Flter widget based on a QGroupBox"""
  
    filter_changed_signal = QtCore.pyqtSignal()
    
    def __init__(self, filter_data, parent):
        super( GroupBoxFilterWidget, self ).__init__( unicode( filter_data.name ), parent )
        layout = QtGui.QVBoxLayout()
        layout.setSpacing( 2 )
        self.filter_data = filter_data
        combobox = QtGui.QComboBox(self)
        self.current_index = 0
        for i, choice in enumerate( filter_data.options ):
            if choice.value == filter_data.default:
                self.current_index = i
            combobox.insertItem(i, unicode( choice.name ) )
        combobox.setCurrentIndex( self.current_index )
        layout.addWidget( combobox )
        self.setLayout(layout)
        combobox.currentIndexChanged.connect( self.emit_filter_changed )
            
    @QtCore.pyqtSlot(int)
    def emit_filter_changed(self, index):
        self.current_index = index
        self.filter_changed_signal.emit()
        
    def decorate_query(self, query):
        if self.current_index>=0:
            return self.filter_data.options[self.current_index].decorator( query )
        return query

class ComboBoxFilter(Filter):
    """Filter where the items are displayed in a QComboBox"""
    
    def render(self, filter_data, parent):
        return GroupBoxFilterWidget(filter_data, parent)
    
class EditorFilter(Filter):
    """Filter that presents the user with an editor, allowing the user to enter
    a value on which to filter, and at the same time to show 'All' or 'None'
    
    :param field_name: the name fo the field on the class on which to filter
    :param default_operator: a default operator to be used, on of the attributes
        of the python module :mod:`operator`, such as `operator.eq`
    :param default_value_1: a default value for the first editor (in case the
        default operator in unary or binary
    :param default_value_2: a default value for the second editor (in case the
        default operator is binary)
    """
    
    def __init__( self, 
                  field_name, 
                  verbose_name = None,
                  default_operator = None,
                  default_value_1 = None,
                  default_value_2 = None ):
        super(EditorFilter, self).__init__(field_name)
        self._field_name = field_name
        self._verbose_name = verbose_name
        self._default_operator = default_operator
        self._default_value_1 = default_value_1
        self._default_value_2 = default_value_2
        
    def render(self, filter_data, parent):
        from camelot.view.controls.filter_operator import FilterOperator
        _name, (entity, field_name, field_attributes) = filter_data
        return FilterOperator( entity, 
                               field_name, 
                               field_attributes, 
                               self._default_operator,
                               self._default_value_1,
                               self._default_value_2,
                               parent )
    
    def get_filter_data(self, admin):
        field_attributes = admin.get_field_attributes(self._field_name)
        name = self._verbose_name or field_attributes['name']
        return name, (admin.entity, self._field_name, field_attributes)
        
class DateFilterWidget( QtGui.QGroupBox ):
    """Filter widget based on a DateEditor"""
  
    filter_changed_signal = QtCore.pyqtSignal()
    
    def __init__( self, filter_data, parent ):
        super( DateFilterWidget, self ).__init__( unicode( filter_data.name ), parent )
        layout = QtGui.QVBoxLayout()
        layout.setSpacing( 2 )
        self.date_editor = DateEditor(parent=self, nullable=True)
        self.date_editor.set_value( filter_data.default )
        for option in filter_data.options:
            self.query_decorator = option.decorator
        layout.addWidget( self.date_editor )
        self.setLayout( layout )
        self.date_editor.editingFinished.connect( self.emit_filter_changed )
            
    @QtCore.pyqtSlot()
    def emit_filter_changed(self):
        self.filter_changed_signal.emit()
        
    def decorate_query(self, query):
        return self.query_decorator(query, self.date_editor.get_value())
            
class ValidDateFilter(Filter):
    """Filters entities that are valid a certain date.  This filter will present
    a date to the user and filter the entities that have their from date before this
    date and their end date after this date.  If no date is given, all entities will
    be shown"""

    def __init__(self, 
                 from_attribute='from_date', 
                 thru_attribute='thru_date', 
                 verbose_name=_('Valid at'),
                 default = datetime.date.today ):
        """
        :param from_attribute: the name of the attribute representing the from date
        :param thru_attribute: the name of the attribute representing the thru date
        :param verbose_name: the displayed name of the filter
        :param default: a function returning a default date for the filter
        """
        super(ValidDateFilter, self).__init__(None, default=default)
        self._from_attribute = from_attribute
        self._thru_attribute = thru_attribute
        self._verbose_name = verbose_name
        
    def render( self, filter_data, parent ):
        return DateFilterWidget(filter_data, parent)
        
    def get_filter_data(self, admin):
        from sqlalchemy.sql import and_
        
        def query_decorator(query, date):
            e = admin.entity
            if date:
                return query.filter(and_(getattr(e, self._from_attribute)<=date,
                                         getattr(e, self._thru_attribute)>=date))
            return query
        
        option = filter_option( name = None,
                                value = None,
                                decorator = query_decorator )
        
        return filter_data( name = self._verbose_name,
                            options = [ option ],
                            default = self.default() )

