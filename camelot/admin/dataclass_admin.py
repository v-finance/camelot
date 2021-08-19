import dataclasses

from camelot.admin.object_admin import ObjectAdmin

class DataclassAdmin(ObjectAdmin):
    
    def __init__(self, app_admin, entity):
        super().__init__(app_admin, entity)
        assert dataclasses.is_dataclass(entity), 'The given entity class is not a dataclass'
    
    def get_descriptor_field_attributes(self, field_name):
        attributes = super().get_descriptor_field_attributes()
        if field_name in self.entity.__dataclass_fields__:
            attributes['editable'] = (True)
        
        return attributes
    