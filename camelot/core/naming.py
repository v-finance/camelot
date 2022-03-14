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

    _names = dict()  

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
