"""
Server side register for objects whose reference is send to the client.
Inspired by the Corba/Java NamingContext.
"""
from __future__ import annotations

import datetime
import decimal
import functools
import logging
import typing

from enum import Enum
from decimal import Decimal
from sqlalchemy import inspect

from .singleton import Singleton

LOGGER = logging.getLogger(__name__)

# Composite name represents a sequence of composed atomic names
CompositeName = typing.Tuple[str, ...]
# Unified name that can be either an atomic name or a composte name.
Name = typing.Union[str, CompositeName]

class BindingType(Enum):

    named_object = 1
    named_context = 2

class NamingException(Exception):

    def __init__(self, message, *args, reason=None, **kwargs):
        assert isinstance(message, self.Message)
        assert reason is None or isinstance(reason, self.Message)
        self.message_text = message.value.format(*args, **kwargs)
        if reason is not None:
            self.message_text = self.message_text + ': ' + reason.value
        super().__init__(self.message_text)
        self.message = message
        self.reason = reason

    class Message(Enum):

        unbound = 'Can not proceed: NamingContext is not bound to another context yet'
        invalid_binding_type = 'Invalid binding type, should be a member of `camelot.core.naming.BindingType'
        name_not_found = "Name '{}' does not identify a {} binding"
        already_bound = "A {} is already bound under the name '{}'"
        context_expected = 'Expected an instance of `camelot.core.naming.AbstractNamingContext`, instead got {0}'
        binding_immutable = 'Can not proceed: the {} binding under name {} is immutable'

        invalid_name = 'The given name is invalid'
        # Invalid name reasons
        invalid_name_type = 'name should an atomic name or a composite name'
        invalid_atomic_name = 'atomic name should be a string'
        invalid_atomic_name_length = 'atomic name should contain at least 1 character'
        invalid_atomic_name_numeric = 'atomic name should be numeric'
        invalid_composite_name = 'composite name should be a tuple'
        invalid_composite_name_length = 'composite name should be composed of at least 1 atomic part'
        invalid_composite_name_parts = 'composite name should be composed of valid atomic parts'
        singular_name_expected = 'only atomic or singular composite names are supported by this endpoint naming context'

class UnboundException(NamingException):
    """A NamingException that is thrown when a NamingContext bound to another NamingContext yet."""

    def __init__(self):
        super().__init__(NamingException.Message.unbound)

class ImmutableBindingException(NamingException):
    """A NamingException that is thrown when trying to mutate an immutable binding."""

    def __init__(self, binding_type: BindingType, name):
        assert binding_type in BindingType
        super().__init__(NamingException.Message.binding_immutable, name, binding_type.name.replace('_', ' '))
        self.name = name
        self.binding_type = binding_type

class NameNotFoundException(NamingException):
    """A NamingException that is thrown when no associated binding could be identified for a name."""

    def __init__(self, name, binding_type: BindingType):
        assert binding_type in BindingType
        super().__init__(NamingException.Message.name_not_found, name, binding_type.name.replace('_', ' '))
        self.name = name
        self.binding_type = binding_type

class AlreadyBoundException(NamingException):
    """
    A NamingException that is thrown if an attempt is made to bind an object
    in the NamingContext to a name that already has an associated binding.
    """

    def __init__(self, name, binding_type: BindingType):
        assert binding_type in BindingType
        super().__init__(NamingException.Message.already_bound, binding_type.name.replace('_', ' '), name)

