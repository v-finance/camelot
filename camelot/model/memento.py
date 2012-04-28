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

"""Set of classes to keep track of changes to objects and be able to restore 
their state
"""

import datetime

from sqlalchemy.types import Unicode, INT, DateTime, PickleType

from camelot.admin.entity_admin import EntityAdmin
from camelot.core.orm import Entity, using_options, Field, ManyToOne
from camelot.admin.not_editable_admin import not_editable_admin
from camelot.core.sql import metadata
from camelot.core.utils import ugettext_lazy as _
import camelot.types
from camelot.view import filters

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
    memento_type = Field( camelot.types.Enumeration( [ (1, 'before_update'),
                                                       (2, 'before_delete'),
                                                       (3, 'create') ], 
                                                     required = True,
                                                     index = True ) )
    previous_attributes = Field( PickleType(), deferred = True )
    
    @property
    def description( self ):
        if self.memento_type in ('before_update', 'before_delete'):
            return u', '.join( [ u'%s : %s'%( key, unicode( value ) ) for key, value in  self.previous_attributes.items() ] )

    class Admin( EntityAdmin ):
        verbose_name = _( 'History' )
        verbose_name_plural = _( 'History' )
        list_display = ['creation_date', 'authentication', 'model',
                        'primary_key', 'memento_type',]
        form_display = list_display + ['description']
        list_filter = [filters.ComboBoxFilter('model'),
                       'memento_type']
        
    Admin = not_editable_admin( Admin )
