#  ============================================================================
#
#  Copyright (C) 2007-2011 Conceptive Engineering bvba. All rights reserved.
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
This is part of a test implementation of the new actions draft, it is not
intended for production use
"""

from ApplicationAction import ApplicationAction, ApplicationActionGuiContext

class ListActionGuiContext( ApplicationActionGuiContext ):
    
    def __init__( self ):
        """The context for an :class:`ListAction`.  On top of the attributes of the 
        :class:`camelot.admin.action.application_action.ApplicationActionGuiContext`, 
        this context contains :
    
        .. attribute:: selection_model
        
           the :class:`QtGui.QItemSelectionModel` class that relates to the table 
           view on which the widget will be placed.
           
        """
        super( ListActionGuiContext, self ).__init__()
        self.selection_model = None

    def copy( self ):
        new_context = super( ListActionGuiContext, self ).copy()
        new_context.selection_model = self.selection_model
        return new_context
    
class ListAction( ApplicationAction ):

    def render( self, gui_context, parent ):
        """
        :param gui_context: the context available in the *GUI thread*
            of type :class:`ListActionGuiContext`
        :param parent: the parent :class:`QtGui.QWidget`
        :return: a :class:`QtGui.QWidget` which when triggered
            will execute the run method.
        """
        from camelot.view.contols.action_widget import ActionPushButton
        return ActionPushButton( self, gui_context, parent )
        
    def gui_run( self, gui_context ):
        """This method is called inside the GUI thread, by default it
        pops up a progress dialog and executes the :meth:`model_run` in 
        the Model thread, while updating the progress dialog.

        :param gui_context: the context available in the *GUI thread*
          of type :class:`ListActionGuiContext`
        """
        super( ApplicationAction, self ).__init__( gui_context )
