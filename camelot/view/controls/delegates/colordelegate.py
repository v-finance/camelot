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

from ....core.qt import variant_to_py, QtCore, QtGui, Qt
from .customdelegate import CustomDelegate, DocumentationMetaclass
from camelot.view.controls import editors
from camelot.view.proxy import ValueLoading

@six.add_metaclass(DocumentationMetaclass)
class ColorDelegate(CustomDelegate):
    
    editor = editors.ColorEditor
    
    def paint(self, painter, option, index):
        painter.save()
        self.drawBackground(painter, option, index)
        field_attributes = variant_to_py( index.model().data( index, Qt.UserRole ) )
        color = variant_to_py( index.model().data( index, Qt.EditRole ) )
        editable = True
        background_color = None
        if field_attributes != ValueLoading:
            editable = field_attributes.get( 'editable', True )
            background_color = field_attributes.get( 'background_color', None )
        if ( option.state & QtWidgets.QStyle.State_Selected ):
            painter.fillRect( option.rect, option.palette.highlight() )
        elif not editable:
            painter.fillRect( option.rect, background_color or option.palette.window() )
        else:
            painter.fillRect( option.rect, background_color or option.palette.base() )
        if color not in ( None, ValueLoading ):
            qcolor = QtGui.QColor()
            qcolor.setRgb( *color )
            rect = QtCore.QRect( option.rect.left() + 1,
                                 option.rect.top() + 1,
                                 option.rect.width() - 2,
                                 option.rect.height() - 2 )
            painter.fillRect( rect, qcolor )            
        painter.restore()





