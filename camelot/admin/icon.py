"""Serializable icon for building admins"""

from dataclasses import dataclass

from camelot.core.serializable import DataclassSerializable

@dataclass
class Icon(DataclassSerializable):
    """An icon that can be used to build admins

.. attribute:: name

    The name of the icon. This can be a front awesome name or image name ending with ".png".
    When the name ends with ".png", it is assumed to be an image from the vfinance module.

.. attribute:: pixmap_size

    The desired size of the pixmap.

.. attribute:: color

    The color of the icon.
    """

    name: str
    pixmap_size: int
    color: str

    def __init__(self, name, pixmap_size=32, color='#009999'):
        self.name = name
        self.pixmap_size = pixmap_size
        self.color = color