class AbstractNamingContext(object):
    """
    Interface for a naming context, which consists of methods for
    adding, examining and updating name-to-object bindings, as well as subcontexts.

    Names
    -----
    Each name passed as an argument to a context method should be relative to that context.
    This can be both an atomic string name, for binding on the context itself,
    or composite names (composed of multiple atomic parts), for binding through subcontexts using the recursive resolve.
    Internally, a context always uses the composite form of names, even when provided with atomic values.

    Each context also keeps track of its fully qualified composite name, once it gets bound to another context.
    This composite name is always relative to the initial naming context :see: camelot.core.naming.InitialNamingContext.
    The context uses this name to compose and return the fully qualified name of created bindings,
    which can thus be used to resolve them afterwards on the initial naming context.

    Exceptions
    ----------
    All the methods in this interface can throw a NamingException or any of its subclasses.
    See NamingException and their subclasses for details on each exception.
    """

    def __init__(self):
        self._name = None

    @classmethod
    def validate_atomic_name(cls, name: str):
        """
        Validate an atomic name for this naming context.
        This method will be used to validate names used within this context,
        or by contexts higher up that have this context bound as one of their subcontexts,
        to validate an atomic part of a composite name with.

        :raises:
            NamingException NamingException.Message.invalid_atomic_name when the given name is not a string instance.
            NamingException NamingException.Message.invalid_atomic_name when the given name is the empty string.
        """
        if not isinstance(name, str):
            raise NamingException(NamingException.Message.invalid_name, reason=NamingException.Message.invalid_atomic_name)
        elif len(name) == 0:
            raise NamingException(NamingException.Message.invalid_name, reason=NamingException.Message.invalid_atomic_name_length)

    @classmethod
    def validate_composite_name(cls, name: CompositeName) -> bool:
        """
        Validate a composite name for this naming context.
        This method will be used to validate composite names used within this context,
        or by contexts higher up that have this context bound as one of their subcontexts,
        to validate composite names with.

        :raises:
            NamingException NamingException.Message.invalid_composite_name when the given composite name is not a tuple instance.
            NamingException NamingException.Message.invalid_composite_name_length when the given composite name has no composed atomic parts.
            NamingException NamingException.Message.invalid_composite_name_parts when the given composite name is not composed of valid atomic parts.
        """
        if not isinstance(name, tuple):
            raise NamingException(NamingException.Message.invalid_name, reason=NamingException.Message.invalid_composite_name)
        elif len(name) == 0:
            raise NamingException(NamingException.Message.invalid_name, reason=NamingException.Message.invalid_composite_name_length)
        elif not all([isinstance(name_part, str) for name_part in name]):
            raise NamingException(NamingException.Message.invalid_name, reason=NamingException.Message.invalid_composite_name_parts)

    @classmethod
    def get_composite_name(cls, name: Name) -> CompositeName:
        """
        Utility method that returns the composite form of the given name (atomic or composite).
        The composite result will also be generally validated for use within this context,
        as well as the the first composed atomic part (as that is the only one used directly on this context).
        Any other atomic parts can only be validated be the corresponding subcontext after the recursive resolve,
        as its validation might differ from this one.

        :param name: the name to convert, atomic or composite.

        :return: the composite form of the provided name.

        :raises:
            NamingException NamingException.Message.invalid_name: The supplied name or one of its composed part is invalid for this context.
        """
        if isinstance(name, str):
            cls.validate_atomic_name(name)
            return tuple([name])
        if isinstance(name, tuple):
            cls.validate_composite_name(name)
            cls.validate_atomic_name(name[0])
            return name
        raise NamingException(NamingException.Message.invalid_name, reason=NamingException.Message.invalid_name_type)

    def check_bounded(func):
        # Validation decorator that checks and raises when this context is unbound.
        @functools.wraps(func)
        def wrapper(self, *args, **kwargs):
            if self._name is None:
                raise UnboundException()
            return func(self, *args, **kwargs)
        return wrapper

    @check_bounded
    def get_qual_name(self, name: Name) -> CompositeName:
        """
        Convert the given name relative to this NamingContext into its
        fully qualified composite name relative to the initial naming context.
        Checks will be performed on the validity of the provided name,
        but not on its presence in the context hierarchy.
        The resulting composite name is thus not guaranteed to resolve into a bound object.

        :param name: the name, atomic or composite, and relative to this naming context.

        :return: the fully qualified composite form of the provided name, relative to the initial naming context.

        :raises:
            UnboundException NamingException.unbound: if this NamingContext has not been bound to a name yet.
            NamingException NamingException.Message.invalid_name: The supplied name is invalid (i.e., is None or has length less than 1).
        """
        name = self.get_composite_name(name)
        return (*self._name, *name)

    def bind(self, name: Name, obj: object, immutable=False) -> CompositeName:
        """
        Creates a binding of a name and an object in the naming context.

        :param name: Name of the object, atomic or composite, and relative to this naming context.
        :param obj: The object to bind with the given name
        :param immutable: flag that indicates whether the created binding should be immutable.

        :return: The fully qualified composite name of the resulting binding, relative to the initial naming context.
        """
        raise NotImplementedError

    def rebind(self, name: Name, obj) -> CompositeName:
        """
        Creates a binding of a name and an object in the naming context even if the name is already bound in the context.

        :param name: Name of the object, atomic or composite, and relative to this naming context.
        :param obj: The object to bind with the given name

        :return: The fully qualified composite name of the resulting binding, relative to the initial naming context.
        """
        raise NotImplementedError

    def bind_context(self, name: Name, context: AbstractNamingContext, immutable=False) -> CompositeName:
        """
        Names an object that is a naming context.
        Naming contexts that are bound using bind_context() participate in recursive name resolution when composite names are passed to be resolved.

        :param name: Name of the object, atomic or composite, and relative to this naming context.
        :param obj: The AbstractNamingContext obj to bind with the given name
        :param immutable: flag that indicates whether the created context binding should be immutable.

        :return: The fully qualified composite name of the resulting binding, relative to the initial naming context.
        """
        raise NotImplementedError

    def rebind_context(self, name: Name, context: AbstractNamingContext) -> CompositeName:
        """
        Creates a binding of a name and a naming context in the naming context even if the name is already bound in the context.

        :param name: Name of the object, atomic or composite, and relative to this naming context.
        :param obj: The AbstractNamingContext obj to bind with the given name

        :return: The fully qualified composite name of the resulting binding, relative to the initial naming context.
        """
        raise NotImplementedError

    def new_context(self) -> AbstractNamingContext:
        """
        Create and return a new instance of this context class.

        :return: the created context
        """
        raise NotImplementedError

    def bind_new_context(self, name: Name, immutable=False) -> AbstractNamingContext:
        """
        Creates a new context and binds it to this context under the provided atomic name.

        :param name: Name, actomic and compose, and relative to this naming context, to bind the created context to this naming context.
        :param immutable: flag that indicates whether the created context should be bound immutable.

        :return: the created context, bound to this context.
        """
        raise NotImplementedError

    def unbind(self, name: Name) -> None:
        """
        Removes a named binding from the context.

        :param name: Name of the object, atomic or composite, and relative to this naming context.
        """
        raise NotImplementedError

    def unbind_context(self, name: Name) -> None:
        """
        Removes a name context binding from the context.

        :param name: Name of the context, atomic or composite.
        """
        raise NotImplementedError

    def resolve(self, name: Name) -> object:
        """
        Retrieve the object bound to a name in the context. The given name must exactly match the bound name.

        :param name: Name of the object, atomic or composite, and relative to this naming context.
        """
        raise NotImplementedError

    def resolve_context(self, name: Name) -> AbstractNamingContext:
        """
        Retrieve the context bound to a name in the context. The given name must exactly match the bound name.

        :param name: Name of the context, atomic or composite, and relative to this naming context.
        """
        raise NotImplementedError

    def list(self):
        """
        Returns the set of bindings in the naming context.
        """
        raise NotImplementedError

    def __contains__(self, name: Name):
        try:
            self.resolve(name)
            return True
        except (NameNotFoundException, KeyError):
            return False

    @classmethod
    def verbose_name(cls, route):
        return '/'.join(route)

    @check_bounded
    def dump_names(self):
        for name in self.list():
            LOGGER.info(self.verbose_name(*self._name, name))

