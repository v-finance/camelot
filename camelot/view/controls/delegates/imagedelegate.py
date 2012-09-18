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
from filedelegate import FileDelegate
from camelot.view.controls import editors
from camelot.view.proxy import ValueLoading

from PyQt4 import QtGui, QtCore
from PyQt4.QtCore import Qt

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

