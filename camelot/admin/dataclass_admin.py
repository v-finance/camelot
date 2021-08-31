import dataclasses

from camelot.admin.object_admin import ObjectAdmin



class DataclassAdmin(ObjectAdmin):
    """
    specialized object admin for dataclasses that introspects fieldattributes based on the dataclass' fields.
    """
    def __init__(self, app_admin, entity):
        super().__init__(app_admin, entity)
        assert dataclasses.is_dataclass(entity), 'The given entity class is not a dataclass'
    
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
