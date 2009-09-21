
from customdelegate import *
from camelot.view.art import Icon
from camelot.core.utils import variant_to_pyobject

class VirtualAddressDelegate(CustomDelegate):
  """
"""

  __metaclass__ = DocumentationMetaclass

  editor = editors.VirtualAddressEditor

  def paint(self, painter, option, index):
    painter.save()
    self.drawBackground(painter, option, index)
    virtual_address = variant_to_pyobject(index.model().data(index, Qt.EditRole))  
    
    background_color = QtGui.QColor(index.model().data(index, Qt.BackgroundRole))
    
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
    
    
    
    if virtual_address and virtual_address!=ValueLoading \
     and virtual_address[1]:
      
      rect = option.rect
      rect = QtCore.QRect(rect.width()-16, rect.top()+6, 16, 16)
      if virtual_address[0] == 'email':
        icon = Icon('tango/16x16/apps/internet-mail.png').getQPixmap()
        painter.drawPixmap(rect, icon)
      elif virtual_address[0] == 'phone':
        icon = Icon('tango/16x16/devices/phone.png').getQPixmap()
        painter.drawPixmap(rect, icon)
      elif virtual_address[0] == 'fax':
        icon = Icon('tango/16x16/devices/printer.png').getQPixmap()
        painter.drawPixmap(rect, icon)
      elif virtual_address[0] == 'mobile':
        icon = Icon('tango/16x16/devices/mobile.png').getQPixmap()
        painter.drawPixmap(rect, icon)
      elif virtual_address[0] == 'im':
        icon = Icon('tango/16x16/places/instant-messaging.png').getQPixmap()
        painter.drawPixmap(rect, icon)
      elif virtual_address[0] == 'pager':
        icon = Icon('tango/16x16/devices/pager.png').getQPixmap()
        painter.drawPixmap(rect, icon)  
      else:
      #if virtual_adress[0] == 'telephone':
        icon = Icon('tango/16x16/apps/preferences-desktop-sound.png').getQPixmap()
        painter.drawPixmap(rect, icon)

        
        
        
      painter.setPen(fontColor.toRgb())
        
        
        
      textRect = option.rect
      textRect = QtCore.QRect(textRect.left(), textRect.top()+6, textRect.width()-16, textRect.height())
      
      
      painter.drawText(textRect,
                       Qt.AlignLeft,
                       '%s : %s' % (unicode(virtual_address[0]), 
                                             unicode(virtual_address[1])))  
        
        
        
      
    painter.restore()
