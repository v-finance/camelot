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
        raise NotImplementedError

    def rebind(self, name: Name, obj):
        raise NotImplementedError

    def bind_context(self, name: Name, context):
        raise NotImplementedError

    def rebind_context(self, name: Name, context):
        raise NotImplementedError

    def bind_new_context(self, name):
        """Creates a new context and binds it to the name supplied as an argument."""
        raise NotImplementedError

    def unbind(self, name: Name):
        raise NotImplementedError

    def resolve(self, name: Name):
        raise NotImplementedError

    def list(self):
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

    def bind_new_context(self, name):
        context = self.__class__()
        self.bind(name, context)
        return context

    def bind(self, name, obj):
        self._bind(name, obj)

    def rebind(self, name, obj):
        self._bind(name, obj, True)

    def _bind(self, name, obj, rebind=False):
        if name is None or not len(name):
            raise NamingException(NamingException.Message.invalid_name)
        key = name[0]
        entry = self._names.get(key)
        if len(name) > 1:
            if entry is None:
                raise NamingException(NamingException.Message.not_found)
            if isinstance(entry, AbstractNamingContext):
                if rebind:
                    entry.rebind(name[1:], obj)
                else:
                    entry.bind(name[1:], obj)
            else:
                raise NamingException(NamingException.Message.context_expected, entry)
        else:
            if not rebind and entry is not None:
                raise NamingException(NamingException.Message.already_bound)
            else:
                self._names[name[0]] = obj

    def list(self):
        return self._names.keys()

    def resolve(self, name: Name):
        if name is None or not len(name):
            raise NamingException(NamingException.Message.invalid_name)
        key = name[0]
        entry = self._names.get(key)
        if entry is None:
            raise NamingException(NamingException.Message.not_found)
        if len(name) > 1:
            # If the length of the name is greater than 1, we go through a number of subcontexts.
            if not isinstance(AbstractNamingContext):
                raise NamingException(NamingException.Message.context_expected)
            return entry.resolve(name[1:])
        return entry

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
