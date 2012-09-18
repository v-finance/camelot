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

"""Set of classes to store authentication and permissions
"""

import datetime
import threading

from sqlalchemy.types import Date, Unicode, DateTime
from sqlalchemy.schema import Column
from sqlalchemy import orm

import camelot.types
from camelot.core.orm import Entity, Session
from camelot.core.utils import ugettext_lazy as _
from camelot.admin.entity_admin import EntityAdmin

def end_of_times():
    return datetime.date( year = 2400, month = 12, day = 31 )

_current_authentication_ = threading.local()

def get_current_authentication( _obj = None ):
    """Get the currently logged in :class:'AuthenticationMechanism'"""
    global _current_authentication_
    if not hasattr( _current_authentication_, 'mechanism' ) or not _current_authentication_.mechanism:
        import getpass
        _current_authentication_.mechanism = AuthenticationMechanism.get_or_create( unicode( getpass.getuser(), encoding='utf-8', errors='ignore' ) )
    return _current_authentication_.mechanism

def clear_current_authentication():
    _current_authentication_.mechanism = None

def update_last_login():
    """Update the last login of the current person to now"""
    authentication = get_current_authentication()
    authentication.last_login = datetime.datetime.now()
    session = orm.object_session( authentication )
    if session:
        session.flush()

class AuthenticationMechanism( Entity ):
    
    __tablename__ = 'authentication_mechanism'
    
    authentication_type = Column( camelot.types.Enumeration( [ (1, 'operating_system'),
                                                               (2, 'database') ] ),
                                  nullable = False, 
                                  index = True , 
                                  default = 'operating_system' )
    username = Column( Unicode( 40 ), nullable = False, index = True, unique = True )
    password = Column( Unicode( 200 ), nullable = True, index = False, default = None )
    from_date = Column( Date(), default = datetime.date.today, nullable = False, index = True )
    thru_date = Column( Date(), default = end_of_times, nullable = False, index = True )
    last_login = Column( DateTime() )

    @classmethod
    def get_or_create( cls, username ):
        session = Session()
        authentication = session.query( cls ).filter_by( username = username ).first()
        if not authentication:
            authentication = cls( username = username )
            session.add( authentication )
            session.flush()
        return authentication

    def __unicode__( self ):
        return self.username
    
    class Admin( EntityAdmin ):
        verbose_name = _('Authentication mechanism')
        list_display = ['authentication_type', 'username', 'from_date', 'thru_date', 'last_login']
