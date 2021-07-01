
"""Admin class for Entity Facade Object"""

import logging
logger = logging.getLogger('camelot.view.object_admin')

from ..core.orm.entity import EntityFacade
from .object_admin import ObjectAdmin

class FacadeAdmin(ObjectAdmin):
    """
    The FacadeAdmin class describes the interface that will be used to interact with facade objects.
    As facade object provide a regular object layer on top of an entity, this admin is a decorated combination of an ObjectAdmin and an EntityAdmin,
    whereby it keeps a reference of the entity admin of the facade's subsystem to delegate behaviour to.
    """    
    
    def __init__(self, app_admin, entity):
        assert issubclass(entity, EntityFacade), '{} is not an EntityFacade class'.format(entity)
        super(FacadeAdmin, self).__init__(app_admin, entity)
        self.entity_admin = self.get_related_admin(entity.__subsystem_cls__)

    def get_verbose_name(self):
        type_ = self.entity.__facade_args__.get('type')
        if type_ is not None:
            return self.entity.__subsystem_cls__.__types__.get_verbose_name(type_)
        return super().get_verbose_name()

    def get_descriptor_field_attributes(self, field_name):
        """
        Expand the set of default introspected field attributes with those that are possibly registered on subsystem's entity admin.
        """
        attributes = super(FacadeAdmin, self).get_descriptor_field_attributes(field_name)
        for cls in self.entity.__mro__ + self.entity.__subsystem_cls__.__mro__:
            descriptor = cls.__dict__.get(field_name, None)
            if descriptor is not None:
                # Check if their are field attributes registered specific to the descriptor's class and or superclasses.
                # For each of the descriptor superclasses and the class itself, starting from the uppermost superclass, check if it is registered
                # and apply attributes accordingly, ensuring this is always done in the correct order of inheritance.
                for descriptor_cls in reversed(descriptor.__class__.__mro__):
                    if descriptor_cls in self.entity_admin.registered_property_attributes:
                        get_attributes_func = self.entity_admin.registered_property_attributes.get(descriptor_cls)
                        attributes = get_attributes_func(self, attributes, descriptor, field_name)
                break
        return attributes
    
    def get_search_identifiers(self, obj):
        return self.entity_admin.get_search_identifiers(obj.subsystem_object)

    def get_depending_objects(self, obj):
        yield from self.entity_admin.get_depending_objects(obj.subsystem_object)

    def get_compounding_objects(self, obj):
        return self.entity_admin.get_compounding_objects(obj.subsystem_object)

    def get_completions(self, obj, field_name, prefix):
        return self.entity_admin.get_completions(obj.subsystem_object, field_name, prefix)

    def set_field_value(self, obj, field_name, value):
        self.entity_admin.set_field_value(obj.subsystem_object, field_name, value)

    def _set_defaults(self, object_instance):
        return self.entity_admin._set_defaults(object_instance.subsystem_object)

    def primary_key( self, obj ):
        return self.entity_admin.primary_key(obj.subsystem_object)

    def get_modifications( self, obj ):
        return self.entity_admin.get_modifications(obj.subsystem_object)

    def delete(self, entity_instance):
        self.entity_admin.delete(entity_instance.subsystem_object)

    def flush(self, entity_instance):
        # TODO
        #session = orm.object_session(entity_instance.subsystem_object)
        #if not isinstance(session, InputSession):
        self.entity_admin.flush(entity_instance.subsystem_object)

    def expunge(self, entity_instance):
        self.entity_admin.expunge(entity_instance.subsystem_object)

    def refresh(self, entity_instance):
        self.entity_admin.refresh(entity_instance.subsystem_object)

    def add(self, entity_instance):
        self.entity_admin.add(entity_instance.subsystem_object)

    def is_deleted(self, _obj):
        return self.entity_admin.is_deleted(_obj.subsystem_object)
    
    def is_persistent(self, _obj):
        return self.entity_admin.is_persistent(_obj.subsystem_object)

    def is_dirty(self, _obj):
        return self.entity_admin.is_dirty(_obj.subsystem_object)

    def copy(self, entity_instance):
        return self.entity_admin.copy(entity_instance.subsystem_object)
