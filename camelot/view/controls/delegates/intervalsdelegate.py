#  ============================================================================
#
#  Copyright (C) 2007-2012 Conceptive Engineering bvba. All rights reserved.
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
from PyQt4 import QtGui
from PyQt4.QtCore import Qt

from customdelegate import DocumentationMetaclass, CustomDelegate
from camelot.core.utils import variant_to_pyobject
from camelot.view.proxy import ValueLoading

class IntervalsDelegate(CustomDelegate):
    """Custom delegate for visualizing camelot.container.IntervalsContainer
  data:
  """
  
    __metaclass__ = DocumentationMetaclass
      
    def paint(self, painter, option, index):
        painter.save()
        self.drawBackground(painter, option, index)
        intervals_container = variant_to_pyobject(index.model().data(index, Qt.EditRole))
        field_attributes = variant_to_pyobject(index.data(Qt.UserRole))
        # background_color = QtGui.QColor(index.model().data(index, Qt.BackgroundRole))
        # editable is defaulted to False, because there is no editor, no need for one currently
        editable, color, background_color = False, None, None
        
        if field_attributes != ValueLoading:
            editable = field_attributes.get( 'editable', False )
            background_color = field_attributes.get( 'background_color', QtGui.QColor(index.model().data(index, Qt.BackgroundRole)) )
            color = field_attributes.get('color', None)
        
        if( option.state & QtGui.QStyle.State_Selected ):
            painter.fillRect(option.rect, option.palette.highlight())
        else:
            if not editable:
                painter.fillRect(option.rect, option.palette.window())
            else:
                painter.fillRect(option.rect, background_color)
          
        if intervals_container and intervals_container!=ValueLoading:
            rect = option.rect
            xscale = float(rect.width()-4)/(intervals_container.max - intervals_container.min)
            xoffset = intervals_container.min * xscale + rect.x()
            yoffset = rect.y() + rect.height()/2
            for interval in intervals_container.intervals:
                qcolor = QtGui.QColor( interval.color or color )
                pen = QtGui.QPen( qcolor )
                pen.setWidth(3)
                painter.setPen(pen)
                xscale_interval = xscale
                x1, x2 =  xoffset + interval.begin *xscale_interval, xoffset + interval.end*xscale_interval
                painter.drawLine(x1, yoffset, x2, yoffset)
                painter.drawEllipse(x1-1, yoffset-1, 2, 2)
                painter.drawEllipse(x2-1, yoffset-1, 2, 2)
                pen = QtGui.QPen(Qt.white)      
                
        painter.restore()
    
    def createEditor(self, parent, option, index):
        pass
    
    def setEditorData(self, editor, index):
        pass
    
    def setModelData(self, editor, model, index):
        pass



