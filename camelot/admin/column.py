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

class ColumnGroup( object ):
    """A group of columns to be displayed in a table view
    :param verbose_name: the text to be displayed in the tab widget of the
        column group
    :param columns: a list of fields to display within this column group
    :param icon: a :class:`camelot.view.art.Icon` object
    """
    
    def __init__( self, 
                  verbose_name,
                  columns,
                  icon = None ):
        self.verbose_name = verbose_name
        self.icon = icon
        self.columns = columns
        
class ColumnGroups( object ):
    """A list of column groups
    :param groups: a list of column groups
    """
    
    def __init__( self,
                  groups ):
        self.groups = groups
        
    def render( self, item_view, parent = None ):
        """
        Create a tab widget that allows the user to switch between column 
        groups.
        :param item_view: a :class:`QtGui.QAbstractItemView` object.
        :param parent: a :class:`QtGui.QWidget` object
        """
        pass

