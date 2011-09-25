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

from camelot.admin.action import Action, GuiContext, Mode
from camelot.core.utils import ugettext, ugettext_lazy as _

class ApplicationActionGuiContext( GuiContext ):
    """The context for an :class:`ApplicationAction`.  On top of the attributes
    of the :class:`camelot.admin.action.GuiContext`, this context contains :
    
    .. attribute:: workspace
        the workspace of the application in which views can be opened or
        adapted.
        
    .. attribute:: admin
        the application admin.
    """
    
    def __init__( self ):
        super( ApplicationActionGuiContext, self ).__init__()
        self.workspace = None
        self.admin = None
        
class ApplicationAction( Action ):
    """A subclass of :class:`camelot.admin.action.Action` that runs in the 
    context of the application. Typical places to use this action are :
    
    * within the :meth:`camelot.admin.ApplicationAdmin.get_sections` method,
      as elements of a section (:class:`camelot.admin.section.Section`)
      
    * within the :meth:`camelot.admin.ApplicationAdmin.get_actions` method,
      for the actions that are displayed on the home screen.
      
    To make an action do something usefull, its :meth:`gui_run` or 
    :meth:`model_run` should be reimplemented in a subclass.
    """

    def render( self, workspace, parent ):
        """
        :param workspace: the :class:`camelot.view.workspace.DesktopWorkspace`
            that is active.
        :param parent: the parent :class:`QtGui.QWidget`
        :return: a :class:`QtGui.QWidget` which when triggered
            will execute the gui_run method. of the action.
        """
        from camelot.view.workspace import ActionButton
        return ActionButton( self, workspace, parent )
        
    def gui_run( self, gui_context ):
        """This method is called inside the GUI thread, by default it
        pops up a progress dialog and executes the :meth:`model_run` in 
        the Model thread, while updating the progress dialog.

        :param gui_context: the context available in ghe *GUI thread*
          of type :class:`ApplicationActionGuiContext`
        """
        from camelot.view.controls.progress_dialog import ProgressDialog
        progress_dialog = ProgressDialog( unicode( self.verbose_name ) )
        gui_context.progress_dialog = progress_dialog
        progress_dialog.show()
        super(ApplicationAction, self).gui_run( gui_context )
        progress_dialog.close()

class EntityAction( ApplicationAction ):
    """Generic ApplicationAction that acts upon an Entity class"""

    def __init__( self, 
                  entity_admin ):
        """
        :param entity_admin: an instance of 
            :class:`camelot.admin.entity_admin.EntityAdmin` to be used to
            visualize the entities
        """
        from camelot.admin.entity_admin import EntityAdmin
        assert isinstance( entity_admin, (EntityAdmin,) )
        self._entity_admin = entity_admin
        
class TableViewAction( EntityAction ):
    """An application action that opens a TableView of an Entity"""

    modes = [ Mode( 'new_tab', _('Open in New Tab') ) ]
    
    @property
    def verbose_name( self ):
        return super( TableViewAction, self ).verbose_name or self._entity_admin.get_verbose_name_plural()
    
    def gui_run( self, gui_context ):
        table_view = self._entity_admin.create_table_view()
        if gui_context.mode_name == 'new_tab':
            gui_context.workspace.add_view( table_view )
        else:
            gui_context.workspace.set_view( table_view )
        
class NewViewAction( EntityAction ):
    """An application action that opens a new view of an Entity"""

    @property
    def verbose_name( self ):
        return super( NewViewAction, self ).verbose_name or ugettext('New %s')%(self._entity_admin.get_verbose_name())
    
    @property
    def tooltip(self):
        return ugettext('Create a new %s')%(self._entity_admin.get_verbose_name())
        
    def gui_run( self, gui_context ):
        """:return: a new view"""
        from camelot.view.workspace import show_top_level
        form = self._entity_admin.create_new_view(parent=None)
        show_top_level( form, gui_context.workspace )
        
def structure_to_application_action(structure, application_admin):
    """Convert a python structure to an ApplicationAction

    :param application_admin: the 
        :class:`camelot.admin.application_admin.ApplicationAdmin` to use to
        create other Admin classes.
    """
    if isinstance(structure, (ApplicationAction,)):
        return structure
    admin = application_admin.get_related_admin( structure )
    return TableViewAction( admin )
