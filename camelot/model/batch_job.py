"""
Classes to store the result of batch jobs to enable the user to
review or plan them
"""

from elixir.entity import Entity
from elixir.options import using_options
from elixir.fields import Field
import sqlalchemy.types
from elixir.relationships import ManyToOne

from camelot.core.utils import ugettext_lazy as _
from camelot.model import metadata
from camelot.view import filters
from camelot.admin.entity_admin import EntityAdmin
import camelot.types

import datetime

__metadata__ = metadata

class BatchJobType(Entity):
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
        
def hostname():
    import socket
    return socket.gethostname()
    
class BatchJob(Entity):
    using_options( tablename = 'batch_job', order_by=['-date'] )
    date    = Field(sqlalchemy.types.DateTime, required=True, default=datetime.datetime.now)
    host    = Field(sqlalchemy.types.Unicode(256), required=True, default=hostname)
    type    = ManyToOne('BatchJobType', required=True, ondelete = 'restrict', onupdate = 'cascade')
    status  = Field(camelot.types.Enumeration([(-2, 'planned'), (-1, 'running'), (0, 'success'), (1,'warnings'), (2,'errors')]), required=True, default='planned' )
    message = Field(camelot.types.RichText())
    
    def add_exception_to_message(self, exception):
        import traceback, cStringIO
        sio = cStringIO.StringIO()
        traceback.print_exc(file=sio)
        traceback_print = sio.getvalue()
        sio.close()
        self.message = (self.message or '') + '<br/>' + unicode(exception) + '<br/>' +  traceback_print.replace('\n', '<br/>')
        
    def add_strings_to_message(self, strings):
        """:param strings: a list or generator of strings"""
        self.message = (self.message or '') + '<br/>'.join(list(strings))
        
    class Admin(EntityAdmin):
        verbose_name = _('Batch job')
        list_display = ['date', 'host', 'type', 'status']
        list_filter = ['status', filters.ComboBoxFilter('host')]
        form_display = list_display + ['message']