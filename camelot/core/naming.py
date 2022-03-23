"""
Server side register for objects whose reference is send to the client.
Inspired by the Corba/Java NamingContext.
"""
from __future__ import annotations

import decimal
import functools
import logging
import typing

from enum import Enum
from decimal import Decimal

from .singleton import Singleton

LOGGER = logging.getLogger(__name__)

Name = typing.Union[str, typing.Tuple[str, ...]]

class BindingType(Enum):

    named_object = 1
    named_context = 2

class NamingException(Exception):

    def __init__(self, message, *args, reason=None, **kwargs):
        assert isinstance(message, self.Message)
        assert reason is None or isinstance(reason, self.Message)
        self.message_text = message.value.format(*args, **kwargs)
        if reason is not None:
            self.message_text = self.message_text + ': ' + reason
        super().__init__(self.message_text)
        self.message = message
        self.reason = reason

    class Message(Enum):

        unbound = 'Can not proceed: NamingContext is not bound to another context yet'
        invalid_name = 'The given name is invalid'
        invalid_binding_type = 'Invalid binding type, should be a member of `camelot.core.naming.BindingType'
        name_not_found = "Name '{}' does not identify a {} binding"
        already_bound = "A {} is already bound under the name '{}'"
        context_expected = 'Expected an instance of `camelot.core.naming.AbstractNamingContext`, instead got {0}'

