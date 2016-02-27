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

from ....core.qt import Qt, QtCore, QtGui, QtWidgets, variant_to_py
from .customdelegate import CustomDelegate, DocumentationMetaclass
from camelot.view.controls import editors
from camelot.view.art import Icon
from camelot.view.proxy import ValueLoading

@six.add_metaclass(DocumentationMetaclass)
class StarDelegate(CustomDelegate):
    """Delegate for integer values from ( default from 1 to 5)(Rating Delegate)  
    """
  
    editor = editors.StarEditor
    star_icon = Icon('tango/16x16/status/weather-clear.png')
  
    def __init__( self, parent = None, editable = True, maximum = 5, **kwargs ):
        CustomDelegate.__init__( self,
                                 parent = parent,
                                 editable = editable,
                                 maximum = maximum,
                                 **kwargs)
        self.maximum = maximum
        
    def paint( self, painter, option, index ):
        painter.save()
        self.drawBackground(painter, option, index)
        stars = variant_to_py( index.model().data(index, Qt.EditRole) )
        
        rect = option.rect
        rect = QtCore.QRect( rect.left()+3, rect.top()+6, 
                             rect.width()-5, rect.height() )
        
        if( option.state & QtGui.QStyle.State_Selected ):
            painter.fillRect(option.rect, option.palette.highlight())
        else:
            if not self.editable:
                painter.fillRect(option.rect, option.palette.window())
        if stars not in (None, ValueLoading):
            pixmap = self.star_icon.getQPixmap()
            style = QtWidgets.QApplication.style()
            for i in range( self.maximum ):
                if i+1<=stars:
                    style.drawItemPixmap( painter, rect, 1, pixmap )
                    rect = QtCore.QRect(rect.left()+20, rect.top(), rect.width(), rect.height())
        painter.restore()


