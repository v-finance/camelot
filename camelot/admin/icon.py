"""Serializable icon for building admins"""

from dataclasses import dataclass

from camelot.core.serializable import DataclassSerializable

@dataclass
class Icon(DataclassSerializable):
    """An icon that can be used to build admins

.. attribute:: name

    The name of the icon. This can be a front awesome name or Qt resource path pointing to an image.
    When the name starts with ":/", it is assumed to be a Qt resource path.

.. attribute:: pixmap_size

    The desired size of the pixmap.

.. attribute:: color

    The color of the icon.
    """

    name: str
    pixmap_size: int = 32
    color: str = '#009999'
