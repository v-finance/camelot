import dataclasses
import typing

from camelot.admin.object_admin import ObjectAdmin
from camelot.view.field_attributes import _dataclass_to_python_type
from camelot.view.controls import delegates
from camelot.core.orm import Entity


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
                attributes['nullable'] = self._is_field_optional(field.type)
                attributes.update(self._get_dataclass_attributes(field.type))
        return attributes
    
    def _get_dataclass_attributes(self, field_type):
        if field_type in _dataclass_to_python_type:
            dataclass_attributes = _dataclass_to_python_type.get(field_type)
            return dataclass_attributes
        elif self._is_field_optional(field_type):
            return self._get_dataclass_attributes(field_type.__args__[0])
        elif issubclass(field_type, Entity):
            return {'delegate':delegates.Many2OneDelegate,
                    'target':field_type,
                    }
        return {}
    
    def _is_field_optional(self, field_type):
        return isinstance(field_type, typing._GenericAlias) and \
               field_type.__origin__ == typing.Union and \
               len(field_type.__args__) == 2 and \
               type(None) == field_type.__args__[1]
    
              
        
    