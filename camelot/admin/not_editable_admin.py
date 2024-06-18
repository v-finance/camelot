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

from copy import copy
from itertools import tee

from camelot.core.exception import UserException
from camelot.core.utils import ugettext_lazy as _

from .admin_route import AdminRoute

class ReadOnlyAdminDecorator(AdminRoute):
    """Decorator to make an instance of an Admin class read only"""

    def __init__(self, original_admin, editable_fields=[], allow_deletes=False):
        super().__init__()
        self._original_admin = original_admin
        self._editable_fields = editable_fields
        self._allow_deletes = allow_deletes
        self._field_attributes = dict()
        self._admin_route = super()._register_admin_route(self)

    def get_admin_route(self):
        return self._admin_route

    def __getattr__(self, name):
        return getattr(self._original_admin, name)

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
        return ReadOnlyAdminDecorator(self._original_admin.get_related_admin(entity), self._editable_fields)
    
    def get_form_actions(self, *a, **kwa):
        return []
    
    def get_list_actions(self, *a, **kwa):
        return []
    
    def get_columns(self): 
        return self._original_admin.get_columns()

    def is_obj_editable(self, obj):
        return False

    def is_obj_deletable(self, obj):
        if self._allow_deletes:
            return self._original_admin.is_obj_deletable(obj)
        return False

    def deletable_or_raise(self, obj):
        if self._allow_deletes:
            self._original_admin.deletable_or_raise(obj)
        else:
            raise UserException(_('{} is not permitted to be deleted', obj))

def not_editable_admin( original_admin, 
                        actions = False, 
                        editable_fields = [],
                        deep = True,
                        allow_deletes=False):
    """Class decorator to make all fields read-only.

    :param original_admin: an :class:`camelot.admin.object_admin.ObjectAdmin` 
        class (not an instance)
    :param actions: :const:`True` if the new admin should have its actions 
        enabled, defaults to :const:`False`
    :param editable_fields: list of fields that should remain editable, if they
        are editable in the original admin.
    :param deep: indicates if Admin classes related to this admin should become
        read-only as well.  This makes other objects pointed to by OneToMany and
        ManyToOne fields read only.
    :param allow_deletes: indicates whether objects are allowed to be deleted within the
        context of this not editable admin. Defaults to False, in which case the existing/
        original admin's deletable methodology is used.
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
            return ReadOnlyAdminDecorator(admin, editable_fields, allow_deletes)

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
    
        def is_obj_editable(self, obj):
            return False

        def is_obj_deletable(self, obj):
            if allow_deletes:
                return super( NewAdmin, self ).is_obj_deletable(obj)
            return False

        def deletable_or_raise(self, obj):
            if allow_deletes:
                super( NewAdmin, self ).deletable_or_raise(obj)
            else:
                raise UserException(_('{} is not permitted to be deleted', obj))

    return NewAdmin


