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

These classes provide the means to store the result of batch jobs to enable the 
user to review or plan them.
"""

import sys

import sqlalchemy.types
from sqlalchemy import orm, sql

from camelot.core.orm import Entity, Field, ManyToOne, using_options

from camelot.core.utils import ugettext_lazy as _
from camelot.view import filters, forms
from camelot.admin.entity_admin import EntityAdmin
from camelot.core.document import documented_entity
import camelot.types

from . import type_and_status

#
# Run batch jobs in separate session to get out of band writing
# to the database
#
BatchSession = orm.sessionmaker( autoflush = False )

batch_job_statusses = [ (-2, 'planned'), 
                        (-1, 'running'), 
                        (0,  'success'), 
                        (1,  'warnings'), 
                        (2,  'errors'),
                        (3,  'canceled') ]
@documented_entity()
class BatchJobType( Entity ):
    """The type of batch job, the user will be able to filter his
    jobs based on their type.  A type might be 'Create management reports' """
    using_options( tablename = 'batch_job_type' )
    name   = Field( sqlalchemy.types.Unicode(256), required=True )
    parent = ManyToOne( 'BatchJobType' )
    
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
        
def hostname():
    import socket
    return unicode( socket.gethostname() )

@documented_entity()
class BatchJob( Entity, type_and_status.StatusMixin ):
    """Information the batch job that is planned, running or has run"""
    using_options( tablename = 'batch_job', order_by=['-id'] )
    host    = Field( sqlalchemy.types.Unicode(256), required=True, default=hostname )
    type    = ManyToOne( 'BatchJobType', required=True, ondelete = 'restrict', onupdate = 'cascade' )
    status  = type_and_status.Status( batch_job_statusses )
    message = Field( camelot.types.RichText() )

    @classmethod
    def create( cls, batch_job_type = None, status = 'running' ):
        """Create a new batch job object in a session of its
        own.  This allows flushing the batch job independent from
        other objects.
        
        :param batch_job_type: an instance of type 
            :class:`camelot.model.batch_job.BatchJobType`
        :param status: the status of the batch job
        :return: a new BatchJob object
        """
        batch_session = BatchSession()
        batch_job = BatchJob(type=batch_job_type)
        batch_job.change_status( 'running' )
        session = orm.object_session( batch_job )
        batch_session_batch_job = batch_session.merge( batch_job )
        if session:
            session.expunge( batch_job )
        batch_session.commit()
        return batch_session_batch_job

    def is_canceled( self ):
        """Verifies if this Batch Job is canceled.  Returns :keyword:`True` if 
        it is.  This method is thus suiteable to call inside a running batch job 
        to verifiy if another user has canceled the running job.  Create a
        batch job object through the :meth:`create` method to make sure
        requesting the status does not interfer with the normal session.
        
        :return: :keyword:`True` or :keyword:`False`
        """
        orm.object_session( self ).expire( self, ['status'] )
        return self.current_status == 'canceled'
        
    def add_exception_to_message( self, 
                                  exc_type = None, 
                                  exc_val = None, 
                                  exc_tb = None ):
        """If an exception occurs in a batch job, this method can be used to add
        the stack trace of an exception to the message.
        
        If no arguments are given, `sys.exc_traceback` is used.
        
        :param exc_type: type of the exception, such as in `sys.exc_type`
        :param exc_val: value of the exception, such as in `sys.exc_value`
        :param exc_tb: a traceback object, such as in `sys.exc_traceback`
        """
        import traceback, cStringIO
        sio = cStringIO.StringIO()
        traceback.print_exception( exc_type or sys.exc_type, 
                                   exc_val or sys.exc_value,
                                   exc_tb or sys.exc_traceback,
                                   None, 
                                   sio )
        traceback_print = sio.getvalue()
        sio.close()
        self.add_strings_to_message( [ unicode(exc_type or sys.exc_type) ], 
                                     color = 'red' )
        self.add_strings_to_message( traceback_print.split('\n'),
                                     color = 'grey' )
        
    def add_strings_to_message( self, strings, color = None ):
        """Add strings to the message of this batch job.
        
        :param strings: a list or generator of strings
        :param color: the html color to be used for the strings (`'red'`, 
        `'green'`, ...), None if the color needs no change. 
        """
        if color:
            strings = [u'<font color="%s">'%color] + strings + [u'</font>']
        session = orm.object_session( self )
        # message might be changed in the orm
        session.commit()
        batch_table = self.__table__
        update = batch_table.update().where( batch_table.c.id == self.id )
        update = update.values( message = sql.func.coalesce( batch_table.c.message, '' ) + sql.bindparam('line') )
        for line in strings:
            session.execute( update, params = {'line':line + '<br/>'} )
        session.commit()
        
    def __enter__( self ):
        self.change_status( 'running' )
        orm.object_session( self ).commit()
        return self
    
    def __exit__( self, exc_type, exc_val, exc_tb ):
        if exc_type != None:
            self.add_exception_to_message( exc_type, exc_val, exc_tb )
            self.change_status( 'errors' )
        elif self.current_status == 'running':
            self.change_status( 'success' )
        orm.object_session( self ).commit()
        return True
        
    class Admin(EntityAdmin):
        verbose_name = _('Batch job')
        list_display = ['host', 'type', 'current_status']
        list_filter = ['current_status', filters.ComboBoxFilter('host')]
        form_display = forms.TabForm( [ ( _('Job'), list_display + ['message'] ),
                                        ( _('History'), ['status'] ) ] )
        form_actions = [ type_and_status.ChangeStatus( 'canceled',
                                                       _('Cancel') ) ]
