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
Proxy representing a collection of entities which is related to a row in 
another model.

If changes occur to entities in this collection, they will not be flushed
to the database, instead the related model will be informed of the changes.
"""
from collection_proxy import *

logger = logging.getLogger('proxy.related_collection_proxy')

class RelatedCollectionProxy(CollectionProxy):
  
  def __init__(self, admin, collection_getter, columns_getter, related_model, row_in_related_model, max_number_of_rows=10):
    self.related_model = related_model
    self.row_in_related_model = row_in_related_model
    CollectionProxy.__init__(self, admin, collection_getter, columns_getter, max_number_of_rows=10, edits=None, flush_changes=True)
    
  def __unicode__(self):
    return u'RelatedCollectionProxy for objects of type %s connected to %s row %s'%(self.admin.entity.__name__, str(self.related_model), self.row_in_related_model)
  
  def refresh(self):
    super(RelatedCollectionProxy, self).refresh()
    
  def setData(self, index, value, role=Qt.EditRole):
    result = super(RelatedCollectionProxy, self).setData(index, value, role)
    self.related_model.handleRowUpdate(self.row_in_related_model)
    return result
    
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
        if o.id:
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
        self.refresh()
      
      return emit_changes
  
    self.mt.post(create_delete_function(), create_emit_function())
    return True
  
  def insertRow(self, row, entity_instance_getter):
    
    def create_insert_function(getter):
      
      @model_function
      def insert_function():
        from elixir import session
        o = getter()
        self.unflushed_rows.add(row)
        self.append(o)
        if self.flush_changes and not len(self.validator.objectValidity(o)):
          session.flush([o])
          try:
            self.unflushed_rows.remove(row)
          except KeyError:
            pass
          
      return insert_function
      
    def create_emit_function(getter):
      
      def emit_changes(*args):
        self.refresh()
      
      return emit_changes
  
    self.mt.post(create_insert_function(entity_instance_getter), create_emit_function(entity_instance_getter))

