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

"""Set of classes to store authentication and permissions
"""
import base64
import datetime
import threading

import six

from sqlalchemy import types

from sqlalchemy.schema import Column, ForeignKey
from sqlalchemy import orm

import camelot.types
from ..core.qt import QtCore, QtGui
from camelot.core.orm import Entity, Session, ManyToMany
from camelot.core.utils import ugettext_lazy as _
from camelot.admin.entity_admin import EntityAdmin
from camelot.view import forms
from camelot.view.controls import delegates

END_OF_TIMES = datetime.date( year = 2400, month = 12, day = 31 )

#
# Enumeration of the types of authentication supported
#
authentication_types = [ (1, 'operating_system'),
                         (2, 'database') ]

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
            if six.PY3:
                user = getpass.getuser()
            else:
                user = six.text_type( getpass.getuser(), encoding='utf-8', errors='ignore' )
            _current_authentication_.mechanism = AuthenticationMechanism.get_or_create( user )
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
    
    authentication_type = Column( camelot.types.Enumeration(authentication_types),
                                  nullable = False, 
                                  index = True , 
                                  default = authentication_types[0][1] )
    username = Column( types.Unicode( 40 ), nullable = False, index = True, unique = True )
    password = Column( types.Unicode( 200 ), nullable = True, index = False, default = None )
    from_date = Column( types.Date(), default = datetime.date.today, nullable = False, index = True )
    thru_date = Column( types.Date(), default = end_of_times, nullable = False, index = True )
    last_login = Column( types.DateTime() )
    representation = Column( types.Text(), nullable=True )

    @classmethod
    def get_or_create( cls, username ):
        session = Session()
        authentication = session.query( cls ).filter_by( username = username ).first()
        if not authentication:
            authentication = cls( username = username )
            session.add( authentication )
            session.flush()
        return authentication

    def get_representation(self):
        """
        :return: a :class:`QtGui.QImage` object with the avatar of the user,
            or `None`.
        """
        if self.representation is None:
            return self.representation
        return QtGui.QImage.fromData(base64.b64decode(self.representation))
    
    def set_representation(self, image):
        """
        :param image: a :class:`QtGui.QImage` object with the avatar of the user,
            or `None`.
        """
        if image is None:
            self.representation=None
        qbyte_array = QtCore.QByteArray()
        qbuffer = QtCore.QBuffer( qbyte_array )
        image.save( qbuffer, 'PNG' )
        self.representation=base64.b64encode(qbyte_array.data())
        
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
        
    def __str__( self ):
        return self.username
    
    class Admin( EntityAdmin ):
        verbose_name = _('Authentication mechanism')
        list_display = ['authentication_type', 'username', 'from_date', 'thru_date', 'last_login']

class AuthenticationGroup( Entity ):
    """A group of users (defined by their :class:`AuthenticationMechanism`).
    Different roles can be assigned to a group.
    """
    
    __tablename__ = 'authentication_group'
    
    name = Column( types.Unicode(256), nullable=False )
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
        verbose_name_plural = _('Authentication groups')
        list_display = [ 'name' ]
        form_state = 'right'
        
        def get_form_display( self ):
            return forms.TabForm( [(_('Group'), ['name', 'members']),
                                   (_('Authentication roles'), [role[1] for role in roles])
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
                      primary_key = True,
                      autoincrement = False )
    group_id = Column( camelot.types.PrimaryKey(), 
                       ForeignKey( 'authentication_group.id',
                                   onupdate = 'cascade',
                                   ondelete = 'cascade' ),
                       nullable = False,
                       primary_key = True,
                       autoincrement = False )

AuthenticationGroup.roles = orm.relationship( AuthenticationGroupRole,
                                              cascade = 'all, delete, delete-orphan')
