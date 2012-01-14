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

"""Module containing the FIFO cache used in the collection proxy to store
the data that is passed between the model and the gui thread"""

from copy import copy

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
        return u','.join(unicode(e) for e in self.entities)
    
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
        return self.data_by_rows.keys()
    
    def shallow_copy(self, max_entries):
        """Copy the cache without the actual data but with the references
        to which object is stored in which row"""
        new_fifo = Fifo(max_entries)
        new_fifo.entities = copy( self.entities )
        # None is to distinguish between a list of data and no data
        new_fifo.data_by_rows = dict( (row, (entity,None)) for (row, (entity, value)) in self.data_by_rows.items() )
        new_fifo.rows_by_entity = copy( self.rows_by_entity )
        return new_fifo
        
    def add_data(self, row, entity, value):
        """The entity might already be on another row, and this row
        might already contain an entity"""
#        try:
#            previous_entity = self.get_entity_at_row(row)
#            self.delete_by_entity(previous_entity)
#        except KeyError:
#            pass
        self.delete_by_entity(entity)
        self.data_by_rows[row] = (entity, value)
        self.rows_by_entity[entity] = row
        self.entities.append(entity)
        if len(self.entities)>self.max_entries:
            entity = self.entities.pop(0)
            self.delete_by_entity(entity)
      
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
        row = None
        try:
            row = self.rows_by_entity[entity]
            del self.data_by_rows[row]
            del self.rows_by_entity[entity]      
        except KeyError:
            pass
        try:
            self.entities.remove(entity)
        except ValueError:
            pass
        return row    
    
    def has_data_at_row(self, row):
        """:return: True if there is data in the cache for the row, False if 
        there isn't"""
        try:
            data = self.get_data_at_row( row )
            if data != None:
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

