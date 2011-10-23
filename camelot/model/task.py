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
"""Most users have the need to do some basic task tracking across various
parts of the data model.

These classes provide basic task tracking with configurable statuses, 
categories and roles.  They are presented to the user as "Todo's"
"""

from elixir import Entity, using_options, Field, ManyToMany, OneToMany, ManyToOne, entities, ColumnProperty
import sqlalchemy.types
from sqlalchemy import sql
from sqlalchemy.orm import backref

from camelot.core.utils import ugettext_lazy as _
from camelot.model import metadata
from camelot.model.authentication import getCurrentAuthentication
from camelot.model.type_and_status import type_3_status, create_type_3_status_mixin, get_status_type_class, get_status_class
from camelot.admin.entity_admin import EntityAdmin
from camelot.core.document import documented_entity
from camelot.view import forms
from camelot.view.filters import ComboBoxFilter
from camelot.view.controls import delegates
import camelot.types

import datetime

__metadata__ = metadata

def task_has_id(task):
    return task.id

task_status_type_features = [(None, None, '', ()),
                             (1, 'hidden', 'Zichtbaar in lijst', ((0, 'False'), (1, 'True'))),
                             (2, 'default', '', ((0, 'False'), (1, 'True')))]
task_status_type_features_enumeration = [(f[0], f[1]) for f in task_status_type_features]
task_status_type_feature_descriptions = dict((f[1], f[2]) for f in task_status_type_features)
task_status_type_feature_values = dict((f[1], f[3]) for f in task_status_type_features)

class TaskType( Entity ):
    using_options(tablename='task_type', order_by=['rank', 'description'])
    description = Field( sqlalchemy.types.Unicode(48), required=True, index=True )
    rank = Field(sqlalchemy.types.Integer(), default=1)
    
    def __unicode__(self):
        return self.description or ''
    
    class Admin( EntityAdmin ):
        verbose_name = _('Task Type')
        list_display = ['description', 'rank']

class TaskRoleType( Entity ):
    using_options(tablename='task_role_type', order_by=['rank', 'description'])
    description = Field( sqlalchemy.types.Unicode(48), required=True, index=True )
    rank = Field(sqlalchemy.types.Integer(), default=1)
    
    def __unicode__(self):
        return self.description or ''
    
    class Admin( EntityAdmin ):
        verbose_name = _('Task Role Type')
        list_display = ['description', 'rank']
        

class TaskRole( Entity ):
    using_options(tablename='task_role')
    task = ManyToOne('Task', required = True, ondelete = 'cascade', onupdate = 'cascade')
    party = ManyToOne('Party', required=True, ondelete='restrict', onupdate='cascade')
    described_by = ManyToOne('TaskRoleType', required = False, ondelete = 'restrict', onupdate = 'cascade')
    rank = Field(sqlalchemy.types.Integer(), required=True, default=1)
    comment = Field( sqlalchemy.types.Unicode( 256 ) )

    class Admin(EntityAdmin):
        verbose_name = _('Role within task')
        list_display = ['party', 'described_by', 'comment', 'rank']
        field_attributes = {'described_by':{'name':_('Type'), 'delegate':delegates.ManyToOneChoicesDelegate},
                                 'rank':{'choices':[(i,str(i)) for i in range(1,5)]},
                                 }

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

class TaskDocumentType( Entity ):
    using_options(tablename='task_document_type', order_by=['rank', 'description'])
    description = Field( sqlalchemy.types.Unicode(48), required=True, index=True )
    rank = Field(sqlalchemy.types.Integer(), default=1)
        
    def __unicode__(self):
        return self.description or ''
    
    class Admin( EntityAdmin ):
        verbose_name = _('Document Type')
        list_display = ['description', 'rank']
  
