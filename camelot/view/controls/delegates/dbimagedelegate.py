import logging

from camelot.core.qt import QtGui, QtCore, Qt

from dataclasses import dataclass
from typing import Optional

from ....core.item_model import PreviewRole
from .customdelegate import CustomDelegate

logger = logging.getLogger(__name__)

@dataclass
class DbImageDelegate(CustomDelegate):
    # Delegate for images that are saved in the database as a base64 string.

    preview_width: int = 100
    preview_height: int = 100
    max_size: int = 50000

    @classmethod
    def get_editor_class(cls):
        return None

    @classmethod
    def value_to_string(cls, value, locale, field_attributes) -> Optional[str]:
        return None

    @classmethod
    def get_standard_item(cls, locale, model_context):
        item = super().get_standard_item(locale, model_context)
        if model_context.value is not None:
            image = QtGui.QImage()
            byte_array = QtCore.QByteArray.fromBase64( model_context.value.encode() )
            image.loadFromData( byte_array )
            thumbnail = image.scaled(100,100, Qt.AspectRatioMode.KeepAspectRatio)
            item.roles[PreviewRole] = thumbnail
        return item  
