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

import logging
import time

import six

from ...core.qt import Qt, QtCore, QtWidgets, QtGui, QtQuick, is_deleted
from ...core.sql import metadata
from camelot.admin.action.base import Action, GuiContext, Mode, ModelContext
from camelot.core.exception import CancelRequest
from camelot.core.orm import Session
from camelot.core.utils import ugettext, ugettext_lazy as _
from camelot.core.backup import BackupMechanism
from camelot.view.art import FontIcon

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
    
        the :class:`camelot.view.workspace.DesktopWorkspace` of the 
        application in which views can be opened or adapted.
        
    .. attribute:: admin
    
        the application admin.
    """
    
    model_context = ApplicationActionModelContext
    
    def __init__( self ):
        super( ApplicationActionGuiContext, self ).__init__()
        self.workspace = None
        self.admin = None
    
    def get_progress_dialog(self):
        if self.workspace is not None and not is_deleted(self.workspace):
            view = self.workspace.active_view()
            if view is not None:
                if view.objectName() == 'dashboard':
                    quick_view = view.quick_view
                    if not is_deleted(quick_view):
                        # try to return the C++ QML progress dialog
                        qml_progress_dialog = quick_view.findChild(QtCore.QObject, 'qml_progress_dialog')
                        if qml_progress_dialog is not None:
                            return qml_progress_dialog


        # return the regular progress dialog
        return super( ApplicationActionGuiContext, self ).get_progress_dialog()

    def get_window(self):
        if self.workspace is not None and not is_deleted(self.workspace):
            return self.workspace.window()

    def create_model_context( self ):
        context = super( ApplicationActionGuiContext, self ).create_model_context()
        context.admin = self.admin
        return context
        
    def copy( self, base_class=None ):
        new_context = super( ApplicationActionGuiContext, self ).copy(base_class)
        new_context.workspace = self.workspace
        new_context.admin = self.admin
        return new_context
        
class SelectProfile( Action ):
    """Select the application profile to use
    
    :param profile_store: an object of type
        :class:`camelot.core.profile.ProfileStore`
    :param edit_dialog_class: a :class:`QtWidgets.QDialog` to display the needed
        fields to store in a profile
    This action is also useable as an action step, which will return the
    selected profile.
    """
    
    new_icon = FontIcon('plus-circle') # 'tango/16x16/actions/document-new.png'
    save_icon = FontIcon('save') # 'tango/16x16/actions/document-save.png'
    load_icon = FontIcon('folder-open') # 'tango/16x16/actions/document-open.png'
    file_name_filter = _('Profiles file (*.ini)')
    
    def __init__( self, profile_store, edit_dialog_class=None):
        from camelot.core.profile import ProfileStore
        if profile_store==None:
            profile_store=ProfileStore()
        self.profile_store = profile_store
        self.edit_dialog_class = edit_dialog_class
        self.selected_profile = None
    
    def gui_run(self, gui_context):
        super(SelectProfile, self).gui_run(gui_context)
        return self.selected_profile
        
    def model_run( self, model_context ):
        from camelot.view import action_steps
        from camelot.view.action_steps.profile import EditProfiles

        # dummy profiles
        new_profile, save_profiles, load_profiles = object(), object(), object()
        selected_profile = new_profile
        try:
            while selected_profile in (None, new_profile, 
                                       save_profiles, load_profiles):
                profiles = self.profile_store.read_profiles()
                profiles.sort()
                items = [(None,'')] + [(p,p.name) for p in profiles]
                font = QtGui.QFont()
                font.setItalic(True)
                items.append({Qt.UserRole: new_profile, Qt.FontRole: font,
                              Qt.DisplayRole: ugettext('new/edit profile'),
                              Qt.DecorationRole: self.new_icon
                              })
                if len(profiles):
                    items.append({Qt.UserRole: save_profiles, Qt.FontRole: font,
                                  Qt.DisplayRole: ugettext('save profiles'),
                                  Qt.DecorationRole: self.save_icon
                                  })
                items.append({Qt.UserRole: load_profiles, Qt.FontRole: font,
                              Qt.DisplayRole: ugettext('load profiles'),
                              Qt.DecorationRole: self.load_icon
                              })
                select_profile = action_steps.SelectItem( items )
                last_profile = self.profile_store.get_last_profile()
                select_profile.title = ugettext('Profile Selection')
                if len(profiles):
                    subtitle = ugettext('Select a stored profile:')
                else:
                    subtitle = ugettext('''Load profiles from file or'''
                                        ''' create a new profile''')
                select_profile.subtitle = subtitle
                if last_profile in profiles:
                    select_profile.value = last_profile
                elif len(profiles):
                    select_profile.value = None
                else:
                    select_profile.value = load_profiles
                selected_profile = yield select_profile
                if selected_profile is new_profile:
                    edit_profile_name = ''
                    while selected_profile is new_profile:
                        profile_info = yield EditProfiles(profiles, current_profile=edit_profile_name, dialog_class=self.edit_dialog_class)
                        profile = self.profile_store.read_profile(profile_info['name'])
                        if profile is None:
                            profile = self.profile_store.profile_class(**profile_info)
                        else:
                            profile.__dict__.update(profile_info)
                        yield action_steps.UpdateProgress(text=ugettext('Verifying database settings'))
                        engine = profile.create_engine()
                        try:
                            connection = engine.raw_connection()
                            cursor = connection.cursor()
                            cursor.close()
                            connection.close()
                        except Exception as e:
                            exception_box = action_steps.MessageBox( title = ugettext('Could not connect to database, please check host and port'),
                                                                     text = _('Verify driver, host and port or contact your system administrator'),
                                                                     standard_buttons = QtWidgets.QMessageBox.Ok )
                            exception_box.informative_text = six.text_type(e)
                            yield exception_box
                            edit_profile_name = profile.name
                            if profile in profiles:
                                profiles.remove(profile)
                            profiles.append(profile)
                            profiles.sort()
                            continue
                        self.profile_store.write_profile(profile)
                        selected_profile = profile
                elif selected_profile is save_profiles:
                    file_name = yield action_steps.SaveFile(file_name_filter=self.file_name_filter)
                    self.profile_store.write_to_file(file_name)
                elif selected_profile is load_profiles:
                    file_names =  yield action_steps.SelectFile(file_name_filter=self.file_name_filter)
                    for file_name in file_names:
                        self.profile_store.read_from_file(file_name)
        except CancelRequest:
            # explicit handling of exit when cancel button is pressed,
            # to avoid the use of subgenerators in the main action
            yield Exit()
        message = ugettext(u'Use {} profile'.format(selected_profile.name))
        yield action_steps.UpdateProgress(text=message)
        self.profile_store.set_last_profile( selected_profile )
        self.selected_profile = selected_profile


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
        assert isinstance( entity_admin, EntityAdmin )
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

    def model_run( self, model_context ):
        from camelot.view import action_steps
        yield action_steps.UpdateProgress(text=_('Open table'))
        # swith comments here to turn on proof-of-concept qml table view
        #step = action_steps.OpenQmlTableView(
        step = action_steps.OpenTableView(
            self._entity_admin, self._entity_admin.get_query()
        )
        step.new_tab = (model_context.mode_name == 'new_tab')
        yield step

class OpenNewView( EntityAction ):
    """An application action that opens a new view of an Entity
    
    :param entity_admin: an instance of 
        :class:`camelot.admin.entity_admin.EntityAdmin` to be used to
        visualize the entities
    
    """

    verbose_name = _('New')
    shortcut = QtGui.QKeySequence.New
    icon = FontIcon('plus-circle') # 'tango/16x16/actions/document-new.png'
    tooltip = _('New')
            
    def get_state( self, model_context ):
        state = super( OpenNewView, self ).get_state( model_context )
        state.verbose_name = self.verbose_name or ugettext('New %s')%(self._entity_admin.get_verbose_name())
        state.tooltip = ugettext('Create a new %s')%(self._entity_admin.get_verbose_name())
        return state

    def model_run( self, model_context ):
        from camelot.view import action_steps
        admin = yield action_steps.SelectSubclass(self._entity_admin)
        new_object = admin.entity()
        # Give the default fields their value
        admin.add(new_object)
        admin.set_defaults(new_object)
        yield action_steps.OpenFormView([new_object], admin)
        

class ShowAbout( Action ):
    """Show the about dialog with the content returned by the
    :meth:`ApplicationAdmin.get_about` method
    """
    
    verbose_name = _('&About')
    icon = FontIcon('address-card') # 'tango/16x16/mimetypes/application-certificate.png'
    tooltip = _("Show the application's About box")
    
    def gui_run( self, gui_context ):
        abtmsg = gui_context.admin.get_application_admin().get_about()
        QtWidgets.QMessageBox.about( gui_context.workspace, 
                                 ugettext('About'), 
                                 six.text_type( abtmsg ) )
        
class Backup( Action ):
    """
