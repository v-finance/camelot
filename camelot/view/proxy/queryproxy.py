#  ============================================================================
#
#  Copyright (C) 2007-2010 Conceptive Engineering bvba. All rights reserved.
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

"""Proxies representing the results of a query"""

import logging
logger = logging.getLogger('camelot.view.proxy.queryproxy')

from collection_proxy import CollectionProxy, strip_data_from_object
from camelot.view.model_thread import model_function, gui_function, post


class QueryTableProxy(CollectionProxy):
    """The QueryTableProxy contains a limited copy of the data in the Elixir
    model, which is fetched from the database to be used as the model for a
    QTableView
    """

    def __init__(self, admin, query_getter, columns_getter,
                 max_number_of_rows=10, edits=None):
        """@param query_getter: a model_thread function that returns a query, can be None at construction time and set later"""
        logger.debug('initialize query table')
        self._query_getter = query_getter
        self._sort_decorator = None
        #rows appended to the table which have not yet been flushed to the
        #database, and as such cannot be a result of the query
        self._appended_rows = []
        super(QueryTableProxy, self).__init__(admin, lambda: [],
                                              columns_getter, max_number_of_rows=max_number_of_rows, edits=None)

#    def default_sort_decorator(self):
#        """Create a function that sorts a query, by default we sort a query by the
#        primary keys because we always want a unique ordering of the results, eg,
#        2 consecutive results should have the same order.  This is not necessary the
#        case when the query is not sorted, which will result to flicker on the screen.
#        """
#        #
#        # _foreign_keys is for sqla pre 0.6.4
#        # 
#        if hasattr(property, '_foreign_keys'):
#            class_attribute = list(property._foreign_keys)[0]
#        else:                             
#            class_attribute = list(property._calculated_foreign_keys)[0]         
        
    def get_query_getter(self):
        if not self._sort_decorator or self._query_getter==None:
            return self._query_getter
        else:
            
            def sorted_query_getter():
                return self._sort_decorator(self._query_getter())
            
            return sorted_query_getter
    
    @model_function
    def _clean_appended_rows(self):
        """Remove those rows from appended rows that have been flushed"""
        flushed_rows = []
        for o in self._appended_rows:
            if o.id:
                flushed_rows.append(o)
        for o in flushed_rows:
            self._appended_rows.remove(o)

    @model_function
    def getRowCount(self):
        self._clean_appended_rows()
        if not self._query_getter:
            return 0
        return self.get_query_getter()().count() + len(self._appended_rows)

    @gui_function
    def setQuery(self, query_getter):
        """Set the query and refresh the view"""
        self._query_getter = query_getter
        self.refresh()
        
    def get_collection(self):
        """In case the collection is requested of a QueryProxy, we will return
        a collection getter for a collection that reuses the data allready queried by
        the collection proxy, and available in the cache.
         
        We do this to :
        
        1. Prevent an unneeded query when the collection is used to fetch an object already
           fetched by the query proxy (eg when a form is opened on a table view)
           
        2. To make sure the index of an object in the query proxy is the same as the index
           in the returned collection.  Should we do the same query twice (once to fill the
           query proxy, and once to fill the returned collection), the same object might appear
           in a different row.  eg when a form is opened in a table view, the form contains 
           another record than the selected row in the table.
        """
        
        if not self._query_getter:
            return []
        return self.get_query_getter()().all()
    
    @gui_function
    def sort( self, column, order ):
        
        def create_set_sort_decorator(column, order):

            def set_sort_decorator():
                from sqlalchemy import orm
                from sqlalchemy.exceptions import InvalidRequestError
                field_name = self._columns[column][0]
                class_attribute = getattr(self.admin.entity, field_name)
                mapper = orm.class_mapper(self.admin.entity)
                try:
                    property = mapper.get_property(
                        field_name,
                        resolve_synonyms=True
                    )
                except InvalidRequestError:
                    #
                    # If the field name is not a property of the mapper, we cannot
                    # sort it using sql
                    #
                    return self._rows
                
                # If the field is a relation: 
                #  If it specifies an order_by option we have to join the related table, 
                #  else we use the foreing key as sort field, without joining
                join = None
                if isinstance(property, orm.properties.PropertyLoader):
                    target = property._get_target()
                    if target:
                        if target.order_by:
                            join = field_name
                            class_attribute = target.order_by[0]
                        else:
                            #
                            # _foreign_keys is for sqla pre 0.6.4
                            # 
                            if hasattr(property, '_foreign_keys'):
                                class_attribute = list(property._foreign_keys)[0]
                            else:                             
                                class_attribute = list(property._calculated_foreign_keys)[0]                    
                    
                def create_sort_decorator(class_attribute, order, join):
                                        
                    def sort_decorator(query):
                        if join:
                            query = query.join(join)                            
                        if order:
                            return query.order_by(class_attribute.desc())
                        else:
                            return query.order_by(class_attribute)
                    
                    return sort_decorator
                
                
                self._sort_decorator = create_sort_decorator(class_attribute, order, join)
                return self._rows
                    
            return set_sort_decorator
            
        post( create_set_sort_decorator(column, order), self._refresh_content )

    def append(self, o):
        """Add an object to this collection, used when inserting a new
        row, overwrite this method for specific behaviour in subclasses"""
        if not o.id:
            self._appended_rows.append(o)

    def remove(self, o):
        if o in self._appended_rows:
            self._appended_rows.remove(o)
        self._rows = self._rows - 1

    @model_function
    def getData(self):
        """Generator for all the data queried by this proxy"""
        if self._query_getter:
            for _i,o in enumerate(self.get_query_getter()().all()):
                yield strip_data_from_object(o, self.getColumns())

    @model_function
    def _get_collection_range( self, offset, limit ):
        """Get the objects in a certain range of the collection
        :return: an iterator over the objects in the collection, starting at 
        offset, until limit
        """
        query = self.get_query_getter()().offset(offset).limit(limit)
        return query.all()
                    
    @model_function
    def _extend_cache(self):
        """Extend the cache around the rows under request"""
        if self._query_getter:
            offset, limit = self._offset_and_limit_rows_to_get()
            if limit:
                columns = self.getColumns()
                for i, obj in enumerate( self._get_collection_range(offset, limit) ):
                    row = i + offset
                    try:
                        previous_obj = self.edit_cache.get_entity_at_row(row)
                        if previous_obj != obj:
                            continue
                    except KeyError:
                        pass
                    self._add_data(columns, i+offset, obj)
                rows_in_query = (self._rows - len(self._appended_rows))
                # Verify if rows that have not yet been flushed have been 
                # requested
                if offset+limit >= rows_in_query:
                    for row in range(max(rows_in_query, offset), min(offset+limit, self._rows)):
                        obj = self._get_object(row)
                        self._add_data(columns, row, obj)                
            return (offset, limit)

    @model_function
    def _get_object(self, row):
        """Get the object corresponding to row"""
        if self._rows > 0:
            self._clean_appended_rows()
            rows_in_query = (self._rows - len(self._appended_rows))
            if row >= rows_in_query:
                return self._appended_rows[row - rows_in_query]
            # first try to get the primary key out of the cache, if it's not
            # there, query the collection_getter
            try:
                return self.edit_cache.get_entity_at_row(row)
            except KeyError:
                pass
            # momentary hack for list error that prevents forms to be closed
            if self._query_getter:
                res = self.get_query_getter()().offset(row)
                if isinstance(res, list):
                    res = res[0]
                # @todo: remove this try catch and find out why it 
                # sometimes fails
                try:
                    return res.limit(1).first()
                except:
                    pass

