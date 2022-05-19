import functools

from camelot.model.authentication import end_of_times
from sqlalchemy import orm, sql

def prospective_attribute(attribute):
    """
    Function decorator that supports registering prospective behaviour for one of the instrumented
    column attribute of an Entity class.
    The user-defined function expects an instance of the target entity and the prospection date,
    and will be decorated/wrapped with the following behaviour:

      * the return value will be undefined if any of the arguments are undefined
      * the return value will be the current value of the given column attribute on the target instance,
        if prospection on the instance is not applicable.
        A default _prospection_applicable method is provided on each Entity class by `orm.entity.EntityMeta` metaclass,
        but can be customized if needed on the corresponding entity.

    This function decorator requires the application_date of the target Entity class to be registered in its __entity_args__.
    """
    assert isinstance(attribute, (sql.schema.Column, orm.attributes.InstrumentedAttribute))
    class decorator:

        def __init__(self, func):
            self.func = func
            self.owner = None

        def __get__(self, instance, owner):
            mapper = orm.class_mapper(owner)
            class_attribute = mapper.get_property(attribute.key).class_attribute
            assert owner._get_entity_arg('application_date') is not None, \
                   "Defining prospective attributes requires the application_date "\
                   "to be registered in the Entity's __entity_args__."
            application_date_prop = mapper.get_property(owner._get_entity_arg('application_date').key)

            @functools.wraps(self.func)
            def wrapper(target, at):
                application_date = application_date_prop.class_attribute.__get__(target, None)
                if None not in (target, at):
                    current_value = class_attribute.__get__(target, None)
                    # The prospection should only be possible if the target's is applicable.
                    # Otherwise, the current value is returned.
                    if not (application_date >= end_of_times() or at < application_date):
                        return self.func(target, at)
                    return current_value
            return wrapper

        def __set_name__(self, owner, name):
            # Descriptor method available since Python 3.6+ that gets called when the owning class gets created,
            # and the descriptor has been assigned to a name.
            # At that point, we can assign the owning class.
            self.owner = owner

    return decorator
