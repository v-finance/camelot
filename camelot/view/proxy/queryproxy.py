#  ============================================================================
#
#  Copyright (C) 2007-2013 Conceptive Engineering bvba. All rights reserved.
#  www.conceptive.be / info@conceptive.be
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
#  visit www.python-camelot.com or contact info@conceptive.be
#
#  This file is provided AS IS with NO WARRANTY OF ANY KIND, INCLUDING THE
#  WARRANTY OF DESIGN, MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE.
#
#  For use of this library in commercial applications, please contact
#  info@conceptive.be
#
#  ============================================================================

"""Proxies representing the results of a query"""

import functools
import logging
logger = logging.getLogger('camelot.view.proxy.queryproxy')

from ...core.item_model import QueryModelProxy
from ..model_thread import object_thread, post
from .collection_proxy import CollectionProxy

class QueryTableProxy(CollectionProxy):
    """The QueryTableProxy contains a limited copy of the data in the SQLAlchemy
    model, which is fetched from the database to be used as the model for a
    QTableView
    """

    def set_value(self, value):
        self._value = QueryModelProxy(value)
        self._reset()
        self.layoutChanged.emit()

    def sort( self, column, order ):
        """Overwrites the :meth:`QAbstractItemModel.sort` method
        """
        assert object_thread( self )
        post( functools.update_wrapper( functools.partial( self._set_sort_decorator, column, order ), self._set_sort_decorator ), 
              self._refresh_content )

    def set_filter(self, list_filter, value):
        """
        Set the filter mode for a specific filter

        :param list_filter: a :class:`camelot.admin.action.list_filter.Filter` object
        :param value: the value on which to filter
        """
        previous_value = self._filters.get(list_filter)
        self._filters[list_filter] = value
        if value != previous_value:
            self._rows = None
            self._reset()
            self.layoutChanged.emit()

    def _get_collection_range( self, offset, limit ):
        """Get the objects in a certain range of the collection
        :return: an iterator over the objects in the collection, starting at 
        offset, until limit
        """
        from sqlalchemy import orm
        from sqlalchemy.exc import InvalidRequestError
        
        query = self.get_query().offset(offset).limit(limit)
        #
        # undefer all columns displayed in the list, to reduce the number
        # of queries
        #
        columns_to_undefer = []
        for field_name, _field_attributes in self._columns:
            
            property = None
            try:
                property = self.admin.mapper.get_property(
                    field_name,
                )
            except InvalidRequestError:
                #
                # If the field name is not a property of the mapper
                #
                pass

            if property and isinstance(property, orm.properties.ColumnProperty):
                columns_to_undefer.append( field_name )
                
        if columns_to_undefer:
            options = [ orm.undefer( field_name ) for field_name in columns_to_undefer ]
            query = query.options( *options )
                
        return query.all()
