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
"""Most users have the need to do some basic task tracking accross various
parts of the data model.

These classes provide basic task tracking with configurable statuses, 
categories and roles.  They are presented to the user as "Todo's"
"""

from elixir import Entity, using_options, Field, ManyToMany, OneToMany, ManyToOne
import sqlalchemy.types

from camelot.core.utils import ugettext_lazy as _
from camelot.model import metadata
from camelot.model.authentication import getCurrentAuthentication
from camelot.admin.entity_admin import EntityAdmin
from camelot.core.document import documented_entity
from camelot.view import forms
from camelot.view.controls import delegates
import camelot.types

import datetime

__metadata__ = metadata

class Task( Entity ):
    using_options(tablename='task', order_by=['-creation_date'] )
    creation_date    = Field( sqlalchemy.types.Date, required=True, default=datetime.date.today )
    due_date         = Field( sqlalchemy.types.Date, required=False, default=None )
    description      = Field( sqlalchemy.types.Unicode(255), required=True )
    notes            = OneToMany( 'TaskNote', cascade='all, delete, delete-orphan' )
    categories = ManyToMany( 'PartyCategory',
                             tablename='party_category_task', 
                             remote_colname='party_category_id',
                             local_colname='task_id')
    
    def _get_first_note(self):
        if self.notes:
            return self.notes[0].note

    def _set_first_note(self, note):
        if note and self.id:
            if self.notes:
                self.notes[0].note = note
            else:
                self.notes.append( TaskNote( note=note, created_by=getCurrentAuthentication() ) )
 
    note = property( _get_first_note, _set_first_note )
    
    class Admin( EntityAdmin ):
        verbose_name = _('Todo')
        list_display = ['creation_date', 'description', 'due_date']
        list_filter  = ['categories.name']
        form_display = forms.Form( ['description', 'creation_date', 'due_date', 
                        'note', 'categories'] )
        field_attributes = {'note':{'delegate':delegates.RichTextDelegate,
                                    'editable':lambda self:self.id}}

Task = documented_entity()( Task )

class TaskNote( Entity ):
    using_options(tablename='task_note', order_by=['-created_at'] )
    of = ManyToOne('Task', required=True, onupdate='cascade', ondelete='cascade')
    created_at = Field( sqlalchemy.types.Date, required=True, default=datetime.date.today )
    created_by = ManyToOne('AuthenticationMechanism', required=True )
    note = Field( camelot.types.RichText() )
  
    class Admin( EntityAdmin ):
        verbose_name = _('Note')
        list_display = ['created_at', 'created_by']
        form_display = list_display + ['note']

