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

    def __init__(self, func):
        self.func = func
        self.register(self)

    @classmethod
    def register(cls, self):
        column = cls.attribute.prop.columns[0] if isinstance(cls.attribute, orm.attributes.InstrumentedAttribute) else cls.attribute
        column.info['prospection'] = self

    def __call__(self, target, at, transition_type=None, **kwargs):
        target_cls = type(target)

        if transition_type is not None:
            # If the transition_type is provided, assert that the target class has
            # its transition types defined, and that the provided one is part of those.
            assert target_cls.transition_types is not None, '{} has no transition_types configured in its __entity_args__'.format(target_cls)
            assert transition_type in target_cls.transition_types, '{} is not a valid transition type for {}'.format(transition_type, target_cls)

        if None not in (target, at):
            return self.func(target, at, transition_type, **kwargs)

    def __get__(self, instance, owner):
        return types.MethodType(self, instance) if instance is not None else self

def prospected_attribute(column_attribute):
    """
    Function decorator that supports registering prospected behaviour for one of the instrumented
    column attribute of an Entity class.
    The user-defined function expects an instance of the target entity, the prospection date and an optional transition type.
    That function will then be decorated/wrapped to be undefined if the provided target instance or prospection date are undefined.
    The transition types used are those that can be registered in the target entity's __entity_args__, and represent the possible
    state transitions of the entity's instances, which may influence the prospection.

    :example:
     |
     |  class ConcreteEntity(Entity):
     |
     |     __entity_args__ = {
     |        'transition_types': types.transition_types,
     |     }
     |
     |     apply_from_date = schema.Column(sqlalchemy.types.Date())
     |     duration = schema.Column(sqlalchemy.types.Integer())
     |
     |     @prospected_attribute(duration)
     |     def prospected_duration(self, at, transition_type=None):
     |        if transition_type == types.transition_types.certain_type:
     |            return self.duration
     |        return months_between_dates(self.apply_from_date, at)
     |
     |  ConcreteEntity(apply_from_date=datetime.date(2012,1,1), duration=24).prospected_duration(datetime.date(2013,1,1)) == 12
     |  ConcreteEntity(apply_from_date=datetime.date(2012,1,1), duration=24).prospected_duration(datetime.date(2013,1,1), types.transition_types.certain_type.name) == 24
     |  ConcreteEntity(apply_from_date=datetime.date(2012,1,1), duration=24).prospected_duration(None) == None
     |  ConcreteEntity(apply_from_date=None, duration=24).prospected_duration(None) == 24
    """
    assert is_supported_attribute(column_attribute), 'The given attribute should be a valid column attribute'

    class attribute_prospection(abstract_attribute_prospection):

        attribute = column_attribute

    return attribute_prospection

def get_prospected_value(attribute, target, at, transition_type=None, default=None, **kwargs):
    """
    Helper method to extract the prospected value for the given instrumented attribute on a target entity, if applicable.
    Note: an attribute without registered prospected behaviour registered is assumed to remain constant in time.

    :param attribute: an instance of orm.attributes.InstrumentedAttribute that maps to a column of the provided target entity.
    :param target: the entity instance to inspect the prospected value on.
    :param at: the date on which the prospection should take place.
    :param transition_type: optional transition type that may influence the prospection.
    :param default: the default value to return if the given attribute has no applicable prospection, None by default.
    """
    if is_supported_attribute(attribute):
        column = attribute.prop.columns[0]
        if 'prospection' in column.info:
            return column.info['prospection'].__call__(target, at, transition_type, **kwargs)
    return default
