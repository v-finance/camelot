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

"""Proxies representing the results of a query"""

from PyQt4.QtCore import Qt

import logging
logger = logging.getLogger('camelot.view.proxy.queryproxy')

from collection_proxy import CollectionProxy, stripped_data_to_unicode, \
                             strip_data_from_object, tool_tips_from_object, \
                             background_colors_from_object
from camelot.view.model_thread import model_function, gui_function


class QueryTableProxy(CollectionProxy):
    """The QueryTableProxy contains a limited copy of the data in the Elixir
    model, which is fetched from the database to be used as the model for a
    QTableView
    """

    def __init__(self, admin, query_getter, columns_getter,
                 max_number_of_rows=10, edits=None):
        """@param query_getter: a model_thread function that returns a query"""
        logger.debug('initialize query table')
        self._query_getter = query_getter
        #rows appended to the table which have not yet been flushed to the
        #database, and as such cannot be a result of the query
        self._appended_rows = []
        CollectionProxy.__init__(self, admin, lambda: [],
                                 columns_getter, max_number_of_rows=10, edits=None)

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
        return self._query_getter().count() + len(self._appended_rows)

    @gui_function
    def setQuery(self, query_getter):
        """Set the query and refresh the view"""
        self._query_getter = query_getter
        self.refresh()

    def append(self, o):
        """Add an object to this collection, used when inserting a new
        row, overwrite this method for specific behaviour in subclasses"""
        if not o.id:
            self._appended_rows.append(o)
        self.rows = self.rows + 1

    def remove(self, o):
        if o in self._appended_rows:
            self._appended_rows.remove(o)
        self.rows = self.rows - 1

    @model_function
    def getData(self):
        """Generator for all the data queried by this proxy"""
        for _i,o in enumerate(self._query_getter().all()):
            yield strip_data_from_object(o, self.getColumns())

    @model_function
    def _extend_cache(self, offset, limit):
        """Extend the cache around row"""
        q = self._query_getter().offset(offset).limit(limit)
        columns = self.getColumns()
        for i, o in enumerate(q.all()):
            row_data = strip_data_from_object(o, columns)
            self.cache[Qt.EditRole].add_data(i+offset, o, row_data)
            self.cache[Qt.ToolTipRole].add_data(i+offset, o, tool_tips_from_object(o, columns))
            self.cache[Qt.BackgroundColorRole].add_data(i+offset, o, background_colors_from_object(o, columns))
            self.cache[Qt.DisplayRole].add_data(i+offset, o, stripped_data_to_unicode(row_data, o, columns))
        rows_in_query = (self.rows - len(self._appended_rows))
        # Verify if rows that have not yet been flushed have been requested
        if offset+limit>=rows_in_query:
            for row in range(max(rows_in_query,offset), min(offset+limit, self.rows)):
                o = self._get_object(row)
                row_data = strip_data_from_object(o, columns)
                self.cache[Qt.EditRole].add_data(row, o, row_data)
                self.cache[Qt.ToolTipRole].add_data(row, o, tool_tips_from_object(o, columns))
                self.cache[Qt.BackgroundColorRole].add_data(row, o, background_colors_from_object(o, columns))
                self.cache[Qt.DisplayRole].add_data(row, o, stripped_data_to_unicode(row_data, o, columns))
        return (offset, limit)

    @model_function
    def _get_object(self, row):
        """Get the object corresponding to row"""
        if self.rows > 0:
            self._clean_appended_rows()
            rows_in_query = (self.rows - len(self._appended_rows))
            if row >= rows_in_query:
                return self._appended_rows[row - rows_in_query]
            # first try to get the primary key out of the cache, if it's not
            # there, query the collection_getter
            try:
                return self.cache[Qt.EditRole].get_entity_at_row(row)
            except KeyError:
                pass
            # momentary hack for list error that prevents forms to be closed
            res = self._query_getter().offset(row)
            if isinstance(res, list):
                res = res[0]
            # @todo: remove this try catch and find out why it sometimes fails
            try:
                return res.limit(1).first()
            except:
                pass
