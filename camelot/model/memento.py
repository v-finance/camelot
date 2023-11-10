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

"""The ORM part of the classes that store the change history of objects to
the database.  The table defined here is used in :mod:`camelot.core.memento` 
to store the changes.

To prevent this table to be used to store changes, overwrite the 
:meth:`camelot.admin.application_admin.ApplicationAdmin.get_memento` method
the custom `ApplicationAdmin`.
"""

import datetime



from sqlalchemy import schema, orm
from sqlalchemy.types import Unicode, Integer, DateTime, PickleType

from camelot.admin.action import list_filter
from camelot.admin.entity_admin import EntityAdmin
from camelot.admin.object_admin import ObjectAdmin
from camelot.admin.not_editable_admin import not_editable_admin
from camelot.core.exception import UserException
from camelot.core.orm import Entity
from camelot.core.utils import ugettext_lazy as _
from camelot.view.controls import delegates
from camelot.types import PrimaryKey

from .authentication import AuthenticationMechanism

class PreviousAttribute( object ):
    """Helper class to display previous attributes"""

    __types__ = None

    def __init__( self, attribute, previous_value ):
        self.attribute = attribute
        self.previous_value = str( previous_value )
        
    class Admin( ObjectAdmin ):
        list_display = ['attribute', 'previous_value']
        

class Memento( Entity ):
    """Keeps information on the previous state of objects, to keep track
    of changes and enable restore to that previous state"""
    
    __tablename__ = 'memento'
    
    model = schema.Column( Unicode( 256 ), index = True, nullable = False )
    primary_key = schema.Column(PrimaryKey(), index=True, nullable=False)
    creation_date = schema.Column( DateTime(), default = datetime.datetime.now )
    authentication_id = schema.Column(Integer(), schema.ForeignKey(AuthenticationMechanism.id, ondelete='restrict', onupdate='cascade'),
                                      nullable=False, index=True)
    authentication = orm.relationship(AuthenticationMechanism)
    memento_type = schema.Column( Integer, 
                                  nullable = False,
                                  index = True )    
    previous_attributes = orm.deferred( schema.Column( PickleType() ) )

    __entity_args__ = {
        'editable': False
    }
    
    @property
    def previous( self ):
        previous = self.previous_attributes
        if previous:
            return [PreviousAttribute(k,v) for k,v in previous.items()]
        return []

    def __str__(self):
        if self.model is not None:
            return self.model
        return ''

class MementoAdmin( EntityAdmin ):

    verbose_name = _( 'History' )
    verbose_name_plural = _( 'History' )

    list_display = ['creation_date', 'authentication', 'model',
                    'primary_key', ]
    form_display = list_display + ['previous']
    list_filter = [list_filter.ComboBoxFilter(Memento.model)]
    field_attributes = {'previous':{'target':PreviousAttribute,
                                    'delegate':delegates.One2ManyDelegate,
                                    'actions': [],
                                    'python_type':list}
                        }

    def add(self, obj):
        raise UserException(_('Not Authorized'))

    def delete(self, obj):
        raise UserException(_('Not Authorized'))

    def copy(self, obj, new_obj=None):
        raise UserException(_('Not Authorized'))

Memento.Admin = not_editable_admin(MementoAdmin)
