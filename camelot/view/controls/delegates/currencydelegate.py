
from customdelegate import *
from camelot.core.constants import *
import locale

class CurrencyDelegate(CustomDelegate):
  """Custom delegate for float values"""

  __metaclass__ = DocumentationMetaclass
  
  editor = editors.FloatEditor
  
  def __init__(self,
               minimum=camelot_minfloat,
               maximum=camelot_maxfloat,
               precision=2,
               editable=True,
               parent=None,
               unicode_format = None,
               prefix="",
               suffix="",
               **kwargs):
    """
:param precision:  The number of digits after the decimal point displayed.  This defaults
to the precision specified in the definition of the Field.     
"""
    CustomDelegate.__init__(self, parent=parent, editable=editable, minimum=minimum, maximum=maximum,
                            precision=precision, prefix=prefix, suffix=suffix, **kwargs)
    self.minimum = minimum
    self.maximum = maximum
    self.precision = precision
    self.editable = editable
    self.prefix = prefix
    self.suffix = suffix
    self.unicode_format = unicode_format
    
  def setEditorData(self, editor, index):
    value = index.model().data(index, Qt.EditRole).toDouble()[0]
    editor.set_value(value)



  def paint(self, painter, option, index):
    painter.save()
    self.drawBackground(painter, option, index)
    value = index.model().data(index, Qt.EditRole).toDouble()[0]
    editor = editors.FloatEditor(parent=None,
                                        minimum=self.minimum,
                                        maximum=self.maximum,
                                        precision=self.precision,
                                        editable=self.editable,
                                        prefix=self.prefix,
                                        suffix=self.suffix)
    rect = option.rect
    rect = QtCore.QRect(rect.left()+3, rect.top()+6, 16, 16)
    #fontColor = QtGui.QColor()
    
    if( option.state & QtGui.QStyle.State_Selected ):
        painter.fillRect(option.rect, option.palette.highlight())
        fontColor = QtGui.QColor()
        if self.editable:
          Color = option.palette.highlightedText().color()
          fontColor.setRgb(Color.red(), Color.green(), Color.blue())
        else:
          fontColor.setRgb(130,130,130)
    else:
        if self.editable:
          fontColor = QtGui.QColor()
          fontColor.setRgb(0,0,0)
        else:
          painter.fillRect(option.rect, option.palette.window())
          fontColor = QtGui.QColor()
          fontColor.setRgb(130,130,130)
        
    qlocale = QtCore.QLocale()
    value_str_formatted  = QtCore.QString("%L1").arg(value or 0.0,0,'f',2);
    
    painter.setPen(fontColor.toRgb())
    rect = QtCore.QRect(option.rect.left()+23,
                        option.rect.top(),
                        option.rect.width()-23,
                        option.rect.height())
    painter.drawText(rect.x()+2,
                     rect.y(),
                     rect.width()-4,
                     rect.height(),
                     Qt.AlignVCenter | Qt.AlignRight,
                     value_str_formatted)
    painter.restore()