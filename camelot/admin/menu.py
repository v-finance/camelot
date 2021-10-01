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

from .action import Action
from ..core.qt import QtWidgets


class Menu(object):
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
        :return: a :class:`QtWidgets.QMenu` object
        """
        from ..view.controls.action_widget import ActionAction
        menu = QtWidgets.QMenu(str(self.get_verbose_name()), parent)
        for item in self.get_items():
            if item is None:
                menu.addSeparator()
                continue
            if isinstance(item, Menu):
                menu.addMenu(item.render(gui_context, menu))
            elif isinstance(item, Action):
                action = ActionAction(item, gui_context, menu)
                menu.addAction(action)
            else:
                raise Exception('Cannot handle menu items of type %s'%type(item))
        return menu



