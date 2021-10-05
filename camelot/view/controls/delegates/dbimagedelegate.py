import logging
logger = logging.getLogger('camelot.view.controls.delegates.dbimagedelegate')

from ....core.item_model import PreviewRole
from ....core.qt import py_to_variant
from .customdelegate import CustomDelegate
from camelot.core.qt import QtGui, QtCore, Qt

from camelot.view.controls import editors

class DbImageDelegate(CustomDelegate):
    # Delegate for images that are saved in the database as a base64 string.
    
    editor = editors.DbImageEditor
    
    @classmethod
    def get_standard_item(cls, locale, value, fa_values):
        item = super(DbImageDelegate, cls).get_standard_item(locale, value, fa_values)
        if value is not None:
            image = QtGui.QImage()
            byte_array = QtCore.QByteArray.fromBase64( value.encode() )
            image.loadFromData( byte_array )
            thumbnail = image.scaled(100,100, Qt.KeepAspectRatio)
            item.setData(py_to_variant(thumbnail), PreviewRole)
        return item  