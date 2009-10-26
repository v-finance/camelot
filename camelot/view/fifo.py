#  ============================================================================
#
#  Copyright (C) 2007-2008 Conceptive Engineering bvba. All rights reserved.
#  www.conceptive.be / project-camelot@conceptive.be
#
#  This file is part of the Camelot Library.
#
#  This file may be used under the terms of the GNU General Public
#  License version 2.0 as published by the Free Software Foundation
#  and appearing in the file LICENSE.GPL included in the packaging of
#  this file.  Please review the following information to ensure GNU
#  General Public Licensing requirements will be met:
#  http://www.trolltech.com/products/qt/opensource.html
#
#  If you are unsure which license is appropriate for your use, please
#  review the following information:
#  http://www.trolltech.com/products/qt/licensing.html or contact
#  project-camelot@conceptive.be.
#
#  This file is provided AS IS with NO WARRANTY OF ANY KIND, INCLUDING THE
#  WARRANTY OF DESIGN, MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE.
#
#  For use of this library in commercial applications, please contact
#  project-camelot@conceptive.be
#
#  ============================================================================


class fifo(object):
    """fifo, is the actual cache containing a limited set of copies of row data
    so the data in fifo, is always immediately accessible to the gui thread,
    with zero delay as you scroll down the table view, fifo is filled and
    refilled with data queried from the database
    
    the cache can be queried either by the row number or by the primary key
    of the object represented by the row data.
    """
    def __init__(self, max_entries):
        self.max_entries = max_entries
        self.entities = []
        self.data_by_rows = dict()
        self.rows_by_entity = dict()
        
    def __unicode__(self):
        return u','.join(unicode(e) for e in self.entities)
    
    def add_data(self, row, entity, value):
        self.delete_by_entity(entity)
        self.data_by_rows[row] = (entity, value)
        self.rows_by_entity[entity] = row
        self.entities.append(entity)
        if len(self.entities)>self.max_entries:
            entity = self.entities.pop(0)
            row = self.rows_by_entity[entity]
            del self.data_by_rows[row]
            del self.rows_by_entity[entity]
      
    def delete_by_row(self, row):
        (entity, value) = self.data_by_rows[row]
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
    
    def get_data_at_row(self, row):
        return self.data_by_rows[row][1]
    
    def get_row_by_entity(self, entity):
        return self.rows_by_entity[entity]
    
    def get_entity_at_row(self, row):
        return self.data_by_rows[row][0]