Backup the database to disk

.. attribute:: backup_mechanism

    A subclass of :class:`camelot.core.backup.BackupMechanism` that enables 
    the application to perform backups an restores.
    """
    
    verbose_name = _('&Backup')
    tooltip = _('Backup the database')
    icon = FontIcon('save') # 'tango/16x16/actions/document-save.png'
    backup_mechanism = BackupMechanism

    def model_run( self, model_context ):
        from camelot.view.action_steps import SaveFile, UpdateProgress
        destination = yield SaveFile()
        yield UpdateProgress(text = _('Backup in progress'))
        backup_mechanism = self.backup_mechanism(destination)
        backup_iterator = backup_mechanism.backup(metadata.bind)
        for completed, total, description in backup_iterator:
            yield UpdateProgress(completed,
                                 total,
                                 text = description)

class Refresh( Action ):
    """Reload all objects from the database and update all views in the
    application."""
    
    verbose_name = _('Refresh')
    tooltip = _('Refresh')
    shortcut = QtGui.QKeySequence( Qt.Key_F9 )
    icon = FontIcon('sync') # 'tango/16x16/actions/view-refresh.png'
    
    def model_run( self, model_context ):
        import sqlalchemy.exc as sa_exc
        from camelot.core.orm import Session
        from camelot.view import action_steps
        LOGGER.debug('session refresh requested')
        progress_db_message = ugettext('Reload data from database')
        progress_view_message = ugettext('Update screens')
        session = Session()
        refreshed_objects = []
        expunged_objects = []
        #
        # Loop over the objects one by one to be able to detect the deleted
        # objects
        #
        session_items = len( session.identity_map )
        for i, (_key, obj) in enumerate( six.iteritems(session.identity_map) ):
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
        yield action_steps.UpdateObjects(refreshed_objects)
        yield action_steps.DeleteObjects(expunged_objects)
        yield action_steps.Refresh()

class Restore(Refresh):
    """
