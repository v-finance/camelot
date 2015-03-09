#  ============================================================================
#
#  Copyright (C) 2007-2013 Conceptive Engineering bvba. All rights reserved.
#  www.conceptive.be / info@conceptive.be
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
#  visit www.python-camelot.com or contact info@conceptive.be
#
#  This file is provided AS IS with NO WARRANTY OF ANY KIND, INCLUDING THE
#  WARRANTY OF DESIGN, MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE.
#
#  For use of this library in commercial applications, please contact
#  info@conceptive.be
#
#  ============================================================================

"""
A :class:`Table` and a :class:`ColumnGroup` class to define table views that
are more complex.

"""

import six

class ColumnGroup( object ):
    """
    A group of columns to be displayed in a table view.  By building a Table
    with multiple column groups, lots of data can be displayed in a limited
    space.
    
        :param verbose_name: the text to be displayed in the tab widget of the
            column group
        :param columns: a list of fields to display within this column group
        :param icon: a :class:`camelot.view.art.Icon` object
        
    .. literalinclude:: ../../test/test_view.py
       :start-after: begin column group
       :end-before: end column group
       
    .. image:: /_static/controls/column_group.png

    """
    
    def __init__( self, 
                  verbose_name,
                  columns,
                  icon = None ):
        self.verbose_name = verbose_name
        self.icon = icon
        self.columns = columns
        
    def get_fields( self ):
        """
        :return: an ordered list of field names displayed in the column group
        """
        return self.columns
        
class Table( object ):
    """
    Represents the columns that should be displayed in a table view.
    
        :param columns: a list of strings with the fields to be displayed, or a 
            list of :class:`ColumnGroup` objects
    """
    
    def __init__( self,
                  columns ):
        self.columns = columns
        
    def get_fields( self, column_group = None ):
        """
        :param column_group: if given, only return the fields in this column group,
            where column_group is the index of the group
        :return: a ordered list of field names displayed in the table
        """
        fields = []
        for i, column in enumerate(self.columns):
            if isinstance( column, six.string_types ):
                fields.append( column )
            else:
                if (column_group is None) or (column_group==i):
                    fields.extend( column.get_fields() )
        return fields

    def render( self, item_view, parent = None ):
        """
        Create a tab widget that allows the user to switch between column 
        groups.
        
            :param item_view: a :class:`QtWidgets.QAbstractItemView` object.
            :param parent: a :class:`QtWidgets.QWidget` object
        """
        pass

def structure_to_table( structure ):
    """Convert a python data structure to a table, using the following rules :

   * if structure is an instance of Table, return structure
   * if structure is a list, create a Table from this list
    """
    if isinstance( structure, Table ):
        return structure
    return Table( structure )

