import logging
logger = logging.getLogger('camelot.view.controls.delegates.dbimagedelegate')

from ....core.item_model import PreviewRole
from ....core.qt import py_to_variant
from .customdelegate import CustomDelegate
from camelot.core.qt import QtGui, QtCore, Qt

from camelot.view.controls import editors

class DbImageDelegate(CustomDelegate):
    # Delegate for images that are saved in the database as a base64 string.
    
    @classmethod
    def get_editor_class(cls):
        return editors.DbImageEditor
    
    @classmethod
    def get_standard_item(cls, locale, model_context):
        item = super(DbImageDelegate, cls).get_standard_item(locale, model_context)
        if model_context.value is not None:
            image = QtGui.QImage()
            byte_array = QtCore.QByteArray.fromBase64( model_context.value.encode() )
            image.loadFromData( byte_array )
            thumbnail = image.scaled(100,100, Qt.AspectRatioMode.KeepAspectRatio)
            item.setData(py_to_variant(thumbnail), PreviewRole)
        return item  