Restore the database to disk

.. attribute:: backup_mechanism

    A subclass of :class:`camelot.core.backup.BackupMechanism` that enables 
    the application to perform backups an restores.
"""
    
    verbose_name = _('&Restore')
    tooltip = _('Restore the database from a backup')
    icon = FontIcon('hdd') # 'tango/16x16/devices/drive-harddisk.png'
    backup_mechanism = BackupMechanism
    shortcut = None
            
    def model_run( self, model_context ):
        from camelot.view.action_steps import UpdateProgress, SelectFile
        backups = yield SelectFile()
        yield UpdateProgress( text = _('Restore in progress') )
        for backup in backups:
            backup_mechanism = self.backup_mechanism(backup)
            restore_iterator = backup_mechanism.restore(metadata.bind)
            for completed, total, description in restore_iterator:
                yield UpdateProgress(completed,
                                     total,
                                     text = description)
            for step in super(Restore, self).model_run(model_context):
                yield step

class Profiler( Action ):
    """Start/Stop the runtime profiler.  This action exists for debugging
    purposes, to evaluate where an application spends its time.
    """
    
    verbose_name = _('Profiler start/stop')
    
    def __init__(self):
        self.model_profile = None
        self.gui_profile = None

    def gui_run(self, gui_context):
        import cProfile
        if self.gui_profile is None:
            self.gui_profile = cProfile.Profile()
            self.gui_profile.enable()
        else:
            self.gui_profile.disable()
        super(Profiler, self).gui_run(gui_context)

    def model_run(self, model_context):
        from ...view import action_steps
        from six import StringIO
        import cProfile
        import pstats
        if self.model_profile is None:
            yield action_steps.MessageBox('Start profiler')
            self.model_profile = cProfile.Profile()
            self.model_profile.enable()
        else:
            yield action_steps.UpdateProgress(text='Creating statistics')
            self.model_profile.disable()
            profiles = [('model', self.model_profile), ('gui', self.gui_profile)]
            self.model_profile = None
            self.gui_profile = None
            for label, profile in profiles:
                stream = StringIO()
                stats = pstats.Stats(profile, stream=stream)
                stats.sort_stats('cumulative')
                yield action_steps.UpdateProgress(
                    text='Create {0} report'.format(label)
                )
                stats.print_stats()
                stream.seek(0)
                yield action_steps.OpenString(stream.getvalue().encode('utf-8'))
                filename = action_steps.OpenFile.create_temporary_file(
                    '{0}.prof'.format(label)
                )
                stats.dump_stats(filename)
                yield action_steps.MessageBox(
                    'Profile stored in {0}'.format(filename))
            
class Exit( Action ):
    """Exit the application"""
    
    verbose_name = _('E&xit')
    shortcut = QtGui.QKeySequence.Quit
    icon = FontIcon('times-circle') # 'tango/16x16/actions/system-shutdown.png'
    tooltip = _('Exit the application')
    
    def gui_run( self, gui_context ):
        from camelot.view.model_thread import get_model_thread
        model_thread = get_model_thread()
        # we might exit the application when the workspace is not even there
        if gui_context.workspace != None:
            gui_context.workspace.close_all_views()
        if model_thread != None:
            model_thread.stop()
        QtCore.QCoreApplication.exit(0)
        
#
# Some actions to assist the debugging process
#

class ChangeLogging( Action ):
    """Allow the user to change the logging configuration"""
    
    verbose_name = _('Change logging')
    icon = FontIcon('wrench') # 'tango/16x16/emblems/emblem-photos.png'
    tooltip = _('Change the logging configuration of the application')

    @classmethod
    def before_cursor_execute(cls, conn, cursor, statement, parameters, context,
                              executemany):
        context._query_start_time = time.time()
        LOGGER.info("start query:\n\t%s" % statement.replace("\n", "\n\t"))
        LOGGER.info("parameters: %r" % (parameters,))

    @classmethod
    def after_cursor_execute(cls, conn, cursor, statement, parameters, context,
                             executemany):
        total = time.time() - context._query_start_time
        LOGGER.info("query Complete in %.02fms" % (total*1000))

    @classmethod
    def begin_transaction(cls, conn):
        LOGGER.info("begin transaction")

    @classmethod
    def commit_transaction(cls, conn):
        LOGGER.info("commit transaction")

    @classmethod
    def rollback_transaction(cls, conn):
        LOGGER.info("rollback transaction")

    @classmethod
    def connection_checkout(cls, dbapi_connection, connection_record, 
                            connection_proxy):
        LOGGER.info('checkout connection {0}'.format(id(dbapi_connection)))

    @classmethod
    def connection_checkin(cls, dbapi_connection, connection_record):
        LOGGER.info('checkin connection {0}'.format(id(dbapi_connection)))

    def model_run( self, model_context ):
        from camelot.view.controls import delegates
        from camelot.view import action_steps
        from camelot.admin.object_admin import ObjectAdmin
        
        from sqlalchemy import event
        from sqlalchemy.engine import Engine
        from sqlalchemy.pool import Pool
        
        class Options( object ):
            
            def __init__( self ):
                self.level = logging.INFO
                self.queries = False
                self.pool = False
                
            class Admin( ObjectAdmin ):
                list_display = ['level', 'queries', 'pool']
                field_attributes = { 'level':{ 'delegate':delegates.ComboBoxDelegate,
                                               'editable':True,
                                               'choices':[(l,logging.getLevelName(l)) for l in [logging.DEBUG, 
                                                                                                logging.INFO, 
                                                                                                logging.WARNING,
                                                                                                logging.ERROR,
                                                                                                logging.CRITICAL]]},
                                     'queries':{ 'delegate': delegates.BoolDelegate,
                                                 'tooltip': _('Log and time queries send to the database'),
                                                 'editable': True},
                                     'pool':{ 'delegate': delegates.BoolDelegate,
                                              'tooltip': _('Log database connection checkin/checkout'),
                                              'editable': True},
                                     }
                
        options = Options()
        yield action_steps.ChangeObject( options )
        logging.getLogger().setLevel( options.level )
        if options.queries == True:
            event.listen(Engine, 'before_cursor_execute',
                         self.before_cursor_execute)
            event.listen(Engine, 'after_cursor_execute',
                         self.after_cursor_execute)
            event.listen(Engine, 'begin',
                         self.begin_transaction)
            event.listen(Engine, 'commit',
                         self.commit_transaction)
            event.listen(Engine, 'rollback',
                         self.rollback_transaction)
        if options.pool == True:
            event.listen(Pool, 'checkout',
                         self.connection_checkout)
            event.listen(Pool, 'checkin',
                         self.connection_checkin)

        
class SegmentationFault( Action ):
    """Create a segmentation fault by reading null, this is to test
        the faulthandling functions.  this method is triggered by pressing
        :kbd:`Ctrl-Alt-0` in the GUI"""
    
    verbose_name = _('Segmentation Fault')
    shortcut = QtGui.QKeySequence( QtCore.Qt.CTRL+QtCore.Qt.ALT+QtCore.Qt.Key_0 )
    
    def model_run( self, model_context ):
        from camelot.view import action_steps
        ok = yield action_steps.MessageBox( text =  'Are you sure you want to segfault the application',
                                            standard_buttons = QtWidgets.QMessageBox.No | QtWidgets.QMessageBox.Yes )
        if ok == QtWidgets.QMessageBox.Yes:
            import faulthandler
            faulthandler._read_null()        

def structure_to_application_action(structure, application_admin):
    """Convert a python structure to an ApplicationAction

    :param application_admin: the 
        :class:`camelot.admin.application_admin.ApplicationAdmin` to use to
        create other Admin classes.
    """
    if isinstance(structure, Action):
        return structure
    admin = application_admin.get_related_admin( structure )
    return OpenTableView( admin )