class NamingContext(AbstractNamingContext):
    """
    Represents a naming context, which consists of a set of name-to-object bindings.
    It implements the AbstractNamingContext interface to provide methods for adding, examining and updating these bindings,
    as well as to define subcontexts that take part in recursive resolving of names.
    """

    def __init__(self):
        super().__init__()
        self._bindings = {btype: dict() for btype in BindingType}

    @AbstractNamingContext.check_bounded
    def bind(self, name: Name, obj: object, immutable=False) -> CompositeName:
        """
        Bind an object under a name in this NamingContext.
        If the name is atomic or composed out of a single atomic part, the given object will be bound with that atomic name to this NamingContext.
        In case it is composed out of multiple parts, the first part is resolved in this context, expecting the result to be a bound NamingContext,
        and the remaining parts are recursively bound in the resulting context.
        An exception is thrown if a binding with the supplied name already exists.
        If the object to be bound is a NamingContext it will not participate in a recursive resolve; use bind_context() instead for this behaviour.

        :param name: name under which the object will be bound, atomic or composite, and relative to this naming context.
        :param obj: the object reference to be bound.
        :param immutable: flag that indicates whether the object should be bound as immutable,
         which will throw a `camelot.core.naming.ImmutableBindingException` when trying to mutate the binding afterwards

        :return: the full qualified composite name of the bound object, relative to the initial naming context.

        :raises:
            UnboundException NamingException.unbound: if this NamingContext has not been bound to a name yet.
            NamingException NamingException.Message.invalid_name: The supplied name is invalid (i.e., is None or has length less than 1).
            NameNotFoundException NamingException.Message.name_not_found: if no binding was found for the supplied name.
            AlreadyBoundException NamingException.Message.already_bound : An object is already bound under the supplied name.
        """
        return self._add_binding(name, obj, False, BindingType.named_object, immutable)

    @AbstractNamingContext.check_bounded
    def rebind(self, name: Name, obj: object) -> CompositeName:
        """
        Bind an object under a name in this NamingContext.
        If the name is atomic or composed out of a single atomic part, the given object will be rebound with that atomic name to this NamingContext.
        In case it is composed out of multiple parts, the first part is resolved in this context, expecting a bound NamingContext,
        and the remaining parts are recursively rebound in that resulting context.
        If a binding under the supplied name already exists it will be unbounded first.
        If the object to be bound is a NamingContext it will not participate in the recursive resolve.

        :param name: name under which the object will be bound, atomic or composite, and relative to this naming context.
        :param obj: the object reference to be bound.

        :return: the full qualified composite name of the bound object, relative to the initial naming context.

        :raises:
            UnboundException NamingException.unbound: if this NamingContext has not been bound to a name yet.
            NamingException NamingException.Message.invalid_name: The supplied name is invalid (i.e., is None or has length less than 1).
            NameNotFoundException NamingException.Message.name_not_found: if no binding was found for the supplied name.
            ImmutableBindingException NamingException.Message.binding_immutable: when trying to rebind an immutable object binding.
        """
        return self._add_binding(name, obj, True, BindingType.named_object)

    @AbstractNamingContext.check_bounded
    def bind_context(self, name: Name, context: AbstractNamingContext, immutable=False) -> CompositeName:
        """
        Bind a NamingContext under a name in this NamingContext.
        If the name is atomic or composed out of a single atomic part, the given context will be bound with that atomic name to this NamingContext.
        In case it is composed out of multiple parts, the first part is resolved in this context, expecting a bound NamingContext,
        and the remaining parts are rebound in that resulting context.
        An exception is thrown if a binding with the supplied name already exists. The NamingContext will participate in recursive resolving.

        :param name: name under which the object will be bound, atomic or composite, and relative to this naming context.
        :param context: the NamingContext object reference to be bound.
        :param immutable: flag that indicates whether the context should be bound as immutable,
         which will throw a `camelot.core.naming.ImmutableBindingException` when trying to mutate the binding afterwards

        :return: the full qualified name of the bound object across the whole context hierarchy.

        :raises:
            UnboundException NamingException.unbound: if this NamingContext has not been bound to a name yet.
            NamingException NamingException.Message.invalid_name: when the supplied name is invalid (i.e., is None or has length less than 1).
            NamingException NamingException.Message.context_expected : when the given object is not a NamingContext.
            NameNotFoundException NamingException.Message.name_not_found: if no binding was found for the supplied name.
            AlreadyBoundException NamingException.Message.already_bound : when an object is already bound under the supplied name.
        """
        if not isinstance(context, AbstractNamingContext):
            raise NamingException(NamingException.Message.context_expected, context)
        return self._add_binding(name, context, False, BindingType.named_context, immutable)

    @AbstractNamingContext.check_bounded
    def rebind_context(self, name: Name, context: AbstractNamingContext) -> CompositeName:
        """
        Bind a NamingContext under a name in this NamingContext.
        If the name is atomic or composed out of a single atomic part, the given context will be rebound with that atomic name to this NamingContext.
        In case it is composed out of multiple parts, the first part is resolved in this context, expecting a bound NamingContext,
        If a binding under the supplied name already exists it will be unbound first.
        The NamingContext will participate in recursive resolving.

        :param name: name under which the object will be bound, atomic or composite, and relative to this naming context.
        :param context: the NamingContext object reference to be bound.

        :return: the full qualified composite name of the bound object, relative to the initial naming context.

        :raises:
            UnboundException NamingException.unbound: if this NamingContext has not been bound to a name yet.
            NamingException NamingException.Message.invalid_name: The supplied name is invalid (i.e., is None or has length less than 1).
            NamingException NamingException.Message.context_expected : when the given object is not a NamingContext.
            NameNotFoundException NamingException.Message.name_not_found: if no binding was found for the supplied name.
            AlreadyBoundException NamingException.Message.already_bound : when an object is already bound under the supplied name.
            ImmutableBindingException NamingException.Message.binding_immutable: when trying to rebind an immutable context binding.
        """
        if not isinstance(context, AbstractNamingContext):
            raise NamingException(NamingException.Message.context_expected, context)
        return self._add_binding(name, context, True, BindingType.named_context)

    def new_context(self) -> NamingContext:
        """
        Create and return a new instance of this context class.

        :return: an instance of `camelot.core.naming.NamingContext`
        """
        return self.__class__()

    @AbstractNamingContext.check_bounded
    def bind_new_context(self, name: Name, immutable=False) -> NamingContext:
        """
        Creates a new NamingContext, binds it in this NamingContext and returns it.
        This is equivalent to new_context(), followed by a bind_context() with the provided name for the newly created context.

        :param name: name under which the created NamingContext will be bound, atomic or composite, and relative to this naming context.
        :param immutable: flag that indicates whether the created naming context should be bound as immutable to this context,
         which will throw a `camelot.core.naming.ImmutableBindingException` when trying to mutate the binding afterwards.

        :return: an instance of `camelot.core.naming.NamingContext`

        :raises:
            UnboundException NamingException.unbound: if this NamingContext has not been bound to a name yet.
        """
        context = self.new_context()
        self.bind_context(name, context, immutable)
        return context

    @AbstractNamingContext.check_bounded
    def _add_binding(self, name: Name, obj, rebind: bool, binding_type: BindingType, immutable=False) -> CompositeName:
        """
        Helper method that implements the addition of all types of bindings.
        It resolves the name to make sure no binding exists already (in case of a bind and bind_context).
        If the name is atomic, or composed of only a single atomic part, the given object is bound with that name in this NamingContext.
        Otherwise, the first atomic part is resolved in this context and the bind is passed to the resulting NamingContext.

        :param name: name under which the object will be bound, atomic or composite, and relative to this naming context.
        :param obj: the object reference to be bound.
        :param rebind: flag indicating if an existing binding should be replaced or not.
        :param binding_type: the type of the binding to add, a member of `camelot.core.orm.BindingType`.
        :param immutable: flag that indicates whether the binding should be added as immutable, which will throw a `camelot.core.naming.ImmutableBindingException` when trying to mutate it afterwards

        :return: the full qualified composite name of the bound object, relative to the initial naming context.

        :raises:
            UnboundException NamingException.unbound: if this NamingContext has not been bound to a name yet.
            NamingException NamingException.Message.invalid_name: when the name is invalid (None or length less than 1).
            NameNotFoundException NamingException.Message.name_not_found: if no binding was found for the given name.
            AlreadyBoundException NamingException.Message.already_bound: when an object is already bound under the supplied name.
            NamingException NamingException.Message.invalid_binding_type: if the binding type is not a valid BindingType enum member.
            ImmutableBindingException NamingException.Message.binding_immutable: when trying to rebind an immutable binding.
        """
        name = self.get_composite_name(name)
        if binding_type not in BindingType:
            raise NamingException(NamingException.Message.invalid_binding_type)
        if len(name) == 1:
            # If binding, check if their exists one already
            if name[0] in self._bindings[binding_type]:
                if not rebind:
                    raise AlreadyBoundException(name[0], binding_type)
                else:
                    _, binding_immutable = self._bindings[binding_type][name[0]]
                    if binding_immutable:
                        raise ImmutableBindingException(binding_type, name[0])

            # Add the object and its mutability to the registry for the given binding_type.
            self._bindings[binding_type][name[0]] = (obj, immutable)
            # Determine the full qualified named of the bound object (extending that of this NamingContext).
            qual_name = self.get_qual_name(name[0])
            # If the object is a NamingContext, assign the qualified name.
            if binding_type == BindingType.named_context:
                if obj._name is not None:
                    raise AlreadyBoundException(name[0], binding_type)
                obj._name = qual_name
            return qual_name
        else:
            if name[0] not in self._bindings[BindingType.named_context]:
                raise NameNotFoundException(name[0], BindingType.named_context)
            context, _ = self._bindings[BindingType.named_context][name[0]]
            if binding_type == BindingType.named_context:
                if rebind:
                    return context.rebind_context(name[1:], obj)
                return context.bind_context(name[1:], obj)
            elif binding_type == BindingType.named_object:
                if rebind:
                    return context.rebind(name[1:], obj)
                return context.bind(name[1:], obj)

    @AbstractNamingContext.check_bounded
    def unbind(self, name: Name) -> None:
        """
        Removes an object binding from this NamingContext.
        If the name is atomic, or composed of only a single atomic part, the object binding under the given name will be removed from this NamingContext.
        In case it is composed out of multiple parts, the first part is resolved in this context, expecting a bound NamingContext,
        and the remaining parts are resolved in that resulting context.

        :param name: name under which the object should have been bound, atomic or composite, and relative to this naming context.

        :raises:
            UnboundException NamingException.unbound: if this NamingContext has not been bound to a name yet.
            NamingException NamingException.Message.invalid_name: when the name is invalid (None or length less than 1).
            NameNotFoundException NamingException.Message.name_not_found: if no binding was found for the given name.
            ImmutableBindingException NamingException.Message.binding_immutable: when trying to unbind an immutable object binding.
        """
        self._remove_binding(name, BindingType.named_object)

    @AbstractNamingContext.check_bounded
    def unbind_context(self, name: Name) -> None:
        """
        Remove a context binding from this NamingContext.
        If the name is atomic, or composed of only a single atomic part, the context binding under the given name will be removed from this NamingContext.
        In case it is composed out of multiple parts, the first part is resolved in this context, expecting a bound NamingContext,
        and the remaining parts are resolved in that resulting context.
        As a result of this removal, the found NamingContext will get unbound and not be usable unless its reassociated.

        :param name: name under which the context should have been bound, atomic or composite, and relative to this naming context.

        :raises:
            UnboundException NamingException.unbound: if this NamingContext has not been bound to a name yet.
            NamingException NamingException.Message.invalid_name: when the name is invalid (None or length less than 1).
            NameNotFoundException NamingException.Message.name_not_found: if no binding was found for the given name.
            ImmutableBindingException NamingException.Message.binding_immutable: when trying to unbind an immutable context binding.
        """
        self._remove_binding(name, BindingType.named_context)

    @AbstractNamingContext.check_bounded
    def _remove_binding(self, name: Name, binding_type: BindingType) -> None:
        """
        Helper method that supports removing all types of bindings from this NamingContext.
        If the name is atomic, or composed of only a single atomic part, the binding under the given name will be removed from this NamingContext.
        In case it is composed out of multiple parts, the first part is resolved in this context, expecting a bound NamingContext,
        and the remaining parts are delegated for removal to the resulting context.

        :param name: name of the binding to remove, atomic or composite, and relative to this naming context.
        :param binding_type: the type of the binding to remove, a member of `camelot.core.orm.BindingType.

        :raises:
            UnboundException NamingException.unbound: if this NamingContext has not been bound to a name yet.
            NamingException NamingException.Message.invalid_name: when the name is invalid (None or length less than 1).
            NamingException NamingException.Message.invalid_binding_type: if the binding type is not a valid BindingType enum member.
            NameNotFoundException NamingException.Message.name_not_found: if no binding was found for the given name.
            ImmutableBindingException NamingException.Message.binding_immutable: when trying to remove an immutable binding.
        """
        name = self.get_composite_name(name)
        if binding_type not in BindingType:
            raise NamingException(NamingException.Message.invalid_binding_type)
        if len(name) == 1:
            if name[0] not in self._bindings[binding_type]:
                raise NameNotFoundException(name[0], binding_type)
            obj, immutable = self._bindings[binding_type][name[0]]
            if immutable:
                raise ImmutableBindingException(binding_type, name[0])
            self._bindings[binding_type].pop(name[0])
            if binding_type == BindingType.named_context:
                obj._name = None
        else:
            if name[0] not in self._bindings[BindingType.named_context]:
                raise NameNotFoundException(name[0], BindingType.named_context)
            context, _ = self._bindings[BindingType.named_context][name[0]]
            if binding_type == BindingType.named_context:
                context.unbind_context(name[1:])
            elif binding_type == BindingType.named_object:
                context.unbind(name[1:])

    @AbstractNamingContext.check_bounded
    def resolve(self, name: Name) -> object:
        """
        Resolve a name in this NamingContext and return the bound object.
        It will throw appropriate exceptions if not found.

        :param name: name under which the object should have been bound, atomic or composite, and relative to this naming context.

        :return: the object that was bound under the given name.

        :raises:
            UnboundException NamingException.unbound: if this NamingContext has not been bound to a name yet.
            NamingException NamingException.Message.invalid_name: when the name is invalid (None or length less than 1).
            NameNotFoundException NamingException.Message.name_not_found: if no binding was found for the given name.
        """
        return self._resolve_binding(name, BindingType.named_object)

    @AbstractNamingContext.check_bounded
    def resolve_context(self, name: Name) -> AbstractNamingContext:
        """
        Resolve a name in this NamingContext and return the bound object, expecting it to be a NamingContext.
        It will throw appropriate exceptions if not found.

        :param name: name under which the context should have been bound, atomic or composite, and relative to this naming context.

        :raises:
            UnboundException NamingException.unbound: if this NamingContext has not been bound to a name yet.
            NamingException NamingException.Message.invalid_name: when the name is invalid (None or length less than 1).
            NameNotFoundException NamingException.Message.name_not_found: if no binding was found for the given name.
        """
        return self._resolve_binding(name, BindingType.named_context)

    @AbstractNamingContext.check_bounded
    def _resolve_binding(self, name: Name, binding_type: BindingType) -> object:
        """
        Helper method that implements the lookup of all types of bindings, returning the bound object.
        It will throw appropriate exceptions if not found.

        :param name: name under which the object should have been bound, atomic or composite, and relative to this naming context.
        :param binding_type: the type of binding to resolve, a member of `camelot.core.orm.BindingType.

        :return: the object that was bound under the given name.

        :raises:
            UnboundException NamingException.unbound: if this NamingContext has not been bound to a name yet.
            NamingException NamingException.Message.invalid_name: when the name is invalid (None or length less than 1).
            NamingException NamingException.Message.invalid_binding_type: if the binding type is not a valid BindingType enum member.
            NameNotFoundException NamingException.Message.name_not_found: if no binding was found for the given name.
        """
        name = self.get_composite_name(name)
        if binding_type not in BindingType:
            raise NamingException(NamingException.Message.invalid_binding_type)
        if len(name) == 1:
            if name[0] not in self._bindings[binding_type]:
                raise NameNotFoundException(name[0], binding_type)
            return self._bindings[binding_type][name[0]][0]
        else:
            if name[0] not in self._bindings[BindingType.named_context]:
                raise NameNotFoundException(name[0], BindingType.named_context)
            context, _ = self._bindings[BindingType.named_context][name[0]]
            if binding_type == BindingType.named_context:
                return context.resolve_context(name[1:])
            elif binding_type == BindingType.named_object:
                return context.resolve(name[1:])

    def list(self):
        return self._bindings[BindingType.named_object].keys()

