import types

from sqlalchemy import orm, schema, sql

def is_supported_attribute(attribute):
    return isinstance(attribute, sql.schema.Column) or \
           isinstance(attribute, orm.attributes.InstrumentedAttribute) and \
           isinstance(attribute.prop, orm.properties.ColumnProperty) and \
           isinstance(attribute.prop.columns[0], schema.Column)

class abstract_attribute_prospection(object):
    """
    Abstract function decorator that supports registering prospected behaviour for one of the instrumented
    column attribute of an Entity class.
    """

    attribute = None
    for_transition_types = None

    def __init__(self, func):
        assert isinstance(self.for_transition_types, tuple)
        self.func = func
        self.register(self)

    @classmethod
    def register(cls, self):
        column = cls.attribute.prop.columns[0] if isinstance(cls.attribute, orm.attributes.InstrumentedAttribute) else cls.attribute
        column.info.setdefault('prospection', {})
        if cls.for_transition_types:
            for transition_type in cls.for_transition_types:
                column.info['prospection'][transition_type.name] = self
        else:
            column.info['prospection'][None] = self

    def __call__(self, target, at, **kwargs):
        target_cls = type(target)
        mapper = orm.class_mapper(target_cls)
        class_attribute = mapper.get_property(self.__class__.attribute.key).class_attribute
        if self.for_transition_types:
            assert target_cls.transition_types is not None, '{} has no transition_types configured in its __entity_args__'.format(target_cls)
            for transition_type in self.for_transition_types:
                assert transition_type in target_cls.transition_types.values(), '{} is not a valid transition type for {}'.format(transition_type, target_cls)

        if None not in (target, at):
            current_value = class_attribute.__get__(target, None)
            # The prospection should only be possible if the target's is applicable.
            if target.is_applicable_at(at):
                return self.func(target, at, **kwargs)
            # Otherwise, the current value is returned.
            return current_value

    def __get__(self, instance, owner):
        return types.MethodType(self, instance) if instance is not None else self

def prospected_attribute(column_attribute, *transition_types):
    """
    Function decorator that supports registering prospected behaviour for one of the instrumented
    column attribute of an Entity class.
    The user-defined function expects an instance of the target entity and the prospection date,
    and will be decorated/wrapped with the following behaviour:

      * the return value will be undefined if any of the arguments are undefined
      * the return value will be the current value of the given column attribute on the target instance,
        if prospection on the instance is not applicable.
        A default _prospection_applicable method is provided on each Entity class by `orm.entity.EntityMeta` metaclass,
        but can be customized if needed on the corresponding entity.

    This function decorator requires the application_date of the target Entity class to be registered in its __entity_args__.

    :example:
     |
     |  class ConcreteEntity(Entity):
     |
     |     apply_from_date = schema.Column(sqlalchemy.types.Date())
     |     duration = schema.Column(sqlalchemy.types.Integer())
     |
     |     __entity_args__ = {
     |        'application_date': apply_from_date,
     |     }
     |
     |     @prospected_attribute(duration)
     |     def prospected_duration(self, at):
     |        return months_between_dates(self.apply_from_date, at)
     |
     |  ConcreteEntity(apply_from_date=datetime.date(2012,1,1), duration=24).prospected_duration(datetime.date(2013,1,1)) == 12
     |  ConcreteEntity(apply_from_date=datetime.date(2012,1,1), duration=24).prospected_duration(None) == None
     |  ConcreteEntity(apply_from_date=None, duration=24).prospected_duration(None) == 24
     |  ConcreteEntity(apply_from_date=datetime.date(2012,1,1), duration=24).prospected_duration(datetime.date(2011,1,1)) == 24
     |  ConcreteEntity(apply_from_date=datetime.date(2401,1,1), duration=24).prospected_duration(datetime.date(2012,1,1)) == 24
    """
    assert is_supported_attribute(column_attribute), 'The given attribute should be a valid column attribute'

    class attribute_prospection(abstract_attribute_prospection):

        attribute = column_attribute
        for_transition_types = transition_types

    return attribute_prospection

def get_prospected_value(attribute, target, at, transition_type=None, default=None, **kwargs):
    """
    Helper method to extract the prospected value for the given instrumented attribute on a target entity, if applicable.

    :param attribute: an instance of orm.attributes.InstrumentedAttribute that maps to a column of the provided target entity.
    :param target: the entity instance to inspect the prospected value on.
    :param at: the date on which the prospection should take place.
    :param transition_type: optional transition type that may influence the prospection.
    :param default: the default value to return if the given attribute has no applicable prospection, None by default.
    """
    if is_supported_attribute(attribute):
        column = attribute.prop.columns[0]
        if 'prospection' in column.info:
            prospection = column.info['prospection']
            attribute_prospection = prospection.get(transition_type, prospection.get(None))
            if attribute_prospection is not None:
                return attribute_prospection.__call__(target, at, **kwargs)
    return default
