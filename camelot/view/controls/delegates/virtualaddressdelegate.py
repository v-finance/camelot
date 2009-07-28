
from customdelegate import *
from camelot.view.art import Icon

class VirtualAddressDelegate(CustomDelegate):
  """
.. image:: ../_static/virtualaddress_editor.png
"""

  editor = editors.VirtualAddressEditor

  def paint(self, painter, option, index):
    painter.save()
    self.drawBackground(painter, option, index)
    virtual_address = index.model().data(index, Qt.EditRole).toPyObject()  
    if virtual_address and virtual_address!=ValueLoading \
     and virtual_address[1]:
      painter.drawText(option.rect,
                       Qt.AlignLeft,
                       '%s : %s' % (unicode(virtual_address[0]),
                                    unicode(virtual_address[1])))
      rect = option.rect
      rect = QtCore.QRect(rect.width()-19, rect.top()+6, 16, 16)
      if virtual_address[0] == 'email':
        icon = Icon('tango/16x16/apps/internet-mail.png').getQPixmap()
        painter.drawPixmap(rect, icon)
      else:
      #if virtual_adress[0] == 'telephone':
        icon = Icon('tango/16x16/apps/preferences-desktop-sound.png').getQPixmap()
        painter.drawPixmap(rect, icon)
    painter.restore()
