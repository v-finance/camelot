#  ============================================================================
#
#  Copyright (C) 2007-2013 Conceptive Engineering bvba. All rights reserved.
#  www.conceptive.be / info@conceptive.be
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
#  visit www.python-camelot.com or contact info@conceptive.be
#
#  This file is provided AS IS with NO WARRANTY OF ANY KIND, INCLUDING THE
#  WARRANTY OF DESIGN, MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE.
#
#  For use of this library in commercial applications, please contact
#  info@conceptive.be
#
#  ============================================================================

"""Set of classes to store authentication and permissions
"""

import datetime
import threading

from sqlalchemy.types import Date, Unicode, DateTime, Integer
from sqlalchemy.schema import Column, ForeignKey
from sqlalchemy import orm

import camelot.types
from camelot.core.document import document_classes
from camelot.core.orm import Entity, Session, ManyToMany
from camelot.core.utils import ugettext_lazy as _
from camelot.admin.entity_admin import EntityAdmin
from camelot.view import forms
from camelot.view.controls import delegates

END_OF_TIMES = datetime.date( year = 2400, month = 12, day = 31 )

def end_of_times():
    return END_OF_TIMES

_current_authentication_ = threading.local()

def get_current_authentication( _obj = None ):
    """Get the currently logged in :class:'AuthenticationMechanism'"""
    global _current_authentication_
    if not hasattr( _current_authentication_, 'mechanism' ) \
        or not _current_authentication_.mechanism \
        or not orm.object_session( _current_authentication_.mechanism ):
            import getpass
            _current_authentication_.mechanism = AuthenticationMechanism.get_or_create( unicode( getpass.getuser(), encoding='utf-8', errors='ignore' ) )
    return _current_authentication_.mechanism

def clear_current_authentication():
    _current_authentication_.mechanism = None

def update_last_login( initial_group_name = None,
                       initial_group_roles = [] ):
    """Update the last login of the currently logged in user to now.  If there
    is no :class:`AuthenticationGroup` yet in the database, create one and add
    the user to it.  This can be used to bootstrap the authentication system
    and create an `admin` group and add the user to it.
    
    :param initial_group_name: The name of the authentication group that needs
        to be created if there is none yet.
    :param initial_group_roles: a :class:`list` with the roles for the initial
        group
    """
    authentication = get_current_authentication()
    session = orm.object_session( authentication )
    if session:
        authentication.last_login = datetime.datetime.now()
        if initial_group_name:
            group_count = session.query( AuthenticationGroup ).count()
            if group_count == 0:
                group = AuthenticationGroup( name = initial_group_name )
                for role in initial_group_roles:
                    setattr( group, role, True )
                group.members.append( authentication )
        session.flush()

#
# Enumeration for the roles in an application
#
roles = []

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

    def has_role( self, role_name ):
        """
        :param role_name: a string with the name of the role
        :return; `True` if the user is associated to this role, otherwise 
            `False`.
            
        """
        for group in self.groups:
            if getattr( group, role_name ) == True:
                return True
        return False
        
    def __unicode__( self ):
        return self.username
    
    class Admin( EntityAdmin ):
        verbose_name = _('Authentication mechanism')
        list_display = ['authentication_type', 'username', 'from_date', 'thru_date', 'last_login']

class AuthenticationGroup( Entity ):
    """A group of users (defined by their :class:`AuthenticationMechanism`).
    Different roles can be assigned to a group.
    """
    
    __tablename__ = 'authentication_group'
    
    name = Column( Unicode(256), nullable=False )
    members = ManyToMany( AuthenticationMechanism, 
                          tablename = 'authentication_group_member',
                          backref = 'groups' )
    
    def __getattr__( self, name ):
        for role_id, role_name in roles:
            if role_name == name:
                for role in self.roles:
                    if role.role_id == role_id:
                        return True
                return False
        raise AttributeError( name )
                
    def __setattr__( self, name, value ):
        for role_id, role_name in roles:
            if role_name == name:
                current_value = getattr( self, name )
                if value==True and current_value==False:
                    group_role = AuthenticationGroupRole( role_id = role_id )
                    self.roles.append( group_role )
                elif value==False and current_value==True:
                    for group_role in self.roles:
                        if group_role.role_id == role_id:
                            self.roles.remove( group_role )
                            break
                break
        return super( AuthenticationGroup, self ).__setattr__( name, value )
        
    def __unicode__( self ):
        return self.name or ''
    
    class Admin( EntityAdmin ):
        verbose_name = _('Authentication group')
        verbose_name_plural = _('Authenication groups')
        list_display = [ 'name' ]
        
        def get_form_display( self ):
            return forms.TabForm( [(_('Group'), ['name', 'members']),
                                   (_('Roles'), [role[1] for role in roles])
                                   ])
        
        def get_field_attributes( self, field_name ):
            fa = EntityAdmin.get_field_attributes( self, field_name )
            if field_name in [role[1] for role in roles]:
                fa['delegate'] = delegates.BoolDelegate
                fa['editable'] = True
            return fa
        
class AuthenticationGroupRole( Entity ):
    """Table with the different roles associated with an
    :class:`AuthenticationGroup`
    """
    
    __tablename__ = 'authentication_group_role'
    
    role_id = Column( camelot.types.PrimaryKey(), 
                      nullable = False,
                      primary_key = True)
    group_id = Column( camelot.types.PrimaryKey(), 
                       ForeignKey( 'authentication_group.id',
                                   onupdate = 'cascade',
                                   ondelete = 'cascade' ),
                       nullable = False,
                       primary_key = True )

AuthenticationGroup.roles = orm.relationship( AuthenticationGroupRole,
                                              cascade = 'all, delete, delete-orphan')

document_classes([AuthenticationGroup,
                  AuthenticationMechanism])
