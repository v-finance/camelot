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

import collections

_fill = object()



class ValueCache(object):
    """
    The ValueCache keeps track of the values of object attributes.

    This cache is used to track which values have changed and for which
    an update of the gui is needed.

    Fifo, is the actual cache containing a limited set of copies of row data
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
        self.data_by_rows = collections.defaultdict(dict)
        self.rows_by_entity = collections.OrderedDict()
    
    def __repr__(self):
        return u'ValueCache({0.max_entries})'.format(self)
    
    def __len__(self):
        """The number of rows in the cache"""
        return len(self.rows_by_entity)
    
    def rows(self):
        """
        :return: a interator of the row numbers for which this fifo
        had data
        """
        return self.data_by_rows.keys()

    def add_data(self, row, entity, values):
        """The entity might already be on another row, and this row
        might already contain an entity
        
        :return: a :class:`set` with all the changed columns in the row
        
        """
        old_value = self.delete_by_entity(entity)[1]
        if old_value is None:
            # there was no old data, so everything has changed
            changed_columns = set(values.keys())
            new_values = values
        else:
            changed_columns = set(col for col, value in values.items() if value != old_value.get(col, _fill))
            new_values = old_value
            new_values.update(values)
        self.data_by_rows[row] = new_values
        self.rows_by_entity[entity] = row
        if len(self.rows_by_entity)>self.max_entries:
            entity, _row = self.rows_by_entity.popitem(last=False)
            self.delete_by_entity(entity)
        return changed_columns

    def get_data(self, row):
        """
        The return value of this function should not be changed.

        :return: a `dict` with the cached data in a row, the keys are the columns
        """
        return self.data_by_rows.get(row, {})

    def delete_by_entity(self, entity):
        """Remove everything in the cache related to an entity instance
        returns the row at which the data was stored if the data was in the
        cache, return None otherwise"""
        try:
            row = self.rows_by_entity[entity]
            value = self.data_by_rows.get(row, None)
            del self.data_by_rows[row]
            del self.rows_by_entity[entity]      
        except KeyError:
            return None, None
        return row, value

