"""Serializable icon for building admins"""

from dataclasses import dataclass

from camelot.core.serializable import DataclassSerializable

@dataclass
class Icon(DataclassSerializable):
    """An icon that can be used to build admins

.. attribute:: name

    The name of the icon in the awesome font.

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
