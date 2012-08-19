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

"""Classes to interface with the Memento model, which tracks modification
of changes.
"""

import collections
import datetime

from sqlalchemy import func, sql, orm

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
#
# lightweight data structure to present object changes to other parts of 
# Camelot
#
object_change = collections.namedtuple( 'object_change',
                                        ['id', 'type', 'at', 'by', 'changes'] )

class SqlMemento( object ):
    """Default Memento system, which uses :class:`camelot.model.memento.Memento`
    to track changes into a database table.  The tracking of changes happens 
    outside the session, but using the same connection as the session.
    
    Reimplement this class to create a custom system to track changes.
    
    This Memento system can only track objects with an integer primary key.
    That means the `primary_key` tuple can only contain a single integer
    value.
    """

    def _get_memento_table( self ):
        """:return: the `Table` to which to store the changes"""
        from camelot.model.memento import Memento
        return orm.class_mapper( Memento ).mapped_table

    def _get_authentication_id( self ):
        """:return: the id to store in the memento table"""
        from camelot.model.authentication import get_current_authentication
        return get_current_authentication().id
    
    def register_changes( self, 
                          memento_changes ):
        """Create rows in the memento table
        :param memento_changes: an iterator over `memento_change` tuples that 
        need to be stored in the memento table.
        """
        rows = list()
        authentication_id = self._get_authentication_id()
        for m in memento_changes:
            if len( m.primary_key ) == 1:
                rows.append( { 'model':m.model,
                               'primary_key':m.primary_key[0],
                               'previous_attributes':m.previous_attributes,
                               'memento_type':m.memento_type,
                               'authentication_id':authentication_id,
                                } )
        if len( rows ):
            table = self._get_memento_table()
            clause = table.insert( creation_date = func.current_timestamp() )
            clause.execute( rows )
    
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
        table = self._get_memento_table()
        c = table.c
        query = sql.select( [ c.id,
                              c.creation_date,
                              c.authentication_id,
                              c.memento_type,
                              c.previous_attributes ] )
        query = query.where( sql.and_( c.model == model,
                                       c.primary_key == primary_key[0] ) )
        query = query.order_by( c.creation_date.desc() )
        for row in table.bind.execute( query ):
            yield object_change( id = row.id,
                                 type = row.memento_type,
                                 at = row.creation_date,
                                 by = row.authentication_id,
                                 changes = row.previous_attributes )
