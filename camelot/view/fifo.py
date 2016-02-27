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

"""Module containing the FIFO cache used in the collection proxy to store
the data that is passed between the model and the gui thread"""

from copy import copy

_fill = object()
_no_data = (None,None)

import six

class Fifo(object):
    """Fifo, is the actual cache containing a limited set of copies of row data
    so the data in Fifo, is always immediately accessible to the gui thread,
    with zero delay as you scroll down the table view, Fifo is filled and
    refilled with data queried from the database
    
    the cache can be queried either by the row number or by object represented 
    by the row data.
    """
    def __init__(self, max_entries):
        """:param max_entries: the maximum entries that will be stored in the
        cache, if more data is added, the oldest data gets removed"""
        self.max_entries = max_entries
        self.entities = []
        self.data_by_rows = dict()
        self.rows_by_entity = dict()
        
    def __unicode__(self):
        return u','.join(six.text_type(e) for e in self.entities)
    
    def __str__(self):
        return 'Fifo cache of %s rows'%(len(self.entities))
    
    def __len__(self):
        """The number of rows in the cache"""
        return len( self.entities )
    
    def rows(self):
        """
        :return: a interator of the row numbers for which this fifo
        had data
        """
        return six.iterkeys(self.data_by_rows)
    
    def shallow_copy(self, max_entries):
        """Copy the cache without the actual data but with the references
        to which object is stored in which row"""
        new_fifo = Fifo(max_entries)
        new_fifo.entities = copy( self.entities )
        # None is to distinguish between a list of data and no data
        new_fifo.data_by_rows = dict( (row, (entity,None)) for (row, (entity, value)) in six.iteritems(self.data_by_rows) )
        new_fifo.rows_by_entity = copy( self.rows_by_entity )
        return new_fifo
        
    def add_data(self, row, entity, value):
        """The entity might already be on another row, and this row
        might already contain an entity
        
        :return: a :class:`set` with all the changed columns in the row
        
        """
        old_value = self.delete_by_entity(entity)[1]
        self.data_by_rows[row] = (entity, value)
        self.rows_by_entity[entity] = row
        self.entities.append(entity)
        if len(self.entities)>self.max_entries:
            entity = self.entities.pop(0)
            self.delete_by_entity(entity)
        if old_value is None:
            # there was no old data, so everything has changed
            return set( range( len( value ) ) )
        values = six.moves.zip_longest( value, old_value or [], fillvalue = _fill )
        return set( i for i,(new,old) in enumerate( values ) if new != old )
      
    def delete_by_row(self, row):
        """Remove the data and the reference to the object at row"""
        (entity, _value_) = self.data_by_rows[row]
        del self.data_by_rows[row]
        del self.rows_by_entity[entity] 
        return row
    
    def delete_by_entity(self, entity):
        """Remove everything in the cache related to an entity instance
        returns the row at which the data was stored if the data was in the
        cache, return None otherwise"""
        row, data = None, _no_data
        try:
            row = self.rows_by_entity[entity]
            data = self.data_by_rows.get( row, _no_data )
            del self.data_by_rows[row]
            del self.rows_by_entity[entity]      
        except KeyError:
            pass
        try:
            self.entities.remove(entity)
        except ValueError:
            pass
        return row, data[1] 
    
    def has_data_at_row(self, row):
        """:return: True if there is data in the cache for the row, False if 
        there isn't"""
        try:
            data = self.get_data_at_row( row )
            if data is not None:
                return True
        except KeyError:
            pass
        return False
    
    def get_data_at_row(self, row):
        """:return: the data at row"""
        return self.data_by_rows[row][1]
    
    def get_row_by_entity(self, entity):
        """:return: the row at which an entity is stored"""
        return self.rows_by_entity[entity]
    
    def get_entity_at_row(self, row):
        """:return: the entity that is stored at a row"""
        return self.data_by_rows[row][0]



