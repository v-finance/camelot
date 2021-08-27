import dataclasses
import typing

from camelot.admin.object_admin import ObjectAdmin
from camelot.admin.action import list_filter
from camelot.core.orm import Entity
from camelot.types.typing import is_optional_type


class DataclassAdmin(ObjectAdmin):
    """
    specialized object admin for dataclasses that introspects fieldattributes based on the dataclass' fields.
    """
    def __init__(self, app_admin, entity):
        super().__init__(app_admin, entity)
        assert dataclasses.is_dataclass(entity), 'The given entity class is not a dataclass'
    
    def get_descriptor_field_attributes(self, field_name):
        attributes = super().get_descriptor_field_attributes(field_name)
           
        for field in dataclasses.fields(self.entity):
            if field.name == field_name:
                attributes['editable'] = True
                attributes['nullable'] = is_optional_type(field.type)
                attributes.update(self.get_typing_attributes(field.type))            
        return attributes
    
    def get_completions(self, obj, field_name, prefix):
        """
        Overwrites `ObjectAdmin.get_completions` and searches for autocompletion
        along relationships.
        """
        for field in dataclasses.fields(self.entity):
            if field.name == field_name:
                field_type = field.type.__args__[0] if is_optional_type(field.type) else field.type
                if issubclass(field_type, Entity):
                    all_attributes = self.get_field_attributes(field_name)
                    admin = all_attributes.get('admin')
                    session = self.get_session(obj)
                    if (admin is not None) and (session is not None):
                        search_filter = list_filter.SearchFilter(admin)
                        query = admin.get_query(session)
                        query = search_filter.decorate_query(query, prefix)
                        return [e for e in query.limit(20).all()]
        return super().get_completions(obj, field_name, prefix)
            
    def get_session(self, obj):
        raise NotImplementedError
    
    
    
              
        
    