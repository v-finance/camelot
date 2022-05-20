import functools
import types

from camelot.model.authentication import end_of_times
from sqlalchemy import orm, sql

class abstract_attribute_prospection(object):
    """
    Abstract function decorator that supports registering prospected behaviour for one of the instrumented
    column attribute of an Entity class.
    """

    attribute = None

    def __init__(self, func):
        assert self.attribute is not None
        self.func = func
        self.owner = None

    def __call__(self, target, at):
        assert isinstance(target, self.owner)
        target_cls = type(target)
        mapper = orm.class_mapper(target_cls)
        class_attribute = mapper.get_property(self.attribute.key).class_attribute
        assert target_cls._get_entity_arg('application_date') is not None, \
               "Defining prospective attributes requires the application_date "\
               "to be registered in the Entity's __entity_args__."
        application_date_prop = mapper.get_property(target_cls._get_entity_arg('application_date').key)
        application_date = application_date_prop.class_attribute.__get__(target, None)
        if None not in (target, at):
            current_value = class_attribute.__get__(target, None)
            # The prospection should only be possible if the target's is applicable.
            # Otherwise, the current value is returned.
            if application_date is not None and not (application_date >= end_of_times() or at < application_date):
                return self.func(target, at)
            return current_value

    def __get__(self, instance, owner):
        return types.MethodType(self, instance) if instance is not None else self

    def __set_name__(self, owner, name):
        # Descriptor method available since Python 3.6+ that gets called when the owning class gets created,
        # and the descriptor has been assigned to a name.
        # At that point, we can assign the owning class.
        self.owner = owner

def prospected_attribute(column_attribute):
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
    assert isinstance(column_attribute, (sql.schema.Column, orm.attributes.InstrumentedAttribute))
    class attribute_prospection(abstract_attribute_prospection):
        attribute = column_attribute

    return attribute_prospection
