from PyQt4 import QtGui, QtCore
from PyQt4.QtCore import Qt

from customdelegate import CustomDelegate, DocumentationMetaclass
from camelot.view.controls import editors
from camelot.view.proxy import ValueLoading
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
  
        if virtual_address and virtual_address!=ValueLoading:
            self.paint_text(painter, option, index, unicode(virtual_address[1] or ''), margin_left=0, margin_right=18)
            if virtual_address[1]:
                x, y, w, h = option.rect.getRect()
                icon_rect = QtCore.QRect(x + w - 18, y + (h-16)/2, 16, 16)
                if virtual_address[0] == 'email':
                    icon = Icon('tango/16x16/apps/internet-mail.png').getQPixmap()
                    painter.drawPixmap(icon_rect, icon)
                elif virtual_address[0] == 'phone':
                    icon = Icon('tango/16x16/devices/phone.png').getQPixmap()
                    painter.drawPixmap(icon_rect, icon)
                elif virtual_address[0] == 'fax':
                    icon = Icon('tango/16x16/devices/printer.png').getQPixmap()
                    painter.drawPixmap(icon_rect, icon)
                elif virtual_address[0] == 'mobile':
                    icon = Icon('tango/16x16/devices/mobile.png').getQPixmap()
                    painter.drawPixmap(icon_rect, icon)
                elif virtual_address[0] == 'im':
                    icon = Icon('tango/16x16/places/instant-messaging.png').getQPixmap()
                    painter.drawPixmap(icon_rect, icon)
                elif virtual_address[0] == 'pager':
                    icon = Icon('tango/16x16/devices/pager.png').getQPixmap()
                    painter.drawPixmap(icon_rect, icon)  
                else:
                #if virtual_adress[0] == 'telephone':
                    icon = Icon('tango/16x16/apps/preferences-desktop-sound.png').getQPixmap()
                    painter.drawPixmap(icon_rect, icon)

        painter.restore()
