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

"""This module complements the sqlalchemy orm module, it contains the global
`Session` factory to create `session` objects.  Whenever a `session`
is needed it can be constructed with a call of `Session` ::
    
    session = Session
        
when using Elixir, Elixir needs to be told to use this session factory ::
    
    elixir.session = Session

when using Declarative, this module contains an `Entity` class that can
be used as a `declarative_base` and has some classes that mimic Elixir
behavior
"""

import functools
import logging

LOGGER = logging.getLogger('camelot.core.orm')

from camelot.core.sql import metadata
from sqlalchemy import orm, event
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.ext.declarative.clsregistry import ( _ModuleMarker,
                                                     _MultipleClassMarker )
from sqlalchemy.orm import scoped_session, sessionmaker, mapper

#
# Singleton session factory, to be used when a session is needed
#
Session = scoped_session( sessionmaker( autoflush = False,
                                        autocommit = True,
                                        expire_on_commit = False ) )

from . options import using_options
from . fields import has_field, Field
from . relationships import ( belongs_to, has_one, has_many,
                              has_and_belongs_to_many, 
                              ManyToOne, OneToOne, OneToMany, ManyToMany )
from . properties import has_property, GenericProperty, ColumnProperty

#
# Default registry for subclasses of Entity that have been mapped
#

class EntityCollection( dict ):

    __name__ = 'EntityCollection'

entities = EntityCollection()

#
# There are 2 base classes that each act in a different way
#
# * ClassMutator : DSL like statements that modify the Entity at definition
#   time
#
# * EntityBuilder : modify an Entity at construction time, in several phases, 
#   before and after mapper and table creation.
#

import six

from . entity import EntityBase, EntityMeta

@event.listens_for( mapper, 'after_configured' )
def process_deferred_properties( class_registry = entities ):
    """After all mappers have been configured, process the Deferred Properties.
    This function is called automatically for the default class_registry.
    """
    LOGGER.debug( 'process deferred properties' )
    descriptors = list()
    for cls in six.itervalues(class_registry):
        if isinstance( cls, ( _ModuleMarker, _MultipleClassMarker ) ):
            continue
        descriptor = getattr(cls, '_descriptor')
        if descriptor.processed == True:
            # because orm.class_mapper will trigger the 'after_configured' event,
            # there might be a recursive call of this function, if this function
            # was called by the application code, and not by the event.
            continue
        descriptors.append( (descriptor.counter, descriptor) )
        descriptor.processed = True
    descriptors.sort()

    for method_name in ( 'create_non_pk_cols',
                         'create_tables',
                         'append_constraints',
                         'create_properties',
                         'finalize', ):
        for counter, descriptor in descriptors:
            method = getattr(descriptor, method_name)
            method()


def setup_all( create_tables=False, *args, **kwargs ):
    """Create all tables that are registered in the metadata
    """
    process_deferred_properties()
    if create_tables:
        metadata.create_all( *args, **kwargs )
        
Entity = declarative_base( cls = EntityBase, 
                           metadata = metadata,
                           metaclass = EntityMeta,
                           class_registry = entities,
                           constructor = None,
                           name = 'Entity' )

def transaction( original_function ):
    """Decorator to make methods transactional with regard to the session
    of the object on which they are called"""
    
    @functools.wraps( original_function )
    def decorated_function( self, *args, **kwargs ):
        session = orm.object_session( self )
        with session.begin():
            return original_function( self, *args, **kwargs )
    
    return decorated_function

__all__ = [ obj.__name__  for obj in [ Entity, EntityBase, EntityMeta, 
            EntityCollection, Field, has_field,
            has_property, GenericProperty, ColumnProperty,
            belongs_to, has_one, has_many, has_and_belongs_to_many,
            ManyToOne, OneToOne, OneToMany, ManyToMany,
            using_options,
            setup_all, transaction
            ] ] + ['Session', 'entities']


