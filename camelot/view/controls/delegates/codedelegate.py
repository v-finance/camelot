#  ============================================================================
#
#  Copyright (C) 2007-2010 Conceptive Engineering bvba. All rights reserved.
#  www.conceptive.be / project-camelot@conceptive.be
#
#  This file is part of the Camelot Library.
#
#  This file may be used under the terms of the GNU General Public
#  License version 2.0 as published by the Free Software Foundation
#  and appearing in the file license.txt included in the packaging of
#  this file.  Please review this information to ensure GNU
#  General Public Licensing requirements will be met.
#
#  If you are unsure which license is appropriate for your use, please
#  visit www.python-camelot.com or contact project-camelot@conceptive.be
#
#  This file is provided AS IS with NO WARRANTY OF ANY KIND, INCLUDING THE
#  WARRANTY OF DESIGN, MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE.
#
#  For use of this library in commercial applications, please contact
#  project-camelot@conceptive.be
#
#  ============================================================================
from PyQt4 import QtGui, QtCore
from PyQt4.QtCore import Qt

from customdelegate import CustomDelegate, DocumentationMetaclass
from camelot.view.controls import editors
from camelot.core.utils import variant_to_pyobject
from camelot.view.proxy import ValueLoading

class CodeDelegate(CustomDelegate):
  
    __metaclass__ = DocumentationMetaclass
      
    editor = editors.CodeEditor
    
    def __init__(self, parent=None, parts=[], separator=u'.', **kwargs):
        CustomDelegate.__init__(self, parent=parent, parts=parts, **kwargs)
        self.parts = parts
        self.separator = separator
    
    def paint(self, painter, option, index):
        painter.save()
        numParts = len(self.parts)
        self.drawBackground(painter, option, index)
        
        background_color = QtGui.QColor(index.model().data(index, Qt.BackgroundRole))
        
        if( option.state & QtGui.QStyle.State_Selected ):
            painter.fillRect(option.rect, option.palette.highlight())
            fontColor = QtGui.QColor()
            if self.editable:
                Color = option.palette.highlightedText().color()
                fontColor.setRgb(Color.red(), Color.green(), Color.blue())
            else:
                fontColor.setRgb(130,130,130)
        else:
            if self.editable:
                painter.fillRect(option.rect, background_color)
                fontColor = QtGui.QColor()
                fontColor.setRgb(0,0,0)
            else:
                painter.fillRect(option.rect, option.palette.window())
                fontColor = QtGui.QColor()
                fontColor.setRgb(130,130,130)
                
        rect = option.rect
        rect = QtCore.QRect(rect.left()+3, rect.top()+6, rect.width(), rect.height()-3)
        
        if numParts != 0:
            value = variant_to_pyobject(index.model().data(index, Qt.EditRole)) or []
            if value == ValueLoading:
                value = []
            value = self.separator.join([unicode(i) for i in value])
            
            painter.setPen(fontColor.toRgb())
            painter.drawText(rect.x(),
                           rect.y()-4,
                           rect.width()-6,
                           rect.height(),
                           Qt.AlignVCenter | Qt.AlignRight,
                           value)  
        
        painter.restore()


