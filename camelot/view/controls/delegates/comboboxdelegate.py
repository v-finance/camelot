
from customdelegate import *
from PyQt4.QtGui import QComboBox, QItemDelegate, QStyleOption
from PyQt4.QtCore import QVariant, QString
from camelot.view.model_thread import post


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
    post(create_choices_getter(index.model(),index.row()), editor.set_choices)

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
                        option.rect.width()-4,
                        option.rect.height())
    painter.drawText(rect.x(),
                     rect.y(),
                     rect.width(),
                     rect.height(),
                     Qt.AlignVCenter | Qt.AlignLeft,
                     unicode(value))
    painter.restore()
    
    
class ComboBoxEditorDelegate(ComboBoxDelegate):  
    """ 
        Delegate for combobox which makes sure that the editor (of the combobox) is visible
        even if it isn't selected
    """
    def __init__(self, choices, parent=None, editable=True, **kwargs):
         ComboBoxDelegate.__init__(self, parent, choices, editable, **kwargs)
         print 'choices by construction', choices(None)
         
    def setEditorData(self, editor, index):
        value = variant_to_pyobject(index.data(Qt.EditRole))
        
        def create_choices_getter(model, row):
          
          def choices_getter():
            print 'in set editor data', self.choices(None)
            return list(self.choices(None))
          
          return choices_getter
        
        #editor.set_value(value)
        post(create_choices_getter(index.model(),index.row()), editor.set_choices)
    
    def setModelData(self, editor, model, index):
        return None
        #model.setData(index, create_constant_function(editor.get_value()))
    
    """ adapted from booldelegate """     
    def paint(self, painter, option, index):
        painter.save()
        self.drawBackground(painter, option, index)
        #checked = index.model().data(index, Qt.EditRole).toString().__str__()
        value = index.model().data(index, Qt.DisplayRole).toString().__str__()
        print "value", value
        #background_color = QtGui.QColor(index.model().data(index, Qt.BackgroundRole))
        background_color = QtGui.QColor(Qt.blue)
        
        #check_option = QtGui.QStyleOptionComboBox()
        #check_option = QtGui.QStyleOptionButton()
        check_option = QtGui.QStyleOptionMenuItem()
        #check_option.OptionType = QStyleOption.SO_ComboBox
        
        #check_option.text = QString('choice')
        
        rect = QtCore.QRect(option.rect.left(),
                            option.rect.top(),
                            option.rect.width(),
                            option.rect.height())

        #check_option.rect = rect
        check_option.palette = option.palette
        
        #if (option.state & QtGui.QStyle.State_Selected):
        #  painter.fillRect(option.rect, option.palette.highlight())
        #elif not self.editable:
        #  painter.fillRect(option.rect, option.palette.window())
        #else:
        painter.fillRect(option.rect, background_color)
          
        #if checked:
          #check_option.state = option.state | QtGui.QStyle.State_On
          #check_option.state = QtGui.QStyle.State_On
        #else:
      #check_option.state = option.state | QtGui.QStyle.State_Off
          #check_option.state = QtGui.QStyle.State_On
          
        check_option.state = QtGui.QStyle.State_DownArrow  
          
        QtGui.QApplication.style().drawControl(QtGui.QStyle.CE_MenuBarItem,
                                               check_option,
                                               painter)
        
        QtGui.QApplication.style().drawItemText(painter, rect, 0, option.palette, True, QString('choice'))
        painter.restore()

             
class TestComboBoxDelegate(QItemDelegate):


    def __init__(self, choices, parent = None):

        QItemDelegate.__init__(self, parent)
        self.choices = choices

    
    def createEditor(self, parent, option, index):
        editor = QComboBox( parent )
        i = 0
        for choice in self.choices:
            editor.insertItem(i, unicode(choice), QVariant(QString(choice)))
            i = i + 1
        return editor

    def setEditorData( self, comboBox, index ):
        value = index.model().data(index, Qt.DisplayRole).toInt()
        comboBox.setCurrentIndex(value[0])

    def setModelData(self, editor, model, index):
        value = editor.currentIndex()
        model.setData( index, editor.itemData( value, Qt.DisplayRole ) )

    def updateEditorGeometry( self, editor, option, index ):

        editor.setGeometry(option.rect)