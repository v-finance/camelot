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

from PyQt4 import QtGui, QtCore
from PyQt4.QtCore import Qt

from camelot.admin.action.base import Action, GuiContext, Mode, ModelContext
from camelot.core.utils import ugettext, ugettext_lazy as _
from camelot.view.art import Icon

"""ModelContex, GuiContext and Actions that run in the context of an 
application.
"""

class ApplicationActionModelContext( ModelContext ):
    """The Model context for an :class:`camelot.admin.action.Action`.  On top 
    of the attributes of the :class:`camelot.admin.action.base.ModelContext`, 
    this context contains :
        
    .. attribute:: admin
    
        the application admin.
    """
    
    def __init__( self ):
        super( ApplicationActionModelContext, self ).__init__()
        self.admin = None
        
class ApplicationActionGuiContext( GuiContext ):
    """The GUI context for an :class:`camelot.admin.action.Action`.  On top of 
    the attributes of the :class:`camelot.admin.action.base.GuiContext`, this 
    context contains :
    
    .. attribute:: workspace
    
        the the :class:`camelot.view.workspace.DesktopWorkspace` of the 
        application in which views can be opened or adapted.
        
    .. attribute:: admin
    
        the application admin.
    """
    
    model_context = ApplicationActionModelContext
    
    def __init__( self ):
        super( ApplicationActionGuiContext, self ).__init__()
        self.workspace = None
        self.admin = None
        
    def create_model_context( self ):
        context = super( ApplicationActionGuiContext, self ).create_model_context()
        context.admin = self.admin
        return context
        
    def copy( self ):
        new_context = super( ApplicationActionGuiContext, self ).copy()
        new_context.workspace = self.workspace
        new_context.admin = self.admin
        return new_context
        
class EntityAction( Action ):
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
        
class OpenTableView( EntityAction ):
    """An application action that opens a TableView of an Entity

    :param entity_admin: an instance of 
        :class:`camelot.admin.entity_admin.EntityAdmin` to be used to
        visualize the entities
    
    """

    modes = [ Mode( 'new_tab', _('Open in New Tab') ) ]
        
    def get_state( self, model_context ):
        state = super( OpenTableView, self ).get_state( model_context )
        state.verbose_name = self.verbose_name or self._entity_admin.get_verbose_name_plural()
        return state
        
    def gui_run( self, gui_context ):
        table_view = self._entity_admin.create_table_view()
        if gui_context.mode_name == 'new_tab':
            gui_context.workspace.add_view( table_view )
        else:
            gui_context.workspace.set_view( table_view )
        
class OpenNewView( EntityAction ):
    """An application action that opens a new view of an Entity
    
    :param entity_admin: an instance of 
        :class:`camelot.admin.entity_admin.EntityAdmin` to be used to
        visualize the entities
    
    """

    verbose_name = _('New')
    shortcut = QtGui.QKeySequence.New
    icon = Icon('tango/16x16/actions/document-new.png')
    tooltip = _('New')
            
    def get_state( self, model_context ):
        state = super( OpenNewView, self ).get_state( model_context )
        state.verbose_name = self.verbose_name or ugettext('New %s')%(self._entity_admin.get_verbose_name())
        state.tooltip = ugettext('Create a new %s')%(self._entity_admin.get_verbose_name())
        return state
        
    def gui_run( self, gui_context ):
        """:return: a new view"""
        from camelot.view.workspace import show_top_level
        form = self._entity_admin.create_new_view(parent=None)
        show_top_level( form, gui_context.workspace )
        
class ShowHelp( Action ):
    """Open the help"""
    
    shortcut = QtGui.QKeySequence.HelpContents
    icon = Icon('tango/16x16/apps/help-browser.png')
    tooltip = _('Help content')
    verbose_name = _('Help')
    
    def gui_run( self, gui_context ):
        #
        # Import QtWebKit as late as possible, since it's the largest
        # part of the QT Library (15 meg on Ubuntu linux)
        #
        from PyQt4 import QtWebKit
        self.view = QtWebKit.QWebView( None )
        self.view.load( gui_context.admin.get_application_admin().get_help_url() )
        self.view.setWindowTitle( ugettext('Help Browser') )
        self.view.setWindowIcon( self.icon.getQIcon() )
        self.view.show()
     
class ShowAbout( Action ):
    """Show the about dialog with the content returned by the
    :meth:`ApplicationAdmin.get_about` method
    """
    
    verbose_name = _('&About')
    icon = Icon('tango/16x16/mimetypes/application-certificate.png')
    tooltip = _("Show the application's About box")
    
    def gui_run( self, gui_context ):
        abtmsg = gui_context.admin.get_application_admin().get_about()
        QtGui.QMessageBox.about( gui_context.workspace, 
                                 ugettext('About'), 
                                 unicode( abtmsg ) )
        
class Backup( Action ):
    """Backup the database to disk"""
    
    verbose_name = _('&Backup')
    tooltip = _('Backup the database')
    icon = Icon('tango/16x16/actions/document-save.png')
    
    def gui_run( self, gui_context ):
        gui_context.admin.get_application_admin().backup( gui_context.workspace )

class Restore( Action ):
    """Restore the database to disk"""
    
    verbose_name = _('&Restore')
    tooltip = _('Restore the database from a backup')
    icon = Icon('tango/16x16/devices/drive-harddisk.png')
    
    def gui_run( self, gui_context ):
        gui_context.admin.get_application_admin().restore( gui_context.workspace )
        
class Refresh( Action ):
    """Refresh all views in the application"""
    
    verbose_name = _('Refresh')
    shortcut = QtGui.QKeySequence( Qt.Key_F9 )
    icon = Icon('tango/16x16/actions/view-refresh.png')
    
    def model_run( self, model_context ):
        from elixir import session
        from camelot.core.orm import refresh_session
        from camelot.view.action_steps import Refresh
        refresh_session( session )
        yield Refresh()

class Exit( Action ):
    """Exit the application"""
    
    verbose_name = _('E&xit')
    shortcut = QtGui.QKeySequence.Quit
    icon = Icon('tango/16x16/actions/system-shutdown.png')
    tooltip = _('Exit the application')
    
    def gui_run( self, gui_context ):
        from camelot.view.model_thread import get_model_thread
        model_thread = get_model_thread()
        gui_context.workspace.close_all_views()
        model_thread.stop()
        QtCore.QCoreApplication.exit(0)
        
def structure_to_application_action(structure, application_admin):
    """Convert a python structure to an ApplicationAction

    :param application_admin: the 
        :class:`camelot.admin.application_admin.ApplicationAdmin` to use to
        create other Admin classes.
    """
    if isinstance(structure, (Action,)):
        return structure
    admin = application_admin.get_related_admin( structure )
    return OpenTableView( admin )
