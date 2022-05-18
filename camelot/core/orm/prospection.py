import functools

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
    """

    assert isinstance(attribute, (sql.schema.Column, orm.attributes.InstrumentedAttribute))
    class decorator:

        def __init__(self, func):
            self.func = func
            self.owner = None

        def __get__(self, instance, owner):
            mapper = orm.class_mapper(owner)
            class_attribute = mapper.get_property(attribute.key).class_attribute

            @functools.wraps(self.func)
            def wrapper(target, at):
                if None not in (target, at):
                    current_value = class_attribute.__get__(target, None)
                    if self.owner._prospection_applicable(target, at):
                        return self.func(target, at)
                    return current_value
            return wrapper

        def __set_name__(self, owner, name):
            # Descriptor method available since Python 3.6+ that gets called when the owning class gets created,
            # and the descriptor has been assigned to a name.
            # At that point, we can assign the owning class.
            self.owner = owner

    return decorator
