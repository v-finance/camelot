"""
Server side register for objects whose reference is send to the client.
Inspired by the Corba/Java NamingContext.
"""

import logging
import typing

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

class NamingContext(AbstractNamingContext):
    """
    Implements the AbstractNamingContext interface and provides the
    starting point for resolution of names.
    """

    _names = dict()

    def bind(self, name, obj):
        self._names[name] = obj

    def list(self):
        return self._names.keys()

    def resolve(self, name: Name):
        return self._names[name]