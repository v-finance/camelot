#  ==================================================================================
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
#  ==================================================================================

"""Proxies representing the results of a query"""
import logging

from collection_proxy import *

logger = logging.getLogger('proxy.queryproxy')
logger.setLevel(logging.DEBUG)
    
class QueryTableProxy(CollectionProxy):
  """The QueryTableProxy contains a limited copy of the data in the Elixir
  model, which is fetched from the database to be used as the model for a
  QTableView
  """

  def __init__(self, admin, query, columns_getter, max_number_of_rows=10, edits=None):
    logger.debug('initialize query table')
    self.query = query
    CollectionProxy.__init__(self, admin, lambda :[], columns_getter, max_number_of_rows=10, edits=None)

  def _getRowCount(self):
    return self.query.count()
  
  def setQuery(self, query):
    """Set the query and refresh the view"""
    self.query = query
    self.refresh()
    
  def append(self, o):
    """Add an object to this collection, used when inserting a new
    row, overwrite this method for specific behaviour in subclasses"""
    pass
      
  def remove(self, o):
    pass
    
  def getData(self):
    """Generator for all the data queried by this proxy"""
    columns = [c[0] for c in self.columns_getter()]
    for o in self.query.all():
      yield RowDataFromObject(o, columns)
      
  def _extend_cache(self, offset, limit):
    """Extend the cache around row"""
    #@TODO : also store the primary key, here we just saved the id
    columns = [c[0] for c in self.columns_getter()] + ['id']
    q = self.query.offset(offset).limit(limit)
    for i,o in enumerate(q.all()):
      row_data = RowDataFromObject(o, columns)
      self.cache[Qt.EditRole][i+offset] = row_data
      self.cache[Qt.DisplayRole][i+offset] = RowDataAsUnicode(row_data)
    return (offset, limit)
        
  def _get_object(self, row):
    """Get the object corresponding to row"""
    return self.query.offset(row).limit(1).first()



