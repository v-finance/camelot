from PyQt4 import QtGui
from PyQt4.QtCore import Qt

from camelot.view.controls.editors.charteditor import ChartEditor
from camelot.view.controls.delegates.customdelegate import CustomDelegate

import logging
LOGGER = logging.getLogger('camelot.view.controls.delegates.chartdelegate')

class ChartDelegate(CustomDelegate):
    """Custom editor for Matplotlib charts"""

    editor = ChartEditor
    
    def __init__(self, parent=None, **kwargs):
        super(ChartDelegate, self).__init__(parent)

    def setModelData(self, editor, model, index):
        pass
