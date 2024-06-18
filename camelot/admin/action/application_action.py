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

import cProfile
import logging
import itertools

from ...core.naming import initial_naming_context
from ...core.qt import Qt, QtCore, QtWidgets, QtGui
from ...core.sql import metadata
from .base import RenderHint
from camelot.admin.icon import Icon, CompletionValue
from camelot.admin.action.base import Action, Mode, ModelContext
from camelot.core.exception import CancelRequest
from camelot.core.orm import Session
from camelot.core.utils import ugettext, ugettext_lazy as _
from camelot.core.backup import BackupMechanism

"""ModelContext, GuiContext and Actions that run in the context of an 
application.
"""

LOGGER = logging.getLogger( 'camelot.admin.action.application_action' )

application_action_context = initial_naming_context.bind_new_context(
    'application_action', immutable=True
)

model_context_counter = itertools.count(1)
model_context_naming = initial_naming_context.bind_new_context('model_context')

class ApplicationActionModelContext(ModelContext):
    """The Model context for an :class:`camelot.admin.action.Action`.  On top 
    of the attributes of the :class:`camelot.admin.action.base.ModelContext`, 
    this context contains :
        
    .. attribute:: admin
   
        the application admin.

    .. attribute:: actions

        the actions in the same context

    .. attribute:: session

        the active session
    """
    
    def __init__(self, admin):
        super(ApplicationActionModelContext, self).__init__()
        self.admin = admin
        self.actions = []

    # Cannot set session in constructor because constructor is called
    # inside the GUI thread
    @property
    def session( self ):
        return Session()


class UpdateActions(Action):

    def model_run(self, model_context, mode):
        from camelot.view import action_steps
        actions_state = dict()
        for action in model_context.actions:
            actions_state[action] = action.get_state(model_context)
        yield action_steps.UpdateActionsState(model_context, actions_state)

new_profile, save_profiles, load_profiles = object(), object(), object()
profiles_context = initial_naming_context.bind_new_context('profiles')
new_profile_name = profiles_context.bind('new_profile', new_profile)
save_profiles_name = profiles_context.bind('save_profiles', save_profiles)
load_profiles_name = profiles_context.bind('load_profiles', load_profiles)
store_context = profiles_context.bind_new_context('store')

class SelectProfileMixin:
    """Select the application profile to use
    
    :param profile_store: an object of type
        :class:`camelot.core.profile.ProfileStore`
    """

    file_name_filter = _('Profiles file (*.ini)')

    @classmethod
    def select_profile(cls, profile_store, app_admin):
        from camelot.view import action_steps
        from camelot.core.profile import Profile, NonEditableProfileAdmin
        selected_profile = new_profile
        try:
            while selected_profile in (None, new_profile,
                                       save_profiles, load_profiles):
                profiles = profile_store.read_profiles()
                profiles.sort()
                last_profile = profile_store.get_last_profile()
                last_profile_name = initial_naming_context._bind_object(None)
                items = [CompletionValue(
                    value = initial_naming_context._bind_object(None),
                    verbose_name = '',
                )]
                for profile in profiles:
                    profile_name = store_context.rebind(profile.name, profile)
                    items.append(CompletionValue(
                        value = profile_name,
                        verbose_name = profile.name,
                    ))
                    if profile == last_profile:
                        last_profile_name = profile_name
                items.append(CompletionValue(
                    value = new_profile_name,
                    verbose_name = ugettext('new/edit profile'),
                    icon = Icon('plus-circle'),
                ))
                if len(profiles):
                    items.append(CompletionValue(
                        value = save_profiles_name,
                        verbose_name = ugettext('save profiles'),
                        icon = Icon('save')
                    ))
                items.append(CompletionValue(
                    value = load_profiles_name,
                    verbose_name = ugettext('load profiles'),
                    icon = Icon('folder-open')
                ))
                select_profile = action_steps.SelectItem(items)
                
                select_profile.title = ugettext('Profile Selection')
                if len(profiles):
                    subtitle = ugettext('Select a stored profile:')
                else:
                    subtitle = ugettext('''Load profiles from file or'''
                                        ''' create a new profile''')
                select_profile.subtitle = subtitle
                if last_profile in profiles:
                    select_profile.value = last_profile_name
                elif len(profiles):
                    select_profile.value = None
                else:
                    select_profile.value = load_profiles_name
                selected_name = yield select_profile
                selected_profile = initial_naming_context.resolve(selected_name)
                if selected_profile is new_profile:
                    while selected_profile is new_profile:
                        profile_admin = NonEditableProfileAdmin(app_admin, Profile)
                        proxy = profile_admin.get_proxy(profiles)
                        try:
                            yield action_steps.ChangeObjects(profiles, profile_admin, proxy)
                            profile_store.write_profiles(proxy.get_model())
                        except CancelRequest:
                            pass
                        selected_profile = None
                elif selected_profile is save_profiles:
                    file_name = yield action_steps.SaveFile(file_name_filter=cls.file_name_filter)
                    profile_store.write_to_file(file_name)
                elif selected_profile is load_profiles:
                    file_names =  yield action_steps.SelectFile(file_name_filter=cls.file_name_filter)
                    for file_name in file_names:
                        profile_store.read_from_file(file_name)
        except CancelRequest:
            # explicit handling of exit when cancel button is pressed,
            # to avoid the use of subgenerators in the main action
            from camelot.view.action_steps.application import Exit
            yield Exit()
            raise SystemExit()
        message = ugettext(u'Use {} profile'.format(selected_profile.name))
        yield action_steps.UpdateProgress(text=message)
        profile_store.set_last_profile(selected_profile)