class EndpointNamingContext(AbstractNamingContext):
    """
    Interface for a naming context that only supports binding and resolving objects/values,
    and not subcontexts.
    As such, they are by definition always an 'endpoint' context in a naming hierachy.
    Because no recursive resolve is possible, names used by this context are validated to be singular.
    """

    @classmethod
    def validate_atomic_name(cls, name: str) -> bool:
        """
        Customized atomic name validation for this endpoint naming context.
        This enforces less constraints than the default validation inherited from ´camelot.core.naming.AbstractNamingContext´,
        in that it allows for the empty string as a valid atomic name,
        as that to should be able to be resolved by the corresponding String constant naming context.

        :raises:
            NamingException NamingException.Message.invalid_atomic_name when the given name is not a string instance.
        """
        if not isinstance(name, str):
            raise NamingException(NamingException.Message.invalid_name, reason=NamingException.Message.invalid_atomic_name)

    @classmethod
    def validate_composite_name(cls, name: CompositeName) -> bool:
        """
        Customized composite name validation for this endpoint naming context.
        This expands on the default composite name validation inherited from ´camelot.core.naming.AbstractNamingContext´
        in that it only allows singular composite names, as this context by definition is an endpoint in the context hierarchy.

        :raises:
            NamingException NamingException.Message.invalid_composite_name when the given composite name is not a tuple instance.
            NamingException NamingException.Message.invalid_composite_name_length when the given composite name has no composed atomic parts.
            NamingException NamingException.Message.invalid_composite_name_parts when the given composite name is not composed of valid atomic parts.
            NamingException NamingException.Message.singular_name_expected when the given composite name is not singular.
        """
        super().validate_composite_name(name)
        if len(name) != 1:
            raise NamingException(NamingException.Message.invalid_name, reason=NamingException.Message.singular_name_expected)

