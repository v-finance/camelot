"""
Server side register for objects whose reference is send to the client.
Inspired by the Corba/Java NamingContext.
"""

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

    def dump_names(self):
        for name in self.list():
            LOGGER.info(self.verbose_name(name))

class NamingException(Exception):

    def __init__(self, message, *args, **kwargs):
        assert isinstance(message, self.Message)
        self.message = message
        self.message_text = message.value.format(*args, **kwargs)
        super().__init__(self.message_text)

    class Message(Enum):

        not_found = 'The given name does not identify a binding'
        not_context = 'Trying to rebind a context, but an object was found'
        #not_object = 'Trying to rebind an object, but a context was found'
        already_bound = 'An object is already bound to the specified name'
        invalid_name = 'The given name is invalid'
        context_expected = 'Expected an instance of `camelot.core.naming.AbstractNamingContext`, instead got {0}'

class NamingContext(AbstractNamingContext):
    """
    Implements the AbstractNamingContext interface and provides the
    starting point for resolution of names.
    """

    def __init__(self):
        self._names = dict()

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
        :raises:
            NamingException NamingException.Message.invalid_name: The supplied name is invalid (i.e., is None or has length less than 1).
            NamingException NamingException.Message.not_found: if no binding was found for the supplied name.
            NamingException NamingException.Message.already_bound : An object is already bound under the supplied name.
            NamingException NamingException.Message.not_context: if the found binding is not an instance of `camelot.core.naming.AbstractNamingContext` when it was expected to be be so.
        """
        self.add_binding(name, obj, rebind=False) #BindingType.nobject

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
        :raises:
            NamingException NamingException.Message.invalid_name: The supplied name is invalid (i.e., is None or has length less than 1).
            NamingException NamingException.Message.not_found: if no binding was found for the supplied name.
            NamingException NamingException.Message.not_context: if the found binding is not an instance of `camelot.core.naming.AbstractNamingContext` when it was expected to be be so.
        """
        self.add_binding(name, obj, rebind=True)

    def bind_context(self, name, context):
        """
        Bind a NamingContext under a name in this NamingContext.
        If the name is singular (length of 1) the given context will be rebound the name in this NamingContext.
        In case it is composed out of multiple parts, the first part is resolved in this context, expecting a bound NamingContext,
        and the tail parts are rebound in that resulting context.
        An exception is thrown if a binding with the supplied name already exists. The NamingContext will participate in recursive resolving.
        :param name: name under which the object will be bound.
        :param context: the NamingContext object reference to be bound.
        :raises:
            NamingException NamingException.Message.invalid_name: The supplied name is invalid (i.e., is None or has length less than 1).
            NamingException NamingException.Message.not_found: if no binding was found for the supplied name.
            NamingException NamingException.Message.already_bound : when an object is already bound under the supplied name.
            NamingException NamingException.Message.not_context: if the found binding is not an instance of `camelot.core.naming.AbstractNamingContext` when it was expected to be be so.
        """
        if not isinstance(context, AbstractNamingContext):
            raise NamingException(NamingException.Message.context_expected)
        # Add binding implements all four flavors of binding
        self.add_binding(name, context, rebind=False) # BindingType.ncontext

    def rebind_context(self, name, context):
        """
        Bind a NamingContext under a name in this NamingContext.
        If the name is singular (length of 1) the given context will be rebound the name in this NamingContext.
        In case it is composed out of multiple parts, the first part is resolved in this context, expecting a bound NamingContext,
        If a binding under the supplied name already exists it will be unbound first.
        The NamingContext will participate in recursive resolving.
        :param name: name under which the object will be bound.
        :param context: the NamingContext object reference to be bound.
        :raises:
            NamingException NamingException.Message.invalid_name: The supplied name is invalid (i.e., is None or has length less than 1).
            NamingException NamingException.Message.not_found: if no binding was found for the supplied name.
            NamingException NamingException.Message.already_bound : when an object is already bound under the supplied name.
            NamingException NamingException.Message.not_context: if the found binding is not an instance of `camelot.core.naming.AbstractNamingContext` when it was expected to be be so.
        """
        self.add_binding(name, context, rebind=True)

    def bind_new_context(self, name):
        """
        Creates a new NamingContext, binds it in this NamingContext and returns it.
        This is equivalent to initializing a new NamingContext, followed by a bind_context() with the provided name for the newly created NamingContext.
        :param name: name under which the created NamingContext will be bound.
        :return: an instance of `camelot.core.naming.AbstractNamingContext`
        """
        context = self.__class__()
        self.bind_context(name, context)
        return context

    def add_binding(self, name, obj, rebind=False):
        """
        Helper method that implements the addition of all types of bindings.
        It resolves the name to make sure no binding exists already (in case of a bind and bind_context).
        If the name has a length of 1, the given object is bound with the name in this NamingContext.
        Otherwise, the first part of the name is resolved in this context and the bind is passed to the resulting NamingContext.
        :param name: name under which the object will be bound.
        :param obj: the object reference to be bound.
        :param rebind: flag indicating if an existing binding should be replaced or not.
        :raises:
            NamingException NamingException.Message.invalid_name: when the name is invalid (None or length less than 1).
            NamingException NamingException.Message.not_context: if no existing context binding was found when trying to rebind a NamingContext.
            NamingException NamingException.Message.not_found: if no binding was found for the given name.
            NamingException NamingException.Message.already_bound : An object is already bound under the supplied name.
        """
        if name is None or not len(name):
            raise NamingException(NamingException.Message.invalid_name)
        if len(name) == 1:
            if rebind:
                entry = self._names.get(name[0])
                if entry is not None:
                    if isinstance(obj, NamingContext):
                        if not isinstance(entry, NamingContext):
                            raise NamingException(NamingException.Message.not_context)
                    #elif isinstance(entry, NamingContext):
                        #raise NamingException(NamingException.Message.not_object)
                #self._names[name[0]] = None
            else:
                raise NamingException(NamingException.Message.already_bound)
            self._names[name[0]] = obj
        else:
            context = self._resolve_context(name)
            if isinstance(obj, NamingContext):
                if rebind:
                    obj.rebind_context(name[1:], obj)
                else:
                    obj.bind_context(name[1:], obj)
            else:
                if rebind:
                    context.rebind(name[1:], obj)
                else:
                    context.bind(name[1:], obj)

    def resolve(self, name: Name):
        """
        Implements resolving a name in this context and expecting an object to be found.
        It will throw appropriate exceptions if not found.
        :param name: name to be bound.
        """
        if name is None or not len(name):
            raise NamingException(NamingException.Message.invalid_name)
        if len(name) == 1:
            obj = self._names.get(name[0])
            if obj is None:
                raise NamingException(NamingException.Message.not_found)
            return obj
        else:
            context = self._resolve_context(name)
            return context.resolve(name[1:])

    def _resolve_context(self, name):
        """
        Resolve the given name in this context non-recursively, expecting the result to be a NamingContext.
        :param name: name under which the object will be bound.
        :raises:
            NamingException NamingException.Message.not_found: if no binding was found for the given name.
            NamingException NamingException.Message.not_context: if the found binding is not an instance of `camelot.core.naming.AbstractNamingContext`
        """
        context = self._names[name]
        if context is None:
            raise NamingException(NamingException.Message.not_found)
        if not isinstance(context, NamingContext):
            raise NamingException(NamingException.Message.not_context)
        return context

    def list(self):
        return self._names.keys()

class InitialNamingContext(AbstractNamingContext):
    """
    Singleton class that provides the initial naming context.
    """

    _instance = None
    _context = NamingContext()

    def __new__(class_, *args, **kwargs):
        if not isinstance(class_._instance, class_):
            class_._instance = object.__new__(class_, *args, **kwargs)
        return class_._instance

    def bind(self, name: Name, obj):
        self._context.bind(name, obj)

    def rebind(self, name: Name, obj):
        self._context.rebind(name, obj)

    def bind_context(self, name: Name, context):
        self._context.bind_context(name, context)

    def rebind_context(self, name: Name, context):
        self._context.rebind_context(name, context)

    def bind_new_context(self, name):
        return self._context.bind_new_context(name)

    def unbind(self, name: Name):
        self._context.unbind(name)

    def resolve(self, name: Name):
        return self._context.resolve(name)

    def list(self):
        return self._context.list()