class EntityAction( Action ):
    """Generic ApplicationAction that acts upon an Entity class"""

    name = 'entity_action'

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

    name = 'open_table_view'
    modes = [ Mode( 'new_tab', _('Open in New Tab') ) ]
        
    def get_state( self, model_context ):
        state = super( OpenTableView, self ).get_state( model_context )
        state.verbose_name = self.verbose_name or self._entity_admin.get_verbose_name_plural()
        return state

    def model_run( self, model_context, mode ):
        from camelot.view import action_steps
        yield action_steps.UpdateProgress(text=_('Open table'))
        yield action_steps.OpenQmlTableView(
            self._entity_admin.get_query(),
            self._entity_admin,
        )

class Backup( Action ):
    """
Backup the database to disk

.. attribute:: backup_mechanism

    A subclass of :class:`camelot.core.backup.BackupMechanism` that enables 
    the application to perform backups an restores.
    """

    name = 'backup'
    verbose_name = _('&Backup')
    tooltip = _('Backup the database')
    icon = Icon('save') # 'tango/16x16/actions/document-save.png'
    backup_mechanism = BackupMechanism

    def model_run( self, model_context, mode ):
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

    name = 'refresh'
    render_hint = RenderHint.TOOL_BUTTON
    verbose_name = _('Refresh')
    tooltip = _('Refresh')
    shortcut = QtGui.QKeySequence( Qt.Key.Key_F9.value )
    icon = Icon('sync') # 'tango/16x16/actions/view-refresh.png'
    
    def model_run( self, model_context, mode ):
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
                yield action_steps.UpdateProgress( i + 1,
                                                   session_items, 
                                                   progress_db_message )
        yield action_steps.UpdateProgress(text = progress_view_message )
        yield action_steps.UpdateObjects(refreshed_objects)
        yield action_steps.DeleteObjects(expunged_objects)
        yield action_steps.Refresh()
        yield action_steps.UpdateProgress(1, 1)

refresh = Refresh()

class Restore(Refresh):
    """
Restore the database to disk

.. attribute:: backup_mechanism

    A subclass of :class:`camelot.core.backup.BackupMechanism` that enables 
    the application to perform backups an restores.
"""

    name = 'restore'
    verbose_name = _('&Restore')
    tooltip = _('Restore the database from a backup')
    icon = Icon('hdd') # 'tango/16x16/devices/drive-harddisk.png'
    backup_mechanism = BackupMechanism
    shortcut = None
            
    def model_run( self, model_context, mode ):
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
            for step in super(Restore, self).model_run(model_context, mode):
                yield step


class Profiler( Action ):
    """Start/Stop the runtime profiler.  This action exists for debugging
    purposes, to evaluate where an application spends its time.
    """

    name = 'profiler'
    verbose_name = _('Profiler start/stop')
    
    def __init__(self):
        self.model_profile = None
        self.gui_profile = None

    def model_run(self, model_context, mode):
        from ...view import action_steps
        if self.model_profile is None:
            yield action_steps.MessageBox('Start profiler')
            yield action_steps.StartProfiler()
            self.model_profile = cProfile.Profile()
            self.model_profile.enable()
        else:
            yield action_steps.StopProfiler()
            self.model_profile.disable()
            action_steps.StopProfiler.write_profile(self.model_profile, 'model')
            yield action_steps.MessageBox('Profiler stopped')


class Exit( Action ):
    """Exit the application"""

    name = 'exit'
    verbose_name = _('E&xit')
    shortcut = QtGui.QKeySequence.StandardKey.Quit
    icon = Icon('times-circle') # 'tango/16x16/actions/system-shutdown.png'
    tooltip = _('Exit the application')

    def model_run( self, model_context, mode ):
        from camelot.view.action_steps.application import Exit
        yield Exit()

exit_name = application_action_context.bind(Exit.name, Exit(), True)

       
class SegmentationFault( Action ):
    """Create a segmentation fault by reading null, this is to test
        the faulthandling functions.  this method is triggered by pressing
        :kbd:`Ctrl-Alt-0` in the GUI"""

    name = 'segfault'
    verbose_name = _('Segmentation Fault')
    shortcut = QtGui.QKeySequence( QtCore.Qt.Modifier.CTRL.value + QtCore.Qt.Modifier.ALT.value + QtCore.Qt.Key.Key_0.value )
    
    def model_run( self, model_context, mode ):
        from camelot.view import action_steps
        ok = yield action_steps.MessageBox( text =  'Are you sure you want to segfault the application',
                                            standard_buttons = [QtWidgets.QMessageBox.StandardButton.No, QtWidgets.QMessageBox.StandardButton.Yes] )
        if ok == QtWidgets.QMessageBox.StandardButton.Yes:
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
    return OpenTableView(admin.get_query(), admin)