class ConstantNamingContext(EndpointNamingContext):
    """
    Represents a stateless endpoint naming context, which handles resolving objects/values of a certain immutable python type.
    Currently, those constant values are considered to be integers, strings, booleans or float.
    """

    def __init__(self, constant_type):
        super().__init__()
        assert constant_type in (int, str, bool, float, Decimal)
        self.constant_type = constant_type

    @AbstractNamingContext.check_bounded
    def resolve(self, name: Name) -> object:
        """
        Resolve a name in this ConstantNamingContext and return the bound object.
        It will throw appropriate exceptions if the resolution failed.

        :param name: name under which the object should have been bound, atomic or composite, and relative to this naming context.

        :return: the bound object, an instance of this ConstantNamingContext's constant_type.

        :raises:
            UnboundException NamingException.unbound: if this NamingContext has not been bound to a name yet.
            NamingException NamingException.Message.invalid_name: when the name is invalid.
            NameNotFoundException NamingException.Message.name_not_found: if no binding was found for the given name.
        """
        name = self.get_composite_name(name)
        try:
            return self.constant_type(name[0])
        except (ValueError, decimal.InvalidOperation):
            raise NameNotFoundException(name[0], BindingType.named_object)

class DatetimeNamingContext(EndpointNamingContext):
    """
    Represents a stateless endpoint naming context, which handles resolving ´datetime.datetime´ objects/values.
    """

    _format = '%Y-%m-%d'

    @AbstractNamingContext.check_bounded
    def resolve(self, name: Name) -> object:
        """
        Resolve a name in this DatetimeNamingContext and return the bound object.
        It will throw appropriate exceptions if the resolution failed.

        :param name: name under which the object should have been bound, atomic or composite, and relative to this naming context.

        :return: the bound object, an instance of ´datetime.datetime´.

        :raises:
            UnboundException NamingException.unbound: if this NamingContext has not been bound to a name yet.
            NamingException NamingException.Message.invalid_name: when the name is invalid.
            NameNotFoundException NamingException.Message.name_not_found: if no binding was found for the given name.
        """
        name = self.get_composite_name(name)
        try:
            return datetime.datetime.strptime(name[0], self._format)
        except ValueError:
            raise NameNotFoundException(name[0], BindingType.named_object)

