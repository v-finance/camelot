from PyQt4 import QtGui
from PyQt4.QtCore import Qt

from customdelegate import CustomDelegate, DocumentationMetaclass
from camelot.view.controls import editors
from camelot.core import constants
from camelot.core.utils import variant_to_pyobject
from camelot.view.proxy import ValueLoading

class FloatDelegate( CustomDelegate ):
    """Custom delegate for float values"""

    __metaclass__ = DocumentationMetaclass

    editor = editors.FloatEditor

    def __init__( self,
                 minimum = constants.camelot_minfloat,
                 maximum = constants.camelot_maxfloat,
                 precision = 2,
                 editable = True,
                 parent = None,
                 unicode_format = None,
                 prefix = '',
                 suffix = '',
                 **kwargs ):
        """
    :param precision:  The number of digits after the decimal point displayed.  This defaults
    to the precision specified in the definition of the Field.     
    """
        CustomDelegate.__init__( self, parent = parent, editable = editable,
                                suffix = suffix, prefix = prefix,
                                precision = precision, **kwargs )
        self.precision = precision
        self.editable = editable
        self.unicode_format = unicode_format
        self.prefix = prefix
        self.suffix = suffix

    def paint( self, painter, option, index ):
        painter.save()
        self.drawBackground( painter, option, index )
        value = variant_to_pyobject( index.model().data( index, Qt.EditRole ) )

        background_color = QtGui.QColor( index.model().data( index, Qt.BackgroundRole ) )

        if( option.state & QtGui.QStyle.State_Selected ):
            painter.fillRect( option.rect, option.palette.highlight() )
            fontColor = QtGui.QColor()
            if self.editable:
                Color = option.palette.highlightedText().color()
                fontColor.setRgb( Color.red(), Color.green(), Color.blue() )
            else:
                fontColor.setRgb( 130, 130, 130 )
        else:
            if self.editable:
                painter.fillRect( option.rect, background_color )
                fontColor = QtGui.QColor()
                fontColor.setRgb( 0, 0, 0 )
            else:
                painter.fillRect( option.rect, option.palette.window() )
                fontColor = QtGui.QColor()
                fontColor.setRgb( 130, 130, 130 )

        value_str = u''
        if value != None and value != ValueLoading:
            value_str = u'%.*f' % ( self.precision, value )

        value_str = unicode( self.prefix ) + ' ' + unicode( value_str ) + ' ' + unicode( self.suffix )
        value_str = value_str.strip()
        if self.unicode_format != None:
            value_str = self.unicode_format( value )

        painter.setPen( fontColor.toRgb() )
        painter.drawText( option.rect.left() + 3,
                         option.rect.top(),
                         option.rect.width() - 6,
                         option.rect.height(),
                         Qt.AlignVCenter | Qt.AlignRight,
                         str( value_str ) )
        painter.restore()
