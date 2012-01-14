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

from PyQt4 import QtGui

class Menu( object ):
    """A menu is a part of the main menu shown on the main window.  Each Menu
contains a list of items the user select.  Such a menu item is either a Menu
itself, an Action object or None to insert a separator.
    """
        
    def __init__( self, 
                  verbose_name,
                  items,
                  icon=None ):
        self.verbose_name = verbose_name
        self.icon = icon
        self.items = items

    def get_verbose_name( self ):
        return self.verbose_name

    def get_icon( self ):
        return self.icon

    def get_items( self ):
        return self.items
    
    def render( self, gui_context, parent ):
        """
        :return: a :class:`QtGui.QMenu` object
        """
        menu = QtGui.QMenu( unicode( self.get_verbose_name() ), parent )
        for item in self.get_items():
            if item == None:
                menu.addSeparator()
                continue
            rendered_item = item.render( gui_context, menu )
            if isinstance( rendered_item, QtGui.QMenu ):
                menu.addMenu( rendered_item )
            elif isinstance( rendered_item, QtGui.QAction ):
                menu.addAction( rendered_item )
            else:
                raise Exception( 'Cannot handle menu items of type %s'%type( rendered_item ) )
        return menu

