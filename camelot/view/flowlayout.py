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
"""
PyQt4 port of the layouts/flowlayout example from Qt v4.x

The original port was copied from the PyQt layout examples.
"""

from PyQt4 import QtCore, QtGui

class FlowLayout( QtGui.QLayout ):
    """
    Layout that arranges child widgets from left to right and top to bottom.
    
    @todo : this layout returns a height for width that is too high, it seems
            as if it takes into account that it should be able to expand
    """
    
    def __init__( self, parent = None ):
        """
        :param parent: a `QtGui.QWidget`
        """
        super(FlowLayout, self).__init__(parent)
        if parent is not None:
            self.setContentsMargins( 0, 0, 0, 0 )
        self.setSpacing( -1 )
        self.item_list = []

    def addItem( self, item ):
        self.item_list.append( item )

    def count(self):
        return len(self.item_list)

    def itemAt( self, index ):
        if index >= 0 and index < len(self.item_list):
            return self.item_list[index]

        return None

    def takeAt( self, index ):
        if index >= 0 and index < len(self.item_list):
            return self.item_list.pop(index)

        return None

    def expandingDirections( self ):
        return QtCore.Qt.Orientations(QtCore.Qt.Orientation(0))

    def hasHeightForWidth( self ):
        return True

    def heightForWidth( self, width ):
        height = self.doLayout( QtCore.QRect(0, 0, width, 0), True )
        return height

    def setGeometry( self, rect ):
        super(FlowLayout, self).setGeometry(rect)
        self.doLayout( rect, False )

    def sizeHint( self ):
        return self.minimumSize()

    def minimumSize(self):
        size = QtCore.QSize()

        for item in self.item_list:
            size = size.expandedTo(item.minimumSize())

        size += QtCore.QSize(2 * self.margin(), 2 * self.margin())
        return size

    def doLayout( self, rect, testOnly ):
        x = rect.x()
        y = rect.y()
        lineHeight = 0

        for item in self.item_list:
            wid = item.widget()
            spaceX = self.spacing() + wid.style().layoutSpacing(QtGui.QSizePolicy.PushButton, QtGui.QSizePolicy.PushButton, QtCore.Qt.Horizontal)
            spaceY = self.spacing() + wid.style().layoutSpacing(QtGui.QSizePolicy.PushButton, QtGui.QSizePolicy.PushButton, QtCore.Qt.Vertical)
            nextX = x + item.sizeHint().width() + spaceX
            if nextX - spaceX > rect.right() and lineHeight > 0:
                x = rect.x()
                y = y + lineHeight + spaceY
                nextX = x + item.sizeHint().width() + spaceX
                lineHeight = 0

            if not testOnly:
                item.setGeometry(QtCore.QRect(QtCore.QPoint(x, y), item.sizeHint()))

            x = nextX
            lineHeight = max(lineHeight, item.sizeHint().height())

        return y + lineHeight - rect.y()

