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

"""ModelContext and Actions that run in the context of an 
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

    @property
    def session( self ):
        return Session()


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
