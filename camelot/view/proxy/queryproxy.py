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

"""Proxies representing the results of a query"""

import logging
logger = logging.getLogger('camelot.view.proxy.queryproxy')

from .collection_proxy import CollectionProxy

class QueryTableProxy(CollectionProxy):
    """The QueryTableProxy contains a limited copy of the data in the SQLAlchemy
    model, which is fetched from the database to be used as the model for a
    QTableView
    """

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