class DateNamingContext(DatetimeNamingContext):
    """
    Represents a stateless endpoint naming context, which handles resolving ´datetime.date´ objects/values.
    """

    _format = '%Y-%m-%d %H:%M:%S'

    @AbstractNamingContext.check_bounded
    def resolve(self, name: Name) -> object:
        """
        Resolve a name in this DateNamingContext and return the bound object.
        It will throw appropriate exceptions if the resolution failed.

        :param name: name under which the object should have been bound, atomic or composite, and relative to this naming context.

        :return: the bound object, an instance of ´datetime.date´.

        :raises:
            UnboundException NamingException.unbound: if this NamingContext has not been bound to a name yet.
            NamingException NamingException.Message.invalid_name: when the name is invalid.
            NameNotFoundException NamingException.Message.name_not_found: if no binding was found for the given name.
        """
        return super().resolve(name).date()

class EntityNamingContext(EndpointNamingContext):
    """
    Represents a stateless endpoint naming context, which handles resolving instances of an Entity.
    """

    def __init__(self, entity):
        super().__init__()
        from camelot.core.orm import EntityBase
        assert issubclass(entity, EntityBase)
        self.entity = entity

    @classmethod
    def validate_atomic_name(cls, name: str) -> bool:
        """
        Customized atomic name validation for this entity naming context that enforces
        the atomic names used by this context to be numeric, as they are used as primary keys
        to query entity instances with.

        :raises:
            NamingException NamingException.Message.invalid_atomic_name_numeric when the given name is not numeric.
        """
        super().validate_atomic_name(name)
        if not name.isdecimal():
            raise NamingException(NamingException.Message.invalid_name, reason=NamingException.Message.invalid_atomic_name_numeric)

    @AbstractNamingContext.check_bounded
    def resolve(self, name: Name) -> object:
        """
        Resolve a name in this EntityNamingContext and return the bound object.
        The name should be singular and its atomic form numeric, as it is used
        as the primary key to query the corresponding instance with of the entity of this naming context.

        It will throw appropriate exceptions if the resolution failed.

        :param name: name under which the object should have been bound, atomic or composite, and relative to this naming context.

        :return: the bound object, an instance of this EntityNamingContext's entity class.

        :raises:
            UnboundException NamingException.unbound: if this NamingContext has not been bound to a name yet.
            NamingException NamingException.Message.invalid_name: when the name is invalid.
            NameNotFoundException NamingException.Message.name_not_found: if no binding was found for the given name.
        """
        from camelot.core.orm import Session
        name = self.get_composite_name(name)
        instance = Session().query(self.entity).get(name[0])
        if instance is None:
            raise NameNotFoundException(name[0], BindingType.named_object)
        return instance

