from dataclasses import dataclass
import logging
logger = logging.getLogger('camelot.view.controls.delegates.dbimagedelegate')

from ....core.item_model import PreviewRole
from .customdelegate import CustomDelegate
from camelot.core.qt import QtGui, QtCore, Qt

from camelot.view.controls import editors

@dataclass
class DbImageDelegate(CustomDelegate):
    # Delegate for images that are saved in the database as a base64 string.

    preview_width: int = 100
    preview_height: int = 100
    max_size: int = 50000

    @classmethod
    def get_editor_class(cls):
        return editors.DbImageEditor
    
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
