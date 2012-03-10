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
"""Most applications need to perform some scheduled jobs to process information.
Users need to be able to monitor the functioning of those scheduled jobs.

These classes provide the means to store the result of batch jobs to enable the user to
review or plan them.
"""

import sqlalchemy.types
from sqlalchemy import orm, sql

from elixir.entity import Entity
from elixir.options import using_options
from elixir.fields import Field
from elixir.relationships import ManyToOne

from camelot.core.utils import ugettext_lazy as _
from camelot.core.sql import metadata
from camelot.view import filters
from camelot.admin.entity_admin import EntityAdmin
from camelot.admin.action import Action
from camelot.core.document import documented_entity
import camelot.types

import datetime

__metadata__ = metadata

class BatchJobType(Entity):
    """The type of batch job, the user will be able to filter his
    jobs based on their type.  A type might be 'Create management reports' """
    using_options( tablename = 'batch_job_type' )
    name   = Field(sqlalchemy.types.Unicode(256), required=True)
    parent = ManyToOne('BatchJobType')
    
    def __unicode__(self):
        return self.name
    
    @classmethod
    def get_or_create( cls, name ):
        batch_job_type = cls.query.filter_by( name = name ).first()
        if not batch_job_type:
            batch_job_type = cls( name = name )
            batch_job_type.flush()
        return batch_job_type
    
    class Admin(EntityAdmin):
        verbose_name = _('Batch job type')
        list_display = ['name', 'parent']
        
BatchJobType = documented_entity()( BatchJobType )

def hostname():
    import socket
    return socket.gethostname()
    
class CancelBatchJob( Action ):
    
    verbose_name = _('Cancel')
    
    def model_run( self, model_context ):
        from camelot.view.action_steps import FlushSession
        for batch_job in model_context.get_selection():
            batch_job.status = 'canceled'
        yield FlushSession( model_context.session )

class BatchJob(Entity):
    """Information the batch job that is planned, running or has run"""
    using_options( tablename = 'batch_job', order_by=['-date'] )
    date    = Field(sqlalchemy.types.DateTime, required=True, default=datetime.datetime.now)
    host    = Field(sqlalchemy.types.Unicode(256), required=True, default=hostname)
    type    = ManyToOne('BatchJobType', required=True, ondelete = 'restrict', onupdate = 'cascade')
    status  = Field(camelot.types.Enumeration([ (-2, 'planned'), 
                                                (-1, 'running'), 
                                                (0,  'success'), 
                                                (1,  'warnings'), 
                                                (2,  'errors'),
                                                (3,  'canceled'), ]), required=True, default='planned' )
    message = Field(camelot.types.RichText())
    
    def is_canceled(self):
        """Verifies if this Batch Job is canceled.  Returns :keyword:`True` if 
        it is.  This verification is done without using the ORM, so the verification
        has no impact on the current session or the objects itself.  This method
        is thus suited to call inside a running batch job to verifiy if another
        user has canceled the running job.
        
        :return: :keyword:`True` or :keyword:`False`
        """
        table = orm.class_mapper( BatchJob ).mapped_table
        query = sql.select( [table.c.status] ).where( table.c.id == self.id )
        for row in table.bind.execute( query ):
            if row['status'] == 'canceled':
                return True
        return False
        
    def add_exception_to_message(self, exception):
        """If an exception occurs in a batch job, this method can be used to add
        the stack trace of the exception to the message"""
        import traceback, cStringIO
        sio = cStringIO.StringIO()
        traceback.print_exc(file=sio)
        traceback_print = sio.getvalue()
        sio.close()
        self.message = (self.message or '') + '<br/>' + unicode(exception) + '<br/><font color="grey">' +  traceback_print.replace('\n', '<br/>') + '</font>'
        
    def add_strings_to_message(self, strings):
        """:param strings: a list or generator of strings"""
        self.message = (self.message or '') + u'<br/>' + '<br/>'.join(list(strings))
        
    class Admin(EntityAdmin):
        verbose_name = _('Batch job')
        list_display = ['date', 'host', 'type', 'status']
        list_filter = ['status', filters.ComboBoxFilter('host')]
        form_display = list_display + ['message']
        form_actions = [ CancelBatchJob() ]
        
BatchJob = documented_entity()( BatchJob )


