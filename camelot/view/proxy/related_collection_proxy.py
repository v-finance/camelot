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
"""
Proxy representing a collection of entities thas is related to a row in 
another model.

If changes occur to entities in this collection, they will not be flushed
to the database, instead the related model will be informed of the changes.
"""
from collection_proxy import *

logger = logging.getLogger('proxy.related_collection_proxy')

class RelatedCollectionProxy(CollectionProxy):
  
  def __init__(self, admin, collection_getter, columns_getter, related_index, max_number_of_rows=10):
    CollectionProxy.__init__(self, admin, collection_getter, columns_getter, max_number_of_rows=10, edits=None, flush_changes=True)
    self.related_index = related_index
    
  def removeRow(self, row):
    logger.debug('remove row %s'%row)
    
    def create_delete_function():
      
      def delete_function():
        from elixir import session
        from camelot.model.memento import BeforeDelete
        from camelot.model.authentication import getCurrentPerson
        o = self._get_object(row)
        pk = o.id
        self.remove(o)
        # save the state before the update
        history = BeforeDelete(model=self.admin.entity.__name__, 
                               primary_key=pk, 
                               previous_attributes={},
                               person = getCurrentPerson() )
        self.rsh.sendEntityDelete(o)        
        o.delete()
        session.flush([history, o])   
      
      return delete_function
    
    def create_emit_function():
      
      def emit_changes(*args):
        self.related_index.model().setData(self.related_index, lambda:None)
        self.refresh()
      
      return emit_changes
  
    self.mt.post(create_delete_function(), create_emit_function())
    return True
  
  def insertRow(self, row, entity_instance_getter):
    
    self.unflushed_rows.add(row)
    
    def create_insert_function(getter):
      
      @model_function
      def insert_function():
        o = getter()
        self.append(o)
          
      return insert_function
      
    def create_emit_function(getter):
      
      def emit_changes(*args):
        self.related_index.model().setData(self.related_index, getter)
        self.refresh()
      
      return emit_changes
  
    self.mt.post(create_insert_function(entity_instance_getter), create_emit_function(entity_instance_getter))

