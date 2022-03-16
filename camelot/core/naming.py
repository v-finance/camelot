"""
Server side register for objects whose reference is send to the client.
Inspired by the Corba/Java NamingContext.
"""
import functools
import logging
import typing

from enum import Enum

LOGGER = logging.getLogger(__name__)

Name = typing.Tuple[str, ...]

class AbstractNamingContext(object):

    def bind(self, name: Name, obj):
        """
        Creates a binding of a name and an object in the naming context.
        :param name: Name of the object
        :param obj: The object to bind with the given name
        """
        raise NotImplementedError

    def rebind(self, name: Name, obj):
        """
        Creates a binding of a name and an object in the naming context even if the name is already bound in the context.
        :param name: Name of the object
        :param obj: The object to bind with the given name
        """
        raise NotImplementedError

    def bind_context(self, name: Name, context):
        """
        Names an object that is a naming context. Naming contexts that are bound using bind_context() participate in name resolution when compound names are passed to be resolved.
        :param name: Name of the object
        :param obj: The AbstractNamingContext obj to bind with the given name
        """
        raise NotImplementedError

    def rebind_context(self, name: Name, context):
        """
        Creates a binding of a name and a naming context in the naming context even if the name is already bound in the context.
        :param name: Name of the object
        :param obj: The AbstractNamingContext obj to bind with the given name
        """
        raise NotImplementedError

    def bind_new_context(self, name):
        """Creates a new context and binds it to the name supplied as an argument."""
        raise NotImplementedError

    def unbind(self, name: Name):
        """
        Removes a name binding from the context.
        :param name: Name of the object
        """
        raise NotImplementedError

    def resolve(self, name: Name):
        """
        Retrieve the object bound to a name in the context. The given name must exactly match the bound name.
        :param name: Name of the object
        """
        raise NotImplementedError

    def resolve_context(self, name: Name):
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
        except KeyError:
            return False

    @classmethod
    def verbose_name(cls, route):
        return '/'.join(route)

class BindingType(Enum):

    named_object = 1
    named_context = 2

class NamingException(Exception):

    def __init__(self, message, *args, **kwargs):
        assert isinstance(message, self.Message)
        self.message = message
        self.message_text = message.value.format(*args, **kwargs)
        super().__init__(self.message_text)

    class Message(Enum):

        not_found = 'The given name does not identify a binding'
        not_context = 'Trying to rebind a context, while an existing object bind was found'
        not_object = 'Trying to rebind an object, while an existing context bind was found'
        already_bound = 'An object is already bound to the specified name'
        context_already_bound = 'This NamingContext is already bound'
        context_unbounded = 'Can not proceed: this NamingContext is not bound to another context yet'
        invalid_name = 'The given name is invalid'
        invalid_binding_type = 'Invalid binding type, should be a member of `camelot.core.naming.BindingType'
        context_expected = 'Expected an instance of `camelot.core.naming.AbstractNamingContext`, instead got {0}'

