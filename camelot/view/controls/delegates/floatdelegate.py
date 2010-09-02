from PyQt4 import QtGui, QtCore
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
                 parent = None,
                 unicode_format = None,
                 **kwargs ):
        """
    :param precision:  The number of digits after the decimal point displayed.  This defaults
    to the precision specified in the definition of the Field.     
    """
        CustomDelegate.__init__( self, parent = parent,
                                precision = precision, **kwargs )
        self.precision = precision
        self.unicode_format = unicode_format

    def paint( self, painter, option, index ):
        painter.save()
        self.drawBackground( painter, option, index )
        value = variant_to_pyobject( index.model().data( index, Qt.EditRole ) )
        field_attributes = variant_to_pyobject( index.model().data( index, Qt.UserRole ) )
        editable, prefix, suffix, background_color = True, '', '', None

        if field_attributes != ValueLoading:
            editable = field_attributes.get( 'editable', True )
            prefix = field_attributes.get( 'prefix', '' )
            suffix = field_attributes.get( 'suffix', '' )
            background_color = field_attributes.get( 'background_color', None )

        fontColor = QtGui.QColor()
        if( option.state & QtGui.QStyle.State_Selected ):
            painter.fillRect(option.rect, option.palette.highlight())
            fontColor = option.palette.highlightedText().color()
        else:
            if editable:
                painter.fillRect(option.rect, background_color or option.palette.base())
                fontColor.setRgb(0,0,0)
            else:
                painter.fillRect(option.rect, background_color or option.palette.window())
                fontColor.setRgb(130,130,130)

        value_str = u''
        if value != None and value != ValueLoading:
            #
            # we need to convert value explicitely to a float, since it might be of some
            # other type when using ColumnProperty (eg Decimal, int), and then another
            # arg method will be called with a different signature (this is C++ remember) 
            #
            value_str = QtCore.QString("%L1").arg(float(value),0,'f',self.precision)

        value_str = unicode( prefix ) + u' ' + unicode( value_str ) + u' ' + unicode( suffix )
        value_str = value_str.strip()
        if self.unicode_format is not None and value != ValueLoading:
            value_str = self.unicode_format( value )

        painter.setPen( fontColor.toRgb() )
        painter.drawText( option.rect.left() + 3,
                         option.rect.top(),
                         option.rect.width() - 6,
                         option.rect.height(),
                         Qt.AlignVCenter | Qt.AlignRight,
                         value_str )
        painter.restore()
