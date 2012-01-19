#  ============================================================================
#
#  Copyright (C) 2007-2012 Conceptive Engineering bvba. All rights reserved.
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

from copy import copy
from itertools import tee

def not_editable_admin( original_admin, 
                        actions = False, 
                        editable_fields = [],
                        deep = True ):
    """Class decorator to make all fields read-only.

    :param original_admin: an :class:`camelot.admin.object_admin.ObjectAdmin` 
        class (not an instance)
    :param actions: :keyword:`True` if the new admin should have its actions 
        enabled, defaults to :keyword:`False`
    :param editable_fields: list of fields that should remain editable, if they
        are editable in the original admin.
    :param deep: indicates if Admin classes related to this admin should become
        read-only as well.  This makes other objects pointed to by OneToMany and
        ManyToOne fields read only.
    :return: a new admin class, with read only fields.  The new admin class
        is a subclass of the original class.

    usage ::

        class Movie(Entity):
            name = Field(Unicode(50))
            contributions = Field(Unicode(255))

            class Admin(EntityAdmin):
                list_display = ['name', 'contributions]

            Admin = not_editable_admin( Admin, 
                                        editable_fields=['contributions'] )
    """
    
    class NewAdmin( original_admin ):

        def get_related_admin( self, cls ):
            admin = super( NewAdmin, self ).get_related_admin( cls )
            if not deep:
                return admin
            
            class AdminReadOnlyDecorator(object):

                def __init__(self, original_admin, editable_fields):
                    self._original_admin = original_admin
                    self._editable_fields = editable_fields
                    self._field_attributes = dict()
                    
                def _process_field_attributes(self, field, attributes):
                    if not 'editable' in attributes:
                        return attributes
                    if attributes['editable']==False:
                        return attributes
                    if self._editable_fields and field in self._editable_fields:
                        return attributes
                    new_attributes = copy( attributes )
                    new_attributes['editable'] = False
                    return new_attributes
                
                def __getattr__(self, name):
                    return getattr( self._original_admin, name)
                
                def get_fields(self):
                    fields = self._original_admin.get_fields()
                    return [(field_name, self._process_field_attributes(field_name, _attrs)) for field_name,_attrs in fields]
                
                def get_field_attributes(self, field_name):
                    attributes = self._original_admin.get_field_attributes(field_name)
                    return self._process_field_attributes(field_name, attributes)
                
                def get_dynamic_field_attributes(self, obj, field_names):
                    fn1, fn2 = tee(field_names, 2)
                    dynamic_fa = self._original_admin.get_dynamic_field_attributes(obj, fn1)
                    return [self._process_field_attributes(name, attributes) for name,attributes in zip(fn2, dynamic_fa)]
                    
                def get_static_field_attributes(self, field_names):
                    fn1, fn2 = tee(field_names, 2)
                    static_fa = self._original_admin.get_static_field_attributes(fn1)
                    return [self._process_field_attributes(name, attributes) for name,attributes in zip(fn2, static_fa)]
                    
                def get_related_admin(self, entity):
                    return AdminReadOnlyDecorator(self._original_admin.get_related_admin(entity), self._editable_fields)
                
                def get_form_actions(self, *a, **kwa):
                    return []
                
                def get_list_actions(self, *a, **kwa):
                    return []
                
                def get_columns(self): 
                    return [(field, self._process_field_attributes(field, attrs))
                            for field, attrs in self._original_admin.get_columns()]       
                     
            return AdminReadOnlyDecorator(admin, editable_fields)

        def get_field_attributes( self, field_name ):
            attribs = super( NewAdmin, self ).get_field_attributes( field_name )
            if field_name not in editable_fields:
                attribs['editable'] = False
            return attribs
        
        def get_form_actions( self, obj ):
            if actions == True:
                return super( NewAdmin, self ).get_form_actions( obj )
            return []
        
        def get_list_actions( self ):
            if actions == True:
                return super( NewAdmin, self ).get_list_actions()
            return []

    return NewAdmin
