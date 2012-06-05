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
            self.setMargin( 0 )
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