class InitialNamingContext(NamingContext, metaclass=Singleton):
    """
    Singleton class that is the starting context for performing naming operations.
    All naming operations are relative to a context.
    This initial context implements the NamingContext interface and provides the starting point for resolution of names.
    """

    def __init__(self):
        super().__init__()
        # Initialize the name of this InitialNamingContext to the empty tuple,
        # so that it becomes bounded but does not contribute to the full composite name
        # resolution of subcontexts.
        self._name = tuple()

        # Add immutable bindings for constants' values and contexts for each supported 'constant' python type.
        constants = self.bind_new_context('constant', immutable=True)
        for constant_type in (str, int, Decimal): # Do not support floats, as vFinance uses Decimals throughout
            constants.bind_context(constant_type.__name__.lower(), ConstantNamingContext(constant_type), immutable=True)
        constants.bind('null', None, immutable=True)
        constants.bind('true', True, immutable=True)
        constants.bind('false', False, immutable=True)
        self.bind_new_context('entity', immutable=True)
        self.bind_new_context('object', immutable=True)

    def new_context(self) -> NamingContext:
        """
        Create and return a new `camelot.core.naming.NamingContext` instance.
        Note that this does not create a new InitialNamingContext instance,
        as this is inherently impossible because of its singleton nature.

        :return: an instance of `camelot.core.naming.NamingContext`
        """
        return NamingContext()

    def _bind_object(self, obj):
        """
        Helper method for binding any type of python object under the appropriate name.
        This functionality is meant for backend binding of objects and will always perform a mutable bind.

        :param obj: the object to be bound.

        :return: the full qualified composite name of the bound object, relative to the initial naming context.

        :raises:
            UnboundException NamingException.unbound: if this NamingContext has not been bound to a name yet.
        """
        from camelot.core.orm import Entity
        if obj is None:
            return ('constant', 'null')
        if isinstance(obj, bool):
            return ('constant', 'true' if obj else 'false')
        if isinstance(obj, (str, int, Decimal)):
            return ('constant', type(obj).__name__.lower(), str(obj))
        if isinstance(obj, Entity):
            # TBD: possibly move the context specific object validations to the respective context?
            if not inspect(obj).persistent or obj.id is None:
                raise NotImplementedError('Only persistent entity instances are supported')
            entity = type(obj)
            return ('entity', entity.__tablename__, entity.__name__, str(obj.id))
        if isinstance(obj, float):
            raise NotImplementedError('Use Decimal instead')
        LOGGER.warn('Binding non-delegated object of type {}'.format(type(obj)))
        # TBD: possibly put objects in a seperate objects subcontext?
        return self.rebind(('object', str(id(obj))), obj)

initial_naming_context = InitialNamingContext()