class TaskDocument( Entity ):
    using_options(tablename='task_document')
    of = ManyToOne('Task', required=True, onupdate='cascade', ondelete='cascade')
    created_at = Field( sqlalchemy.types.Date(), default = datetime.date.today, required = True, index = True )
    created_by = ManyToOne('AuthenticationMechanism', required=True)
    type = ManyToOne('TaskDocumentType', required = False, ondelete = 'restrict', onupdate = 'cascade')
    document = Field( camelot.types.File(), required=True )
    description = Field( sqlalchemy.types.Unicode(200) )
    summary = Field( camelot.types.RichText() )
        
    class Admin(EntityAdmin):
        verbose_name = _('Document')
        list_display = ['document', 'description', 'type']
        form_display = list_display + ['created_at', 'created_by', 'summary']
        field_attributes = {'type':{'delegate':delegates.ManyToOneChoicesDelegate},
                            'created_by':{'default':getCurrentAuthentication}}


class Task( Entity, create_type_3_status_mixin('status') ):
    using_options(tablename='task', order_by=['-creation_date', 'id'] )
    creation_date    = Field( sqlalchemy.types.Date, required=True, default=datetime.date.today )
    due_date         = Field( sqlalchemy.types.Date, required=False, default=None )
    description      = Field( sqlalchemy.types.Unicode(255), required=True )
    status           = OneToMany( type_3_status( 'Task', metadata, entities ), cascade='all, delete, delete-orphan' )
    notes            = OneToMany( 'TaskNote', cascade='all, delete, delete-orphan' )
    documents        = OneToMany( 'TaskDocument', cascade='all, delete, delete-orphan' )
    roles            = OneToMany( 'TaskRole', cascade='all, delete, delete-orphan' )
    described_by     = ManyToOne( 'TaskType', required = False, ondelete = 'restrict', onupdate = 'cascade')
    categories       = ManyToMany( 'PartyCategory',
                                   tablename='party_category_task', 
                                   remote_colname='party_category_id',
                                   local_colname='task_id')
                             
    Admin = None
    
    @ColumnProperty
    def number_of_documents( self ):
        return sql.select( [sql.func.count( TaskDocument.id ) ],
                            whereclause = TaskDocument.of_id == self.id )

    @ColumnProperty
    def current_status_sql( self ):
        status_class = get_status_class('Task')
        status_type_class = get_status_type_class('Task')
        return sql.select( [status_type_class.code],
                           whereclause = sql.and_( status_class.status_for_id == self.id,
                                                   status_class.status_from_date <= sql.functions.current_date(),
                                                   status_class.status_thru_date >= sql.functions.current_date() ),
                           from_obj = [status_type_class.table.join( status_class.table )] ).limit(1)

    @ColumnProperty
    def hidden(self):
        status_class = get_status_class('Task')
        status_type_class = get_status_type_class('Task')
        query = sql.select( [TaskStatusTypeFeature.value],
                            whereclause = sql.and_( status_class.status_for_id == self.id,
                                                    status_class.status_from_date <= sql.functions.current_date(),
                                                    status_class.status_thru_date >= sql.functions.current_date(),
                                                    TaskStatusTypeFeature.described_by == 'hidden' ),
                            from_obj = [status_type_class.table.join( status_class.table ).join( TaskStatusTypeFeature.table )] ).limit(1)
        return sql.func.coalesce( query.as_scalar(), 0 )
        
    @classmethod
    def role_query(cls, columns, role_type_rank ):
        from camelot.model.authentication import Party
        return sql.select( [Party.full_name],
                            sql.and_( Party.id == TaskRole.party_id,
                                      TaskRole.task_id == columns.id,
                                      TaskRoleType.id == TaskRole.described_by_id,
                                      TaskRoleType.rank == role_type_rank ) ).limit(1)
    
    @ColumnProperty
    def role_1(self):
        return Task.role_query( self, 1 )
    
    @ColumnProperty
    def role_2(self):
        return Task.role_query( self, 2 )
    
    @property
    def documents_icon(self):
        if (self.number_of_documents > 0) or len(self.documents):
            return 'document'

    def __unicode__( self ):
        return self.description or ''
    
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
                                
            
TaskStatusType = get_status_type_class( 'Task' )
Task = documented_entity()( Task )

