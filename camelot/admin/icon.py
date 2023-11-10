"""Serializable icon for building admins"""

from dataclasses import dataclass
import typing

from ..core.naming import CompositeName
from ..core.serializable import DataclassSerializable
from ..core.utils import ugettext_lazy

@dataclass
class Icon(DataclassSerializable):
    """An icon that can be used to build admins

.. attribute:: name

    The name of the icon. This can be a front awesome name or Qt resource path pointing to an image.
    When the name starts with ":/", it is assumed to be a Qt resource path.

.. attribute:: pixmap_size

    The desired size of the pixmap, should be higher than 0, or the painter will fail

.. attribute:: color

    The color of the icon.
    """

    name: str
    pixmap_size: int = 32
    color: str = '#009999'

# @tbd : correct location of this class in the source code

@dataclass
class CompletionValue(DataclassSerializable):
    """
    Represent one of the autocompletion values.

    .. attribute:: value

        A :class:`camelot.core.naming.CompositeName` that resolves to a bound completion value.

    .. attribute:: verbose_name

        The verbose representation of the value as it will appear to the user.

    .. attribute:: tooltip

        The tooltip as displayed to the user, this should be of type :class:`camelot.core.utils.ugettext_lazy`.

    """

    value: CompositeName
    verbose_name: typing.Union[str, ugettext_lazy, None] = None
    tooltip: typing.Union[str, ugettext_lazy, None] = None
    icon: typing.Union[Icon, None] = None
    foreground: typing.Union[str, None] = None
    background: typing.Union[str, None] = None
    virtual: typing.Union[bool, None] = None
