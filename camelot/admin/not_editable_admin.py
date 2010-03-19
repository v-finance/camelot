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

"""Class decorator to make all fields visualized with the Admin into read-only
fields"""

from copy import copy
def notEditableAdmin(original_admin, actions=False, editable_fields=None):

    """Turn all fields visualized with original_admin into read only fields
  :param original_admin: an implementation of ObjectAdmin
  :param actions: True if the notEditableAdmin should have its actions enabled, default to False
  :param editable_fields: list of fields that should remain editable

  usage ::

    class Movie(Entity):
      name = Field(Unicode(50))
      contributions = Field(Unicode(255))

      class Admin(EntityAdmin):
        list_display = ['name', 'contributions]

      Admin = notEditableAdmin(Admin, editable_fields=['contributions'])
    """
    
    class NewAdmin(original_admin):

        def get_related_entity_admin(self, entity):
            admin = original_admin.get_related_entity_admin(self, entity)
            
            class AdminReadOnlyDecorator(object):
                
                def __init__(self, original_admin, editable_fields):
                    self._original_admin = original_admin
                    self._editable_fields = editable_fields
                    self._field_attributes = dict()
                    
                def __getattr__(self, name):
                    return self._original_admin.__getattribute__(name)
                
                def get_fields(self):
                    fields = self._original_admin.get_fields()
                    return [(field_name,self.get_field_attributes(field_name)) for field_name,_attrs in fields]
                
                def get_field_attributes(self, field_name):
                    try:
                        return self._field_attributes[field_name]
                    except KeyError:
                        attribs = copy( self._original_admin.get_field_attributes(field_name) )
                        if self._editable_fields and field_name in self._editable_fields:
                            attribs['editable'] = True
                        else: 
                            attribs['editable'] = False
                        return attribs
                
                def get_related_entity_admin(self, entity):
                    return AdminReadOnlyDecorator(self._original_admin.get_related_entity_admin(entity))
                
                def get_form_actions(self, *a, **kwa):
                    return []
                
                def get_list_actions(self, *a, **kwa):
                    return []
                
                def get_columns(self): 
                    return [(field, self.get_field_attributes(field))
                            for field, _attrs in self._original_admin.get_columns()]           
                     
            return AdminReadOnlyDecorator(admin, editable_fields)

        def get_field_attributes(self, field_name):
            attribs = original_admin.get_field_attributes(self, field_name)
            if editable_fields and field_name in editable_fields:
                attribs['editable'] = True
            else:
                attribs['editable'] = False
            return attribs
        
        def get_form_actions(self, *a, **kwa):
            return []
        
        def get_list_actions(self, *a, **kwa):
            return []

    return NewAdmin
