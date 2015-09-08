
"""
This module contains the helper classes and constants for building a
`QAbstractItemModel` by the view.  The classes in this module are no subclasses
of `QObject`, but pure Python helper classes.
"""

from ..qt import Qt

#
# Custom Roles
#
FieldAttributesRole = Qt.UserRole
ObjectRole = Qt.UserRole + 1
PreviewRole = Qt.UserRole + 2
VerboseIdentifierRole = Qt.UserRole + 3

class ProxyDict(dict):
    """Subclass of dictionary to fool the Qt Variant object and prevent
    it from converting dictionary keys to whatever Qt object, but keep
    everything python"""
    pass
