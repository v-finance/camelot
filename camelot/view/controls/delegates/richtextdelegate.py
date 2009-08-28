
from customdelegate import *

class RichTextDelegate(CustomDelegate):
  """
"""

  __metaclass__ = DocumentationMetaclass
  
  editor = editors.RichTextEditor
  
  
  def __init__(self, parent=None, editable=True, **kwargs):
    CustomDelegate.__init__(self, parent, editable)
    
    self.editable = editable


  def paint(self, painter, option, index, background_color=QtGui.QColor("white")):
    painter.save()
    self.drawBackground(painter, option, index)
    unstrippedText = unicode(index.model().data(index, Qt.EditRole).toString())
    if not unstrippedText:
      text = ''
    else:

      from HTMLParser import HTMLParser

      string = []

      class HtmlToTextParser(HTMLParser):
        def handle_data(self, data):
          string.append(data.replace('\n',''))

      parser = HtmlToTextParser()
      parser.feed(unstrippedText)

      text = (' '.join(string))[:256]  
    
    rect = option.rect
    rect = QtCore.QRect(rect.left(), rect.top(), rect.width(), rect.height())  
      
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
          painter.fillRect(option.rect, background_color)
          fontColor = QtGui.QColor()
          fontColor.setRgb(0,0,0)
        else:
          painter.fillRect(option.rect, option.palette.window())
          fontColor = QtGui.QColor()
          fontColor.setRgb(130,130,130)
        
        
    painter.setPen(fontColor.toRgb())
    rect = QtCore.QRect(option.rect.left(),
                        option.rect.top(),
                        option.rect.width(),
                        option.rect.height())
    painter.drawText(rect.x(),
                     rect.y(),
                     rect.width(),
                     rect.height(),
                     Qt.AlignVCenter | Qt.AlignLeft,
                     text)
    painter.restore()

