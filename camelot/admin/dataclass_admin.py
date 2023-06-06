import dataclasses
from enum import Enum

from camelot.admin.object_admin import ObjectAdmin, register_list_actions
from camelot.admin.action import list_action
from camelot.core.serializable import DataclassSerializable


class DataclassAdmin(ObjectAdmin):
    """
    specialized object admin for dataclasses that introspects fieldattributes based on the dataclass' fields.
    """
    
    class AssertionMessage(Enum):
        
        no_dataclass = 'The given entity class is not a dataclass'
    
    def __init__(self, app_admin, entity):
        super().__init__(app_admin, entity)
        assert dataclasses.is_dataclass(entity), self.AssertionMessage.no_dataclass.value
    
    def get_typing(self, field_name):
        for field in dataclasses.fields(self.entity):
            if field.name == field_name:
                return field.type
        return super().get_typing(field_name)
    
    def get_descriptor_field_attributes(self, field_name):
        attributes = super().get_descriptor_field_attributes(field_name)
        for field in dataclasses.fields(self.entity):
            if field.name == field_name:
                attributes['editable'] = True
        return attributes
    
    def _get_entity_descriptor(self, field_name):
        if not field_name in self.entity.__dataclass_fields__:
            return super()._get_entity_descriptor(field_name)

    def copy(self, entity_instance):
        """Duplicate this dataclass entity instance"""
        if isinstance(entity_instance, DataclassSerializable):
            fields = DataclassSerializable.asdict(entity_instance)
        else:
            fields = dataclasses.asdict(entity_instance)
        new_entity_instance = entity_instance.__class__(**fields)
        return new_entity_instance

    @register_list_actions('_admin_route', '_toolbar_actions')
    def get_list_toolbar_actions(self):
        return super().get_list_toolbar_actions() + [list_action.stretch]
