#  ============================================================================
#
#  Copyright (C) 2007-2016 Conceptive Engineering bvba.
#  www.conceptive.be / info@conceptive.be
#
#  Redistribution and use in source and binary forms, with or without
#  modification, are permitted provided that the following conditions are met:
#      * Redistributions of source code must retain the above copyright
#        notice, this list of conditions and the following disclaimer.
#      * Redistributions in binary form must reproduce the above copyright
#        notice, this list of conditions and the following disclaimer in the
#        documentation and/or other materials provided with the distribution.
#      * Neither the name of Conceptive Engineering nor the
#        names of its contributors may be used to endorse or promote products
#        derived from this software without specific prior written permission.
#  
#  THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
#  ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
#  WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
#  DISCLAIMED. IN NO EVENT SHALL <COPYRIGHT HOLDER> BE LIABLE FOR ANY
#  DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
#  (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
#  LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
#  ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
#  (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
#  SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
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


