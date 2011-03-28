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
from elixir.entity import Entity
from elixir.options import using_options
from elixir.fields import Field
from sqlalchemy.types import Unicode, INT, DateTime, PickleType
from elixir.relationships import ManyToOne

from camelot.model import metadata
from camelot.view import filters

"""Set of classes to keep track of changes to objects and
be able to restore their state
"""

__metadata__ = metadata

from camelot.core.utils import ugettext_lazy as _
from camelot.admin.entity_admin import EntityAdmin
import datetime


class Memento( Entity ):
    """Keeps information on the previous state of objects, to keep track
    of changes and enable restore to that previous state"""
    using_options( tablename = 'memento' )
    model = Field( Unicode( 256 ), index = True, required = True )
    primary_key = Field( INT(), index = True, required = True )
    creation_date = Field( DateTime(), default = datetime.datetime.now )
    authentication = ManyToOne( 'AuthenticationMechanism',
                               required = True,
                               ondelete = 'restrict',
                               onupdate = 'cascade' )
    description = property( lambda self:'Change' )

    class Admin( EntityAdmin ):
        verbose_name = _( 'History' )
        verbose_name_plural = _( 'History' )
        list_display = ['creation_date',
                        'authentication',
                        'model',
                        'primary_key',
                        'description']
        list_filter = [filters.ComboBoxFilter('model')]


class BeforeUpdate( Memento ):
    """The state of the object before an update took place"""
    using_options( inheritance = 'multi', tablename = 'memento_update', )
    previous_attributes = Field( PickleType() )

    @property
    def description( self ):
        if self.previous_attributes:
            return u'Update %s when previous value was %s' % ( 
                ','.join( self.previous_attributes.keys() ),
                ','.join( unicode( v ) for v in self.previous_attributes.values() ) )

    class Admin( Memento.Admin ):
        verbose_name = _('Update')
        verbose_name_plural = _('Updates')

class BeforeDelete( Memento ):
    """The state of the object before it is deleted"""
    using_options( inheritance = 'multi', tablename = 'memento_delete', )
    previous_attributes = Field( PickleType() )

    @property
    def description( self ):
        return 'Delete'

    class Admin( Memento.Admin ):
        verbose_name = _('Delete')
        verbose_name_plural = _('Deletes')

class Create( Memento ):
    """Marks the creation of an object"""
    using_options( inheritance = 'multi', tablename = 'memento_create', )

    @property
    def description( self ):
        return 'Create'

    class Admin( Memento.Admin ):
        verbose_name = _('Create')
        verbose_name_plural = _('Creates')


