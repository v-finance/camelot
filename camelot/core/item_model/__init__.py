
"""
This module contains the helper classes and constants for building a
`QAbstractItemModel` by the view.  The classes in this module are no subclasses
of `QObject`, but pure Python helper classes.
"""

from ..qt import Qt

from .list_proxy import ListModelProxy
from .proxy import AbstractModelProxy
from .query_proxy import QueryModelProxy

#
# Custom Roles
#
FieldAttributesRole = Qt.UserRole
ObjectRole = Qt.UserRole + 1
PreviewRole = Qt.UserRole + 2
VerboseIdentifierRole = Qt.UserRole + 3
ValidRole = Qt.UserRole + 4
ValidMessageRole = Qt.UserRole + 5

class ProxyDict(dict):
    """Subclass of dictionary to fool the Qt Variant object and prevent
    it from converting dictionary keys to whatever Qt object, but keep
    everything python"""
    pass

__all__ = [
    AbstractModelProxy.__name__,
    ListModelProxy.__name__,
    ProxyDict.__name__,
    QueryModelProxy.__name__,
]
