#  ============================================================================
#
#  Copyright (C) 2007-2013 Conceptive Engineering bvba. All rights reserved.
#  www.conceptive.be / info@conceptive.be
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
#  visit www.python-camelot.com or contact info@conceptive.be
#
#  This file is provided AS IS with NO WARRANTY OF ANY KIND, INCLUDING THE
#  WARRANTY OF DESIGN, MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE.
#
#  For use of this library in commercial applications, please contact
#  info@conceptive.be
#
#  ============================================================================

import six

from ....core.qt import variant_to_py, QtGui, QtCore, Qt
from .customdelegate import CustomDelegate, DocumentationMetaclass
from camelot.view.controls import editors
from camelot.view.art import Icon
from camelot.view.proxy import ValueLoading

class StarDelegate( six.with_metaclass( DocumentationMetaclass, 
                                        CustomDelegate ) ):
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
            style = QtGui.QApplication.style()
            for i in range( self.maximum ):
                if i+1<=stars:
                    style.drawItemPixmap( painter, rect, 1, pixmap )
                    rect = QtCore.QRect(rect.left()+20, rect.top(), rect.width(), rect.height())
        painter.restore()

