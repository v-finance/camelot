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
from PyQt4 import QtGui, QtCore
from PyQt4.QtCore import Qt

from camelot.core.utils import variant_to_pyobject
from customdelegate import CustomDelegate, DocumentationMetaclass
from camelot.view.controls import editors
from camelot.view.art import Icon

class StarDelegate(CustomDelegate):
    """Delegate for integer values from (1 to 5)(Rating Delegate)
  
  """
  
    __metaclass__ = DocumentationMetaclass
  
    editor = editors.StarEditor
  
    def __init__(self, parent=None, editable=True, maximum=5, **kwargs):
        CustomDelegate.__init__(self,
                                parent=parent,
                                editable=editable,
                                maximum=maximum,
                                **kwargs)
        self.maximum = maximum
        
    def paint(self, painter, option, index):
        painter.save()
        self.drawBackground(painter, option, index)
        stars = variant_to_pyobject( index.model().data(index, Qt.EditRole) )
        
        rect = option.rect
        rect = QtCore.QRect(rect.left()+3, rect.top()+6, rect.width()-5, rect.height())
        
        if( option.state & QtGui.QStyle.State_Selected ):
            painter.fillRect(option.rect, option.palette.highlight())
        else:
            if not self.editable:
                painter.fillRect(option.rect, option.palette.window())
          
        for i in range(5):
            if i+1<=stars:
                icon = Icon('tango/16x16/status/weather-clear.png').getQPixmap()
                QtGui.QApplication.style().drawItemPixmap(painter, rect, 1, icon)
                rect = QtCore.QRect(rect.left()+20, rect.top(), rect.width(), rect.height())
        painter.restore()

