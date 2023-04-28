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

"""Classes to interface with the Memento model, which tracks modification
of changes.

This module contains the `memento_types` variable, which is a list of different
types of changes that can be tracked.  Add elements to this list to add custom
tracking of changes
"""

import collections
import datetime
import logging

from sqlalchemy import sql, orm, exc




from camelot.core.utils import ugettext

memento_types = [ (1, 'before_update'),
                  (2, 'before_delete'),
                  (3, 'create')
                  ]
                                                        
LOGGER = logging.getLogger( 'camelot.core.memento' )
            
#
# lightweight data structure to present object changes to the memento
# system
#
# :param model: a string with the name of the model
# :param primary_key: a tuple with the primary key of the changed object
# :param previous_attributes: a dict with the names and the values of
#     the attributes of the object before they were changed.
# :param memento_type: a string with the type of memento
#
memento_change = collections.namedtuple( 'memento_change',
                                         [ 'model', 
                                           'primary_key', 
                                           'previous_attributes', 
                                           'memento_type' ] )

class Change( object ):
    
    def __init__( self, memento, row ):
        self.id = row.id
        self.type = row.memento_type
        self.at = row.at
        self.by = row.by
        self.changes = None
        if row.previous_attributes:
            self.changes = u', '.join( ugettext('%s was %s')%(k,str(v)) for k,v in row.previous_attributes.items() )
        self.memento_type = row.memento_type
        
class SqlMemento( object ):
    """Default Memento system, which uses :class:`camelot.model.memento.Memento`
    to track changes into a database table.  The tracking of changes happens 
    outside the session, but using the same connection as the session.
    
    Reimplement this class to create a custom system to track changes.
    
    This Memento system can only track objects with an integer primary key.
    That means the `primary_key` tuple can only contain a single integer
    value.
    
    :param memento_types: a list with all types of changes that can be tracked
        and their identifier used to store them
    """

    def __init__( self, memento_types = memento_types ):
        self.memento_types = memento_types
        self.memento_type_by_id = dict( (i,t) for i,t in memento_types )
        self.memento_id_by_type = dict( (t,i) for i,t in memento_types )
        
    def _get_memento_table( self ):
        """:return: the :class:`sqlalchemy:sqlalchemy.schema.Table` to which to 
        store the changes"""
        from camelot.model.memento import Memento
        return orm.class_mapper( Memento ).mapped_table
    
    def _get_authentication_table( self ):
        """:return: the :class:`sqlalchemy:sqlalchemy.schema.Table` in 
        which the authentication id and username are stored"""
        from camelot.model.authentication import AuthenticationMechanism
        return orm.class_mapper( AuthenticationMechanism ).mapped_table    

    def _get_authentication_id( self ):
        """:return: the id to store in the memento table"""
        from camelot.model.authentication import AuthenticationMechanism
        authentication = AuthenticationMechanism.get_current_authentication()
        return authentication.authentication_mechanism_id
    
    def register_changes( self, 
                          memento_changes ):
        """Create rows in the memento table
        :param memento_changes: an iterator over `memento_change` tuples that 
        need to be stored in the memento table.
        """
        from camelot.core.orm import Session
        from camelot.model.memento import Memento
        authentication_id = self._get_authentication_id()
        connection = Session().connection(mapper=orm.class_mapper( Memento ))
        session = orm.Session(bind=connection, autocommit=True)
        mementos = []
        for m in memento_changes:
            if len( m.primary_key ) == 1:
                mementos.append( Memento( model=m.model,
                                          primary_key=m.primary_key[0],
                                          previous_attributes=m.previous_attributes,
                                          memento_type=self.memento_id_by_type.get(m.memento_type, None),
                                          authentication_id=authentication_id,
                                          _session=session ) )
        if len( mementos ):
            try:
                session.flush()
            except exc.DatabaseError as e:
                LOGGER.error( 'Programming Error, could not flush history', exc_info = e )                
    
    def get_changes( self, 
                     model, 
                     primary_key, 
                     current_attributes,
                     from_datetime = datetime.datetime(2000,1,1),
                     depth = {} ):
        """Query the memento system for changes made to an object.
        
        :param model: a string with the name of the model
        :param primary_key: a tuple with the primary key of the changed object
        :param current_attributes: a `dict` with the current state of the 
            attributes of the object, this is used to reconstruct the changes.
        :param from_datetime: the `datetime` upto which the changes should be
            reconstructed.
        :param depth: reserved for future usage to query the history of
            object trees.
        :return: generator of `change_object` tuples in reverse order, meaning the
            last change will be first generated.
        """
        memento_c = self._get_memento_table().columns
        authentication_table = self._get_authentication_table()
        authentication_c = authentication_table.columns
        authentication_query = sql.select( [authentication_c.username], 
                                           authentication_c.id == memento_c.authentication_id )
        query = sql.select( [ memento_c.id.label('id'),
                              memento_c.creation_date.label('at'),
                              authentication_query.as_scalar().label('by'),
                              memento_c.memento_type.label('memento_type'),
                              memento_c.previous_attributes ] )
        query = query.where( sql.and_( memento_c.model == model,
                                       memento_c.primary_key == primary_key[0] ) )
        query = query.order_by( memento_c.creation_date.desc() )
        for row in authentication_table.bind.execute( query ):
            yield Change( self, row )