class TaskStatusTypeAdmin(TaskStatusType.Admin):
    def get_delete_message(self, obj):
        return _('All tasks that are related to this status will be effected by this removal.\n\n' +
                 'Are you sure you want to remove this status?')
                  
TaskStatusType.Admin = TaskStatusTypeAdmin
TaskStatusType.Admin.delete_mode = 'on_confirm'

class TaskAdmin( EntityAdmin ):
    verbose_name = _('Task')
    verbose_name_plural = _('Tasks')
    list_display = ['creation_date', 'due_date', 'description', 'described_by', 'current_status_sql', 'role_1', 'role_2', 'documents_icon']
    list_filter  = [ComboBoxFilter('described_by.description'), 
                    ComboBoxFilter('current_status_sql'), 
                    ComboBoxFilter('categories.name'), 'hidden']
    form_state = 'maximized'
    form_display = forms.TabForm( [ ( _('Task'), ['description', 'described_by', 'current_status', 
                                                  'creation_date', 'due_date',  'note',]),
                                    ( _('Category'), ['categories'] ),
                                    ( _('Roles'), ['roles'] ),
                                    ( _('Documents'), ['documents'] ),
                                    ( _('Status'), ['status'] ) ] )
    field_attributes = {'note':{'delegate':delegates.RichTextDelegate,
                                'editable':lambda self:self.id},
                        'described_by':{'delegate':delegates.ManyToOneChoicesDelegate, 'name':_('Type')},
                        'role_1':{'editable':False},
                        'role_2':{'editable':False},
                        'description':{'minimal_column_width':50},
                        'current_status_sql':{'name':'Current status',
                                              'editable':False}}
    
    def get_field_attributes(self, field_name):
        field_attributes = EntityAdmin.get_field_attributes(self, field_name)
        if field_name in ['role_1', 'role_2']:
            name_query = sql.select( [TaskRoleType.description], TaskRoleType.rank == int(field_name[-1]) ).limit(1)
            name = TaskRoleType.query.session.scalar( name_query )
            field_attributes['name'] = name or field_attributes['name']
        return field_attributes

    def flush(self, obj):
        """Set the status of the agreement to draft if it has no status yet"""
        #if not len(obj.status):
            #obj.status.append(self.get_field_attributes('status')['target'](status_from_date=datetime.date.today(),
                                                                            #status_thru_date=end_of_times(),
                                                                            #classified_by=TaskStatusType.query.order_by(TaskStatusType.).first()))
        EntityAdmin.flush(self, obj)
  
Task.Admin = TaskAdmin                      

class TaskStatusTypeFeature(Entity):
    using_options(tablename='task_status_type_feature')
    task_status_type_id = ManyToOne( TaskStatusType, required = True, ondelete = 'cascade', onupdate = 'cascade',
                                     backref=backref('available_with', cascade="all, delete-orphan"))
    described_by = Field(camelot.types.Enumeration(task_status_type_features_enumeration), required = True, default = "hidden")
    comment = Field( sqlalchemy.types.Unicode( 256 ) )
    value = Field( sqlalchemy.types.Integer() )
    
    class Admin(EntityAdmin):
        verbose_name = _('TaskStatusTypeFeature')
        list_display = ['described_by', 'comment', 'value']
        form_display = list_display + ['comment']
        field_attributes = {'described_by': {'name': _('Feature'), 
                                             'tooltip': lambda o:task_status_type_feature_descriptions.get(o.described_by, None)},
                            'value': {'choices': lambda f:task_status_type_feature_values[f.described_by]},
                            }
                            
TaskStatusType.Admin.form_display.append('available_with')
