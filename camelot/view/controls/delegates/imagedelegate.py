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

from ....core.qt import QtGui, QtCore, Qt
from ....view.controls import editors
from ....view.proxy import ValueLoading
from .filedelegate import FileDelegate


class ImageDelegate(FileDelegate):
    """Delegate for :class:`camelot.types.Image` fields.  Expects values of type 
    :class:`camelot.core.files.storage.StoredImage`.

    .. image:: /_static/image.png
    """
    
    editor = editors.ImageEditor
    margin = 2
    
    def paint(self, painter, option, index):
        painter.save()
        self.drawBackground(painter, option, index)
        
        data = index.data(Qt.DisplayRole)
        if data not in (None, ValueLoading):
            pixmap = QtGui.QPixmap(index.data(Qt.DisplayRole))
        
            if pixmap.width() > 0 and pixmap.height() > 0:
                rect = option.rect
                w_margin = max(0, rect.width() - pixmap.width())/2 + self.margin
                h_margin = max(0, rect.height()- pixmap.height())/2 + self.margin
                rect = QtCore.QRect(rect.left() + w_margin, 
                                    rect.top() + h_margin , 
                                    rect.width() - w_margin * 2, 
                                    rect.height() - h_margin * 2 )
                painter.drawPixmap( rect, pixmap )
                pen = QtGui.QPen(Qt.darkGray)
                pen.setWidth(3)
                painter.setPen(pen)
                painter.drawRect(rect)
        painter.restore()



