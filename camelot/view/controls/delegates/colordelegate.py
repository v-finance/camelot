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

from customdelegate import CustomDelegate, DocumentationMetaclass
from camelot.view.controls import editors
from camelot.core.utils import variant_to_pyobject
from camelot.view.proxy import ValueLoading

class ColorDelegate(CustomDelegate):
  
    __metaclass__ = DocumentationMetaclass
    
    editor = editors.ColorEditor
    
    def paint(self, painter, option, index):
        painter.save()
        self.drawBackground(painter, option, index)
        field_attributes = variant_to_pyobject( index.model().data( index, Qt.UserRole ) )
        color = variant_to_pyobject( index.model().data( index, Qt.EditRole ) )
        editable = True
        background_color = None
        if field_attributes != ValueLoading:
            editable = field_attributes.get( 'editable', True )
            background_color = field_attributes.get( 'background_color', None )
        if ( option.state & QtGui.QStyle.State_Selected ):
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



