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

import logging

from PyQt4 import QtGui, QtCore
from PyQt4.QtCore import Qt

from camelot.admin.action.base import Action, GuiContext, Mode, ModelContext
from camelot.core.orm import Session
from camelot.core.utils import ugettext, ugettext_lazy as _
from camelot.core.backup import BackupMechanism
from camelot.view.art import Icon

"""ModelContext, GuiContext and Actions that run in the context of an 
application.
"""

LOGGER = logging.getLogger( 'camelot.admin.action.application_action' )

class ApplicationActionModelContext( ModelContext ):
    """The Model context for an :class:`camelot.admin.action.Action`.  On top 
    of the attributes of the :class:`camelot.admin.action.base.ModelContext`, 
    this context contains :
        
    .. attribute:: admin
   
        the application admin.

    .. attribute:: session

        the active session
    """
    
    def __init__( self ):
        super( ApplicationActionModelContext, self ).__init__()
        self.admin = None

    # Cannot set session in constructor because constructor is called
    # inside the GUI thread
    @property
    def session( self ):
        return Session()
        
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
        
    def copy( self, base_class=None ):
        new_context = super( ApplicationActionGuiContext, self ).copy( base_class )
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
        table_view = self._entity_admin.create_table_view( gui_context )
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
    """
Backup the database to disk

.. attribute:: backup_mechanism

    A subclass of :class:`camelot.core.backup.BackupMechanism` that enables 
    the application to perform backups an restores.    
    """
    
    verbose_name = _('&Backup')
    tooltip = _('Backup the database')
    icon = Icon('tango/16x16/actions/document-save.png')
    backup_mechanism = BackupMechanism

    def model_run( self, model_context ):
        from camelot.view.action_steps import UpdateProgress, SelectBackup
        label, storage = yield SelectBackup( self.backup_mechanism )
        yield UpdateProgress( text = _('Backup in progress') )
        backup_mechanism = self.backup_mechanism( label, 
                                                  storage )
        for completed, total, description in backup_mechanism.backup():
            yield UpdateProgress( completed,
                                  total,
                                  text = description )

class Restore( Action ):
    """
Restore the database to disk

.. attribute:: backup_mechanism

    A subclass of :class:`camelot.core.backup.BackupMechanism` that enables 
    the application to perform backups an restores.
"""
    
    verbose_name = _('&Restore')
    tooltip = _('Restore the database from a backup')
    icon = Icon('tango/16x16/devices/drive-harddisk.png')
    backup_mechanism = BackupMechanism
            
    def model_run( self, model_context ):
        from camelot.view.action_steps import UpdateProgress, SelectRestore
        label, storage = yield SelectRestore( self.backup_mechanism )
        yield UpdateProgress( text = _('Restore in progress') )
        backup_mechanism = self.backup_mechanism( label,
                                                  storage )
        for completed, total, description in backup_mechanism.restore():
            yield UpdateProgress( completed,
                                  total,
                                  text = description )

class Refresh( Action ):
    """Reload all objects from the database and update all views in the
    application."""
    
    verbose_name = _('Refresh')
    shortcut = QtGui.QKeySequence( Qt.Key_F9 )
    icon = Icon('tango/16x16/actions/view-refresh.png')
    
    def model_run( self, model_context ):
        import sqlalchemy.exc as sa_exc
        from camelot.core.orm import Session
        from camelot.view import action_steps
        from camelot.view.remote_signals import get_signal_handler
        LOGGER.debug('session refresh requested')
        progress_db_message = ugettext('Reload data from database')
        progress_view_message = ugettext('Update screens')
        session = Session()
        signal_handler = get_signal_handler()
        refreshed_objects = []
        expunged_objects = []
        #
        # Loop over the objects one by one to be able to detect the deleted
        # objects
        #
        session_items = len( session.identity_map )
        for i, (_key, obj) in enumerate( session.identity_map.items() ):
            try:
                session.refresh( obj )
                refreshed_objects.append( obj )
            except sa_exc.InvalidRequestError:
                #
                # this object could not be refreshed, it was probably deleted
                # outside the scope of this session, so assume it is deleted
                # from the application its point of view
                #
                session.expunge( obj )
                expunged_objects.append( obj )
            if i%10 == 0:
                yield action_steps.UpdateProgress( i, 
                                                   session_items, 
                                                   progress_db_message )
        yield action_steps.UpdateProgress( text = progress_view_message )
        for obj in refreshed_objects:
            signal_handler.sendEntityUpdate( None, obj )
        for obj in expunged_objects:
            signal_handler.sendEntityDelete( None, obj )
        yield action_steps.Refresh()

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
        
class ChangeLogging( Action ):
    """Allow the user to change the logging configuration"""
    
    verbose_name = _('Change logging')
    icon = Icon('tango/16x16/emblems/emblem-photos.png')
    tooltip = _('Change the logging configuration of the application')
    
    def model_run( self, model_context ):
        from camelot.view.controls import delegates
        from camelot.view import action_steps
        from camelot.admin.object_admin import ObjectAdmin
        
        class Options( object ):
            
            def __init__( self ):
                self.level = logging.INFO
                
            class Admin( ObjectAdmin ):
                list_display = ['level']
                field_attributes = { 'level':{ 'delegate':delegates.ComboBoxDelegate,
                                               'editable':True,
                                               'choices':[(l,logging.getLevelName(l)) for l in [logging.DEBUG, 
                                                                                                logging.INFO, 
                                                                                                logging.WARNING,
                                                                                                logging.ERROR,
                                                                                                logging.CRITICAL]]} }
                
        options = Options()
        yield action_steps.ChangeObject( options )
        logging.getLogger().setLevel( options.level )
    
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

