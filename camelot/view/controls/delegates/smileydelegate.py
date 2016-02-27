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

from ....core.qt import Qt, QtCore, QtGui, QtWidgets, variant_to_py

import six

from .customdelegate import CustomDelegate, DocumentationMetaclass
from ..editors.smileyeditor import SmileyEditor, default_icons

@six.add_metaclass(DocumentationMetaclass)
class SmileyDelegate(CustomDelegate):
    """Delegate for Smiley's
  """
    
    editor = SmileyEditor
  
    def __init__(self, parent, editable=True,  icons=default_icons, **kwargs):
        CustomDelegate.__init__(self,
                                parent=parent,
                                editable=editable,
                                icons=icons,
                                **kwargs)
        self.icons_by_name = dict(icons)
        
    def paint(self, painter, option, index):
        painter.save()
        icon_name = six.text_type(variant_to_py(index.model().data(index, Qt.DisplayRole)))
        
        background_color = QtGui.QColor(index.model().data(index, Qt.BackgroundRole))
        
        self.drawBackground(painter, option, index)
        rect = option.rect
        rect = QtCore.QRect(rect.left()+3, rect.top()+6, rect.width()-5, rect.height())
        
        if( option.state & QtGui.QStyle.State_Selected ):
            painter.fillRect(option.rect, option.palette.highlight())
        else:
            if not self.editable:
                painter.fillRect(option.rect, option.palette.window())
            else:
                painter.fillRect(option.rect, background_color)
                
        if icon_name:
            pixmap = self.icons_by_name[icon_name].getQPixmap()
            QtWidgets.QApplication.style().drawItemPixmap(painter, rect, 1, pixmap)

        painter.restore()





