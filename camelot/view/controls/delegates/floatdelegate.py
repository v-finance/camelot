
from customdelegate import *
from camelot.core.constants import *

class FloatDelegate(CustomDelegate):
  """Custom delegate for float values"""

  editor = editors.FloatEditor
  
  def __init__(self,
               minimum=camelot_minfloat,
               maximum=camelot_maxfloat,
               precision=2,
               editable=True,
               parent=None,
               unicode_format = None,
               **kwargs):
    """
:param precision:  The number of digits after the decimal point displayed.  This defaults
to the precision specified in the definition of the Field.     
"""
    CustomDelegate.__init__(self, parent=parent, editable=editable, minimum=minimum, maximum=maximum,
                            precision=precision, **kwargs)
    self.minimum = minimum
    self.maximum = maximum
    self.precision = precision
    self.editable = editable
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
                                        editable=self.editable)
    rect = option.rect
    rect = QtCore.QRect(rect.left()+3, rect.top()+6, 16, 16)
    #fontColor = QtGui.QColor()
    
    if( option.state & QtGui.QStyle.State_Selected ):
        painter.fillRect(option.rect, option.palette.highlight())
        fontColor = QtGui.QColor()
        fontColor.setRgb(255,255,255)
    else:
        fontColor = QtGui.QColor()
        fontColor.setRgb(0,0,0)
    

    value_str = str(value)
    if self.unicode_format != None:
        value_str = self.unicode_format(value)

    #fontColor = fontColor.darker()
    
    if not self.editable:
        fontColor = QtGui.QColor()
        fontColor.setRgb(130,130,130)

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
                     value_str)
    painter.restore()