class UnboundException(NamingException):
    """A NamingException that is thrown when a NamingContext bound to another NamingContext yet."""

    def __init__(self):
        super().__init__(NamingException.Message.unbound)

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
    Each name passed as an argument to a context method is relative to that context.
    A context keeps track of its fully qualified name, once bounded to another context,
    so as to return the fully qualified name of bindings where needed.
    Both singular textual names, as composite names (tuples) for recursive resolving through subcontexts, are supported.

    Exceptions
    ----------
    All the methods in this interface can throw a NamingException or
    any of its subclasses. See NamingException and their subclasses
    for details on each exception.
    """

    def __init__(self):
        self._name = None

    @classmethod
    def _assert_valid_name(cls, name:Name):
        """
        Helper method that validates the given (composite) name and returns its composite form.

        :raises:
            NamingException NamingException.Message.invalid_name: The supplied name is invalid (i.e., is None or has length less than 1).
        """
        if isinstance(name, str) and len(name):
            return tuple([name])
        if isinstance(name, tuple) and len(name):
            for _name in name:
                cls._assert_valid_name(_name)
            return name
        raise NamingException(NamingException.Message.invalid_name)

    def check_bounded(func):
        # Validation decorator that checks and raises when this context is unbound.
        @functools.wraps(func)
        def wrapper(self, *args, **kwargs):
            if self._name is None:
                raise UnboundException()
            return func(self, *args, **kwargs)
        return wrapper

    @check_bounded
    def get_qual_name(self, name: Name) -> tuple:
        """
        Convert the given binding name into its fully qualified composite name for this NamingContext.

        :param name: the name relative to this NamingContext.

        :return: the fully qualified composite form of the provided name

        :raises:
            UnboundException NamingException.unbound: if this NamingContext has not been bound to a name yet.
            NamingException NamingException.Message.invalid_name: The supplied name is invalid (i.e., is None or has length less than 1).
        """
        name = self._assert_valid_name(name)
        return (*self._name, *name)

    def bind(self, name: Name, obj) -> Name:
        """
        Creates a binding of a name and an object in the naming context.

        :param name: Name of the object
        :param obj: The object to bind with the given name

        :return: The fully qualified name of the resulting binding.
        """
        raise NotImplementedError

    def rebind(self, name: Name, obj) -> Name:
        """
        Creates a binding of a name and an object in the naming context even if the name is already bound in the context.

        :param name: Name of the object
        :param obj: The object to bind with the given name

        :return: The fully qualified name of the resulting binding.
        """
        raise NotImplementedError

    def bind_context(self, name: Name, context) -> Name:
        """
        Names an object that is a naming context. Naming contexts that are bound using bind_context() participate in name resolution when compound names are passed to be resolved.

        :param name: Name of the object
        :param obj: The AbstractNamingContext obj to bind with the given name

        :return: The fully qualified name of the resulting binding
        """
        raise NotImplementedError

    def rebind_context(self, name: Name, context) -> Name:
        """
        Creates a binding of a name and a naming context in the naming context even if the name is already bound in the context.

        :param name: Name of the object
        :param obj: The AbstractNamingContext obj to bind with the given name

        :return: The fully qualified name of the resulting binding
        """
        raise NotImplementedError

    def new_context(self):
        """
        Create and return a new instance of this context class.

        :return: the created context
        """
        raise NotImplementedError

    def bind_new_context(self, name) -> AbstractNamingContext:
        """
        Creates a new context and binds it to the name supplied as an argument.

        :return: the created context, bound to this context.
        """
        raise NotImplementedError

    def unbind(self, name: Name) -> None:
        """
        Removes a named binding from the context.

        :param name: Name of the object
        """
        raise NotImplementedError

    def unbind_context(self, name: Name) -> None:
        """
        Removes a name context binding from the context.

        :param name: Name of the context
        """
        raise NotImplementedError

    def resolve(self, name: Name) -> object:
        """
        Retrieve the object bound to a name in the context. The given name must exactly match the bound name.

        :param name: Name of the object
        """
        raise NotImplementedError

    def resolve_context(self, name: Name) -> AbstractNamingContext:
        """
        Retrieve the context bound to a name in the context. The given name must exactly match the bound name.

        :param name: Name of the context
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
    def bind(self, name, obj) -> Name:
        """
        Bind an object under a name in this NamingContext.
        If the name is singular (length of 1) the given object will be bound with the name in this NamingContext.
        In case it is composed out of multiple parts, the first part is resolved in this context, expecting a bound NamingContext,
        and the remaining parts are bound in that resulting context.
        An exception is thrown if a binding with the supplied name already exists.
        If the object to be bound is a NamingContext it will not participate in a recursive resolve; use bind_context() instead for this behaviour.

        :param name: name under which the object will be bound.
        :param obj: the object reference to be bound.

        :return: the full qualified name of the bound object across the whole context hierarchy.

        :raises:
            UnboundException NamingException.unbound: if this NamingContext has not been bound to a name yet.
            NamingException NamingException.Message.invalid_name: The supplied name is invalid (i.e., is None or has length less than 1).
            NameNotFoundException NamingException.Message.name_not_found: if no binding was found for the supplied name.
            AlreadyBoundException NamingException.Message.already_bound : An object is already bound under the supplied name.
        """
        return self._add_binding(name, obj, False, BindingType.named_object)

    @AbstractNamingContext.check_bounded
    def rebind(self, name, obj) -> Name:
        """
        Bind an object under a name in this NamingContext.
        If the name is singular (length of 1) the given object will be rebound the name in this NamingContext.
        In case it is composed out of multiple parts, the first part is resolved in this context, expecting a bound NamingContext,
        and the remaining parts are rebound in that resulting context.
        If a binding under the supplied name already exists it will be unbounded first.
        If the object to be bound is a NamingContext it will not participate in a recursive resolve.

        :param name: name under which the object will be bound.
        :param obj: the object reference to be bound.

        :return: the full qualified name of the bound object across the whole context hierarchy.

        :raises:
            UnboundException NamingException.unbound: if this NamingContext has not been bound to a name yet.
            NamingException NamingException.Message.invalid_name: The supplied name is invalid (i.e., is None or has length less than 1).
            NameNotFoundException NamingException.Message.name_not_found: if no binding was found for the supplied name.
        """
        return self._add_binding(name, obj, True, BindingType.named_object)

    @AbstractNamingContext.check_bounded
    def bind_context(self, name, context) -> Name:
        """
        Bind a NamingContext under a name in this NamingContext.
        If the name is singular (length of 1) the given context will be rebound the name in this NamingContext.
        In case it is composed out of multiple parts, the first part is resolved in this context, expecting a bound NamingContext,
        and the remaining parts are rebound in that resulting context.
        An exception is thrown if a binding with the supplied name already exists. The NamingContext will participate in recursive resolving.

        :param name: name under which the object will be bound.
        :param context: the NamingContext object reference to be bound.

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
        return self._add_binding(name, context, False, BindingType.named_context)

    @AbstractNamingContext.check_bounded
    def rebind_context(self, name, context) -> Name:
        """
        Bind a NamingContext under a name in this NamingContext.
        If the name is singular (length of 1) the given context will be rebound the name in this NamingContext.
        In case it is composed out of multiple parts, the first part is resolved in this context, expecting a bound NamingContext,
        If a binding under the supplied name already exists it will be unbound first.
        The NamingContext will participate in recursive resolving.

        :param name: name under which the object will be bound.
        :param context: the NamingContext object reference to be bound.

        :return: the full qualified name of the bound object across the whole context hierarchy.

        :raises:
            UnboundException NamingException.unbound: if this NamingContext has not been bound to a name yet.
            NamingException NamingException.Message.invalid_name: The supplied name is invalid (i.e., is None or has length less than 1).
            NamingException NamingException.Message.context_expected : when the given object is not a NamingContext.
            NameNotFoundException NamingException.Message.name_not_found: if no binding was found for the supplied name.
            AlreadyBoundException NamingException.Message.already_bound : when an object is already bound under the supplied name.
        """
        if not isinstance(context, AbstractNamingContext):
            raise NamingException(NamingException.Message.context_expected, context)
        return self._add_binding(name, context, True, BindingType.named_context)

    def new_context(self):
        """
        Create and return a new instance of this context class.

        :return: an instance of `camelot.core.naming.NamingContext`
        """
        return self.__class__()

    @AbstractNamingContext.check_bounded
    def bind_new_context(self, name) -> NamingContext:
        """
        Creates a new NamingContext, binds it in this NamingContext and returns it.
        This is equivalent to new_context(), followed by a bind_context() with the provided name for the newly created context.
        :param name: name under which the created NamingContext will be bound.

        :return: an instance of `camelot.core.naming.AbstractNamingContext`

        :raises:
            UnboundException NamingException.unbound: if this NamingContext has not been bound to a name yet.
        """
        context = self.new_context()
        self.bind_context(name, context)
        return context

    @AbstractNamingContext.check_bounded
    def _add_binding(self, name: Name, obj, rebind: bool, binding_type: BindingType) -> Name:
        """
        Helper method that implements the addition of all types of bindings.
        It resolves the name to make sure no binding exists already (in case of a bind and bind_context).
        If the name has a length of 1, the given object is bound with the name in this NamingContext.
        Otherwise, the first part of the name is resolved in this context and the bind is passed to the resulting NamingContext.

        :param name: name under which the object will be bound.
        :param obj: the object reference to be bound.
        :param rebind: flag indicating if an existing binding should be replaced or not.
        :param binding_type: the type of the binding to add, a member of `camelot.core.orm.BindingType.

        :return: the full qualified name of the bound object across the whole context hierarchy.

        :raises:
            UnboundException NamingException.unbound: if this NamingContext has not been bound to a name yet.
            NamingException NamingException.Message.invalid_name: when the name is invalid (None or length less than 1).
            NameNotFoundException NamingException.Message.name_not_found: if no binding was found for the given name.
            AlreadyBoundException NamingException.Message.already_bound: when an object is already bound under the supplied name.
            NamingException NamingException.Message.invalid_binding_type: if the binding type is not a valid BindingType enum member.
        """
        name = self._assert_valid_name(name)
        if binding_type not in BindingType:
            raise NamingException(NamingException.Message.invalid_binding_type)
        if len(name) == 1:
            bound_obj = self._bindings[binding_type].get(name[0])
            if not rebind and bound_obj is not None:
                raise AlreadyBoundException(name[0], binding_type)

            # Add the object to the registry for the given binding_type.
            self._bindings[binding_type][name[0]] = obj
            # Determine the full qualified named of the bound object (extending that of this NamingContext).
            qual_name = self.get_qual_name(name[0])
            # If the object is a NamingContext, assign the qualified name.
            if binding_type == BindingType.named_context:
                if obj._name is not None:
                    raise AlreadyBoundException(name[0], binding_type)
                obj._name = qual_name
            return qual_name
        else:
            context = self._bindings[BindingType.named_context].get(name[0])
            if context is None:
                raise NameNotFoundException(name[0], BindingType.named_context)
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
        If the name is singular (length of 1) the binding under the given name will be removed from this NamingContext.
        In case it is composed out of multiple parts, the first part is resolved in this context, expecting a bound NamingContext,
        and the remaining parts are resolved in that resulting context.

        :param name: name under which the object should have been bound.

        :raises:
            UnboundException NamingException.unbound: if this NamingContext has not been bound to a name yet.
            NamingException NamingException.Message.invalid_name: when the name is invalid (None or length less than 1).
            NameNotFoundException NamingException.Message.name_not_found: if no binding was found for the given name.
        """
        self._remove_binding(name, BindingType.named_object)

    @AbstractNamingContext.check_bounded
    def unbind_context(self, name: Name) -> None:
        """
        Remove a context binding from this NamingContext.
        If the name is singular (length of 1) the context binding under the given name will be removed from this NamingContext.
        In case it is composed out of multiple parts, the first part is resolved in this context, expecting a bound NamingContext,
        and the remaining parts are resolved in that resulting context.
        As a result of this removal, the found NamingContext will get unbound and not be usable unless its reassociated.

        :param name: name under which the context should have been bound.

        :raises:
            UnboundException NamingException.unbound: if this NamingContext has not been bound to a name yet.
            NamingException NamingException.Message.invalid_name: when the name is invalid (None or length less than 1).
            NameNotFoundException NamingException.Message.name_not_found: if no binding was found for the given name.
        """
        self._remove_binding(name, BindingType.named_context)

    @AbstractNamingContext.check_bounded
    def _remove_binding(self, name: Name, binding_type: BindingType) -> None:
        """
        Helper method that supports removing all types of bindings from this NamingContext.
        If the name is singular (length of 1) the context binding under the given name will be removed from this NamingContext.
        In case it is composed out of multiple parts, the first part is resolved in this context, expecting a bound NamingContext,
        and the remaining parts are delegated to the resulting context.

        :param name: name of the binding.
        :param binding_type: the type of the binding to remove, a member of `camelot.core.orm.BindingType.

        :raises:
            UnboundException NamingException.unbound: if this NamingContext has not been bound to a name yet.
            NamingException NamingException.Message.invalid_name: when the name is invalid (None or length less than 1).
            NamingException NamingException.Message.invalid_binding_type: if the binding type is not a valid BindingType enum member.
            NameNotFoundException NamingException.Message.name_not_found: if no binding was found for the given name.
        """
        name = self._assert_valid_name(name)
        if binding_type not in BindingType:
            raise NamingException(NamingException.Message.invalid_binding_type)
        if len(name) == 1:
            if name[0] not in self._bindings[binding_type]:
                raise NameNotFoundException(name[0], binding_type)
            obj = self._bindings[binding_type].pop(name[0])
            if binding_type == BindingType.named_context:
                obj._name = None
        else:
            context = self._bindings[BindingType.named_context][name[0]]
            if context is None:
                raise NameNotFoundException(name[0], BindingType.named_context)
            if binding_type == BindingType.named_context:
                context.unbind_context(name[1:])
            elif binding_type == BindingType.named_object:
                context.unbind(name[1:])

    @AbstractNamingContext.check_bounded
    def resolve(self, name: Name) -> object:
        """
        Resolve a name in this NamingContext and return the bound object.
        It will throw appropriate exceptions if not found.

        :param name: name under which the object should have been bound.

        :raises:
            UnboundException NamingException.unbound: if this NamingContext has not been bound to a name yet.
            NamingException NamingException.Message.invalid_name: when the name is invalid (None or length less than 1).
            NameNotFoundException NamingException.Message.name_not_found: if no binding was found for the given name.
        """
        return self._resolve_binding(name, BindingType.named_object)

    @AbstractNamingContext.check_bounded
    def resolve_context(self, name: Name) -> NamingContext:
        """
        Resolve a name in this NamingContext and return the bound object, expecting it to be a NamingContext.
        It will throw appropriate exceptions if not found.

        :param name: name under which the context should have been bound.

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

        :param name: name under which the object should have been bound.
        :param binding_type: the type of binding to resolve, a member of `camelot.core.orm.BindingType.

        :raises:
            UnboundException NamingException.unbound: if this NamingContext has not been bound to a name yet.
            NamingException NamingException.Message.invalid_name: when the name is invalid (None or length less than 1).
            NamingException NamingException.Message.invalid_binding_type: if the binding type is not a valid BindingType enum member.
            NameNotFoundException NamingException.Message.name_not_found: if no binding was found for the given name.
        """
        name = self._assert_valid_name(name)
        if binding_type not in BindingType:
            raise NamingException(NamingException.Message.invalid_binding_type)
        if len(name) == 1:
            obj = self._bindings[binding_type].get(name[0])
            if obj is None:
                raise NameNotFoundException(name[0], binding_type)
            return obj
        else:
            context = self._bindings[BindingType.named_context].get(name[0])
            if context is None:
                raise NameNotFoundException(name[0], BindingType.named_context)
            if binding_type == BindingType.named_context:
                return context.resolve_context(name[1:])
            elif binding_type == BindingType.named_object:
                return context.resolve(name[1:])

    def list(self):
        return self._bindings[BindingType.named_object].keys()

class ConstantNamingContext(AbstractNamingContext):
    """
    Represents a stateless naming context, which handles resolving objects/values of a certain immutable python type.
    Currently, those constant values are considered to be integers, strings, booleans or float.
    As it only implements the resolve method from the AbstractNamingContext, no subcontexts can be bound.
    A ConstantNamingContext will thus by definition always be the 'endpoint' context in a naming hierachy.
    """

    def __init__(self, constant_type):
        super().__init__()
        assert constant_type in (int, str, bool, float, Decimal)
        self.constant_type = constant_type

    @classmethod
    def _assert_valid_name(cls, name:str) -> Name:
        """
        Helper method that validates a name and returns its composite form.

        :raises:
            NamingException NamingException.Message.invalid_name: The supplied name is invalid (i.e. is not a valid string).
        """
        if isinstance(name, tuple) and len(name) == 1:
            name = name[0]
        if not isinstance(name, str):
            raise NamingException(NamingException.Message.invalid_name)
        return (name,)

    @AbstractNamingContext.check_bounded
    def resolve(self, name: Name) -> object:
        """
        Resolve a name in this ConstantNamingContext and return the bound object.
        It will throw appropriate exceptions if the resolution failed.

        :param name: name under which the object should have been bound.
        :return: the bound object, an instance of this ConstantNamingContext's constant_type.

        :raises:
            UnboundException NamingException.unbound: if this NamingContext has not been bound to a name yet.
            NamingException NamingException.Message.invalid_name: when the name is invalid (None or length less than 1).
            NameNotFoundException NamingException.Message.name_not_found: if no binding was found for the given name.
        """
        name = self._assert_valid_name(name)
        try:
            return self.constant_type(name[0])
        except (ValueError, decimal.InvalidOperation):
            raise NameNotFoundException(name, BindingType.named_object)

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

        # Bind values and contexts for each supported 'constant' python type.
        constants = self.bind_new_context('constants')
        for constant_type in (str, int, Decimal): # Do not support floats, as vFinance uses Decimals throughout
            constants.bind_context(constant_type.__name__.lower(), ConstantNamingContext(constant_type))
        constants.bind('None', None)
        constants.bind('True', True)
        constants.bind('False', False)

    def new_context(self):
        """
        Create and return a new `camelot.core.naming.NamingContext` instance.
        Note that this does not create a new InitialNamingContext instance,
        as this is inherently impossible because of its singleton nature.

        :return: an instance of `camelot.core.naming.NamingContext`
        """
        return NamingContext()

initial_naming_context = InitialNamingContext()