class NamingContext(AbstractNamingContext):
    """
    Implements the AbstractNamingContext interface and provides the
    starting point for resolution of names.
    """

    def __init__(self):
        self._bindings = {btype: dict() for btype in BindingType}
        self._name = None

    def check_bounded(func):
        # Validation decorator that checks and raises when this NamingContext is unbound.
        @functools.wraps(func)
        def wrapper(self, *args, **kwargs):
            if self._name is None:
                raise NamingException(NamingException.Message.context_unbounded)
            return func(self, *args, **kwargs)
        return wrapper

    @check_bounded
    def dump_names(self):
        for name in self.list():
            LOGGER.info(self.verbose_name(*self._name, name))

    @check_bounded
    def bind(self, name, obj):
        """
        Bind an object under a name in this NamingContext.
        If the name is singular (length of 1) the given object will be bound with the name in this NamingContext.
        In case it is composed out of multiple parts, the first part is resolved in this context, expecting a bound NamingContext,
        and the tail parts are bound in that resulting context.
        An exception is thrown if a binding with the supplied name already exists.
        If the object to be bound is a NamingContext it will not participate in a recursive resolve; use bind_context() instead for this behaviour.
        :param name: name under which the object will be bound.
        :param obj: the object reference to be bound.
        :return: the full composite name of the bounded object across the whole context hierarchy.
        :raises:
            NamingException NamingException.context_unbounded: if this NamingContext has not been bounded to a name yet.
            NamingException NamingException.Message.invalid_name: The supplied name is invalid (i.e., is None or has length less than 1).
            NamingException NamingException.Message.not_found: if no binding was found for the supplied name.
            NamingException NamingException.Message.already_bound : An object is already bound under the supplied name.
            NamingException NamingException.Message.not_context: if the found binding is not an instance of `camelot.core.naming.AbstractNamingContext` when it was expected to be be so.
        """
        return self._add_binding(name, obj, False, BindingType.named_object)

    @check_bounded
    def rebind(self, name, obj):
        """
        Bind an object under a name in this NamingContext.
        If the name is singular (length of 1) the given object will be rebound the name in this NamingContext.
        In case it is composed out of multiple parts, the first part is resolved in this context, expecting a bound NamingContext,
        and the tail parts are rebound in that resulting context.
        If a binding under the supplied name already exists it will be unbounded first.
        If the object to be bound is a NamingContext it will not participate in a recursive resolve.
        :param name: name under which the object will be bound.
        :param obj: the object reference to be bound.
        :return: the full composite name of the bounded object across the whole context hierarchy.
        :raises:
            NamingException NamingException.context_unbounded: if this NamingContext has not been bounded to a name yet.
            NamingException NamingException.Message.invalid_name: The supplied name is invalid (i.e., is None or has length less than 1).
            NamingException NamingException.Message.not_found: if no binding was found for the supplied name.
            NamingException NamingException.Message.not_context: if the found binding is not an instance of `camelot.core.naming.AbstractNamingContext` when it was expected to be be so.
        """
        return self._add_binding(name, obj, True, BindingType.named_object)

    @check_bounded
    def bind_context(self, name, context):
        """
        Bind a NamingContext under a name in this NamingContext.
        If the name is singular (length of 1) the given context will be rebound the name in this NamingContext.
        In case it is composed out of multiple parts, the first part is resolved in this context, expecting a bound NamingContext,
        and the tail parts are rebound in that resulting context.
        An exception is thrown if a binding with the supplied name already exists. The NamingContext will participate in recursive resolving.
        :param name: name under which the object will be bound.
        :param context: the NamingContext object reference to be bound.
        :return: the full composite name of the bounded object across the whole context hierarchy.
        :raises:
            NamingException NamingException.context_unbounded: if this NamingContext has not been bounded to a name yet.
            NamingException NamingException.Message.invalid_name: The supplied name is invalid (i.e., is None or has length less than 1).
            NamingException NamingException.Message.not_found: if no binding was found for the supplied name.
            NamingException NamingException.Message.already_bound : when an object is already bound under the supplied name.
            NamingException NamingException.Message.not_context: if the found binding is not an instance of `camelot.core.naming.AbstractNamingContext` when it was expected to be be so.
        """
        if not isinstance(context, NamingContext):
            raise NamingException(NamingException.Message.context_expected)
        # Add binding implements all four flavors of binding
        return self._add_binding(name, context, False, BindingType.named_context)

    @check_bounded
    def rebind_context(self, name, context):
        """
        Bind a NamingContext under a name in this NamingContext.
        If the name is singular (length of 1) the given context will be rebound the name in this NamingContext.
        In case it is composed out of multiple parts, the first part is resolved in this context, expecting a bound NamingContext,
        If a binding under the supplied name already exists it will be unbound first.
        The NamingContext will participate in recursive resolving.
        :param name: name under which the object will be bound.
        :param context: the NamingContext object reference to be bound.
        :return: the full composite name of the bounded object across the whole context hierarchy.
        :raises:
            NamingException NamingException.context_unbounded: if this NamingContext has not been bounded to a name yet.
            NamingException NamingException.Message.invalid_name: The supplied name is invalid (i.e., is None or has length less than 1).
            NamingException NamingException.Message.not_found: if no binding was found for the supplied name.
            NamingException NamingException.Message.already_bound : when an object is already bound under the supplied name.
            NamingException NamingException.Message.not_context: if the found binding is not an instance of `camelot.core.naming.AbstractNamingContext` when it was expected to be be so.
        """
        return self._add_binding(name, context, True, BindingType.named_context)

    @check_bounded
    def bind_new_context(self, name):
        """
        Creates a new NamingContext, binds it in this NamingContext and returns it.
        This is equivalent to initializing a new NamingContext, followed by a bind_context() with the provided name for the newly created NamingContext.
        :param name: name under which the created NamingContext will be bound.
        :return: an instance of `camelot.core.naming.AbstractNamingContext`
        :raises:
            NamingException NamingException.context_unbounded: if this NamingContext has not been bounded to a name yet.
        """
        context = NamingContext()
        self.bind_context(name, context)
        return context

    def _add_binding(self, name: Name, obj, rebind: bool, binding_type: BindingType):
        """
        Helper method that implements the addition of all types of bindings.
        It resolves the name to make sure no binding exists already (in case of a bind and bind_context).
        If the name has a length of 1, the given object is bound with the name in this NamingContext.
        Otherwise, the first part of the name is resolved in this context and the bind is passed to the resulting NamingContext.
        :param name: name under which the object will be bound.
        :param obj: the object reference to be bound.
        :param rebind: flag indicating if an existing binding should be replaced or not.
        :param binding_type: the type of the binding to add, a member of `camelot.core.orm.BindingType.
        :return: the full composite name of the bounded object across the whole context hierarchy.
        :raises:
            NamingException NamingException.Message.invalid_name: when the name is invalid (None or length less than 1).
            NamingException NamingException.Message.not_context: if no existing context binding was found when trying to rebind a NamingContext.
            NamingException NamingException.Message.not_found: if no binding was found for the given name.
            NamingException NamingException.Message.already_bound: when an object is already bound under the supplied name.
            NamingException NamingException.Message.invalid_binding_type: if the binding type is not a valid BindingType enum member.
        """
        if name is None or not len(name):
            raise NamingException(NamingException.Message.invalid_name)
        if binding_type not in BindingType:
            raise NamingException(NamingException.Message.invalid_binding_type)
        if len(name) == 1:
            bound_obj = self._bindings[binding_type].get(name[0])
            if not rebind and bound_obj is not None:
                raise NamingException(NamingException.Message.already_bound)

            # Add the object to the registry for the given binding_type.
            self._bindings[binding_type][name[0]] = obj
            # Determine the full composite named of the bounded object (extending that of this NamingContext).
            composite_name = (*self._name, name[0])
            # If the object is a NamingContext, assign the composite name.
            if binding_type == BindingType.named_context:
                if obj._name is not None:
                    raise NamingException(NamingException.Message.context_already_bound)
                obj._name = composite_name
            return composite_name
        else:
            context = self._bindings[BindingType.named_context][name]
            if context is None:
                raise NamingException(NamingException.Message.not_found)
            if binding_type == BindingType.named_context:
                if rebind:
                    return obj.rebind_context(name[1:], obj)
                return obj.bind_context(name[1:], obj)
            if binding_type == BindingType.named_object:
                if rebind:
                    return context.rebind(name[1:], obj)
                return context.bind(name[1:], obj)
            raise NamingException(NamingException.Message.invalid_binding_type)

    @check_bounded
    def resolve(self, name: Name):
        """
        Resolve a name in this NamingContext and return the bound object.
        It will throw appropriate exceptions if not found.
        :param name: name under which the object should have been bound.
        :raises:
            NamingException NamingException.context_unbounded: if this NamingContext has not been bounded to a name yet.
            NamingException NamingException.Message.invalid_name: when the name is invalid (None or length less than 1).
            NamingException NamingException.Message.not_found: if no binding was found for the given name.
        """
        return self._resolve_binding(name, BindingType.named_object)

    @check_bounded
    def resolve_context(self, name: Name):
        """
        Resolve a name in this NamingContext and return the bound object, expecting it to be a NamingContext.
        It will throw appropriate exceptions if not found.
        :param name: name under which the context should have been bound.
        :raises:
            NamingException NamingException.context_unbounded: if this NamingContext has not been bounded to a name yet.
            NamingException NamingException.Message.invalid_name: when the name is invalid (None or length less than 1).
            NamingException NamingException.Message.not_found: if no binding was found for the given name.
        """
        return self._resolve_binding(name, BindingType.named_context)

    def _resolve_binding(self, name: Name, binding_type: BindingType):
        """
        Helper method that implements the lookup of all types of bindings, returning the bound object.
        It will throw appropriate exceptions if not found.
        :param name: name under which the object should have been bound.
        :param binding_type: the type of binding to resolve, a member of `camelot.core.orm.BindingType.
        :raises:
            NamingException NamingException.Message.invalid_name: when the name is invalid (None or length less than 1).
            NamingException NamingException.Message.not_found: if no binding was found for the given name.
        """
        if name is None or not len(name):
            raise NamingException(NamingException.Message.invalid_name)
        if len(name) == 1:
            obj = self._bindings[binding_type].get(name[0])
            if obj is None:
                raise NamingException(NamingException.Message.not_found)
            return obj
        else:
            context = self._bindings[BindingType.named_context][name[0]]
            if context is None:
                raise NamingException(NamingException.Message.not_found)
            return context.resolve(name[1:])

    def list(self):
        return self._bindings[BindingType.named_object].keys()

class InitialNamingContext(NamingContext):
    """
    Singleton class that provides the initial naming context.
    """

    _instance = None

    def __new__(class_, *args, **kwargs):
        if not isinstance(class_._instance, class_):
            class_._instance = object.__new__(class_, *args, **kwargs)
        return class_._instance

    def __init__(self):
        super().__init__()
        # Initialize the name of this InitialNamingContext to the empty tuple,
        # so that it becomes bounded but does not contribute to the full composite name
        # resolution of subcontexts.
        self._name = tuple()
