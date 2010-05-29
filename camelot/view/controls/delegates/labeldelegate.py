from PyQt4 import QtGui, QtCore
from PyQt4.QtCore import Qt

from customdelegate import CustomDelegate, DocumentationMetaclass
from camelot.view.controls import editors

class LabelDelegate(CustomDelegate):

    __metaclass__ = DocumentationMetaclass
    
    editor = editors.LabelEditor

    def paint(self, painter, option, index):
        painter.save()
        self.drawBackground(painter, option, index)
        checked = index.model().data(index, Qt.EditRole).toBool()
        
        background_color = QtGui.QColor(index.model().data(index, Qt.BackgroundRole))
        
        if( option.state & QtGui.QStyle.State_Selected ):
            painter.fillRect(option.rect, option.palette.highlight())
        elif not self.editable:
            painter.fillRect(option.rect, option.palette.window())
        else:
            painter.fillRect(option.rect, background_color)
            
            
        QtGui.QApplication.style().drawControl(QtGui.QStyle.CE_CheckBox,
                                               checked,
                                               painter)
        painter.restore()
