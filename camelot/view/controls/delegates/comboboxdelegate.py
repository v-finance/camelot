
from customdelegate import *

class ComboBoxDelegate(CustomDelegate):
  
  __metaclass__ = DocumentationMetaclass

  editor = editors.ChoicesEditor
  
  def __init__(self, parent, choices, editable=True, **kwargs):
    CustomDelegate.__init__(self, parent, editable=editable, **kwargs)
    self.choices = choices

              
  def setEditorData(self, editor, index):
    value = variant_to_pyobject(index.data(Qt.EditRole))
    
    def create_choices_getter(model, row):
      
      def choices_getter():
        return list(self.choices(model._get_object(row)))
      
      return choices_getter
    
    editor.set_value(value)
    get_model_thread().post(create_choices_getter(index.model(),
                                                  index.row()),
                                                  editor.set_choices)

  def paint(self, painter, option, index):
    painter.save()
    self.drawBackground(painter, option, index)
    value = variant_to_pyobject(index.data(Qt.EditRole))
    
    background_color = QtGui.QColor(index.model().data(index, Qt.BackgroundRole))
    
    rect = option.rect
    rect = QtCore.QRect(rect.left() + 3, rect.top() + 6, rect.width() - 5, rect.height())
    
    if(option.state & QtGui.QStyle.State_Selected):
        painter.fillRect(option.rect, option.palette.highlight())
        fontColor = QtGui.QColor()
        if self.editable:         
          Color = option.palette.highlightedText().color()
          fontColor.setRgb(Color.red(), Color.green(), Color.blue())
        else:          
          fontColor.setRgb(130, 130, 130)
    else:
        if self.editable:
          painter.fillRect(option.rect, background_color)
          fontColor = QtGui.QColor()
          fontColor.setRgb(0, 0, 0)
        else:
          painter.fillRect(option.rect, option.palette.window())
          fontColor = QtGui.QColor()
          fontColor.setRgb(130, 130, 130)
          
    
    
    painter.setPen(fontColor.toRgb())
    rect = QtCore.QRect(option.rect.left()+2,
                        option.rect.top(),
                        option.rect.width()-2,
                        option.rect.height())
    painter.drawText(rect.x(),
                     rect.y(),
                     rect.width(),
                     rect.height(),
                     Qt.AlignVCenter | Qt.AlignLeft,
                     unicode(value))
    painter.restore()
    
    
  

