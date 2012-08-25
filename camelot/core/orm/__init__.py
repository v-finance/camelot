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

import contextlib
import logging

LOGGER = logging.getLogger('camelot.core.orm')

from camelot.core.sql import metadata
from sqlalchemy import orm, event
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import scoped_session, sessionmaker, mapper

from . options import ( using_options, using_table_options,
                        using_mapper_options, options_defaults,
                        using_options_defaults )
from . fields import has_field, Field
from . relationships import ( belongs_to, has_one, has_many,
                              has_and_belongs_to_many, 
                              ManyToOne, OneToOne, OneToMany, ManyToMany )
from . properties import has_property, GenericProperty, ColumnProperty

#
# Singleton session factory, to be used when a session is needed
#
Session = scoped_session( sessionmaker( autoflush = False,
                                        autocommit = True,
                                        expire_on_commit = False ) )

#
# Default registry for subclasses of Entity that have been mapped
#

class EntityCollection( dict ):
    
    __name__ = 'EntityCollection'
    
    pass

entities = EntityCollection()

#
# There are 3 base classes that each act in a different way
#
# * ClassMutator : DSL like statements that modify the Entity at definition
#   time
#
# * Property : modify an Entity at construction time, in several phases, before
#   and after mapper and table creation.
#

def setup_all( create_tables=False, *args, **kwargs ):
    """Create all tables that are registered in the metadata
    """
    if create_tables:
        metadata.create_all( *args, **kwargs )

from . entity import EntityBase, EntityMeta

@event.listens_for( mapper, 'after_configured' )
def process_deferred_properties( class_registry = entities ):
    """After all mappers have been configured, process the Deferred Propoperties.
    This function is called automatically for the default class_registry.
    """
    LOGGER.debug( 'process deferred properties' )
    
    for cls in class_registry.values():
        mapper = orm.class_mapper( cls )
        # set some convenience attributes to the Entity
        setattr( cls, 'table', mapper.local_table )
        setattr( cls, 'query', Session().query( cls ) )
                
    for method_name in ( 'create_non_pk_cols', 
                         'append_constraints',
                         'create_properties' ):
        for cls in class_registry.values():
            method = getattr( cls._descriptor, method_name )
            method()

Entity = declarative_base( cls = EntityBase, 
                           metadata = metadata,
                           metaclass = EntityMeta,
                           class_registry = entities,
                           constructor = None,
                           name = 'Entity' )

@contextlib.contextmanager
def SessionTransaction( session = None, 
                        subtransactions = False, 
                        nested = False ):
    """Context manager to run a block within a transaction and roll back if an 
    exception is raised.
    
    :param session: a :class:`sqlalchemy.orm.session.Session` object, if `None`
        is given, the default session is used.
    """
    from camelot.core.orm import Session
    if session == None:
        session = Session()
    transaction = session.begin( subtransactions = subtransactions, 
                                 nested = nested )
    try:
        yield transaction
        session.commit()
    except:
        session.rollback()
        raise    

__all__ = [ obj.__name__  for obj in [ Entity, EntityBase, EntityMeta, EntityCollection,
            entities,
            Field, has_field,
            has_property, GenericProperty, ColumnProperty,
            belongs_to, has_one, has_many, has_and_belongs_to_many,
            ManyToOne, OneToOne, OneToMany, ManyToMany,
            using_options, using_table_options, using_mapper_options,
            options_defaults, using_options_defaults,
            setup_all
            ] ] + ['Session']