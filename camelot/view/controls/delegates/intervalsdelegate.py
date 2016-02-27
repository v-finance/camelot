#  ============================================================================
#
#  Copyright (C) 2007-2016 Conceptive Engineering bvba.
#  www.conceptive.be / info@conceptive.be
#
#  Redistribution and use in source and binary forms, with or without
#  modification, are permitted provided that the following conditions are met:
#      * Redistributions of source code must retain the above copyright
#        notice, this list of conditions and the following disclaimer.
#      * Redistributions in binary form must reproduce the above copyright
#        notice, this list of conditions and the following disclaimer in the
#        documentation and/or other materials provided with the distribution.
#      * Neither the name of Conceptive Engineering nor the
#        names of its contributors may be used to endorse or promote products
#        derived from this software without specific prior written permission.
#  
#  THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
#  ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
#  WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
#  DISCLAIMED. IN NO EVENT SHALL <COPYRIGHT HOLDER> BE LIABLE FOR ANY
#  DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
#  (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
#  LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
#  ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
#  (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
#  SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#
#  ============================================================================

import six

from ....core.qt import variant_to_py, Qt, QtGui
from .customdelegate import DocumentationMetaclass, CustomDelegate
from camelot.view.proxy import ValueLoading

@six.add_metaclass(DocumentationMetaclass)
class IntervalsDelegate(CustomDelegate):
    """Custom delegate for visualizing camelot.container.IntervalsContainer
  data:
  """
      
    def paint(self, painter, option, index):
        painter.save()
        self.drawBackground(painter, option, index)
        intervals_container = variant_to_py(index.model().data(index, Qt.EditRole))
        field_attributes = variant_to_py(index.data(Qt.UserRole))
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





