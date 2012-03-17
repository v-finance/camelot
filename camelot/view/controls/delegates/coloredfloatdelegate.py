#  ============================================================================
#
#  Copyright (C) 2007-2012 Conceptive Engineering bvba. All rights reserved.
#  www.conceptive.be / project-camelot@conceptive.be
#
#  This file is part of the Camelot Library.
#
#  This file may be used under the terms of the GNU General Public
#  License version 2.0 as published by the Free Software Foundation
#  and appearing in the file license.txt included in the packaging of
#  this file.  Please review this information to ensure GNU
#  General Public Licensing requirements will be met.
#
#  If you are unsure which license is appropriate for your use, please
#  visit www.python-camelot.com or contact project-camelot@conceptive.be
#
#  This file is provided AS IS with NO WARRANTY OF ANY KIND, INCLUDING THE
#  WARRANTY OF DESIGN, MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE.
#
#  For use of this library in commercial applications, please contact
#  project-camelot@conceptive.be
#
#  ============================================================================

from PyQt4.QtCore import Qt
from PyQt4 import QtGui, QtCore

from customdelegate import CustomDelegate, DocumentationMetaclass
from camelot.view.proxy import ValueLoading

from camelot.view.controls import editors
from camelot.core.utils import variant_to_pyobject
from camelot.view.art import Icon


class ColoredFloatDelegate(CustomDelegate):
    """Custom delegate for float values.

  The class attribute icons is used to customize the icons displayed.
  """

    __metaclass__ = DocumentationMetaclass

    editor = editors.ColoredFloatEditor
    icons = {
        1:'tango/16x16/actions/go-up.png',
        -1:'tango/16x16/actions/go-down-red.png',
        0:'tango/16x16/actions/zero.png'
    }

    def __init__(self, parent=None,
        precision=2, reverse=False, neutral=False,
        unicode_format=None, **kwargs
    ):
        CustomDelegate.__init__(self, parent=parent,
            reverse=reverse, neutral=neutral,
            precision=precision, unicode_format=unicode_format, **kwargs
        )
        self.precision = precision
        self.reverse = reverse
        self.neutral = neutral
        self.unicode_format = unicode_format
        self._locale = QtCore.QLocale()

    def paint(self, painter, option, index):
        painter.save()
        self.drawBackground(painter, option, index)
        value = variant_to_pyobject( index.model().data(index, Qt.EditRole) )
        field_attributes = variant_to_pyobject(index.data(Qt.UserRole))
        fontColor = QtGui.QColor()
        editable, prefix, suffix, background_color, arrow = True, '', '', None, None

        if field_attributes != ValueLoading:
            editable = field_attributes.get('editable', True)
            prefix = field_attributes.get('prefix', '')
            suffix = field_attributes.get('suffix', '')
            background_color = field_attributes.get('background_color', None)
            arrow = field_attributes.get('arrow', None)

        fontColor = QtGui.QColor()
        if (option.state & QtGui.QStyle.State_Selected):
            painter.fillRect(option.rect, option.palette.highlight())
        else:
            if editable:
                painter.fillRect(option.rect, background_color or option.palette.base())
                fontColor.setRgb(0,0,0)
            else:
                painter.fillRect(option.rect, background_color or option.palette.window())
                fontColor.setRgb(130,130,130)

        if arrow:
            comparator = arrow.y
        else:
            comparator = value
        #self.icons[cmp(comparator,0)].paint(painter, option.rect.left(), option.rect.top()+1, option.rect.height(), option.rect.height(), Qt.AlignVCenter)
        iconpath = self.icons[cmp(comparator,0)]
        icon = QtGui.QIcon(Icon(iconpath).getQPixmap())
        icon.paint(
            painter, option.rect.left(), option.rect.top()+1,
            option.rect.height(), option.rect.height(), Qt.AlignVCenter
        )

        value_str = u''
        if value != None and value != ValueLoading:
            if self.unicode_format != None:
                value_str = self.unicode_format(value)
            else:
                value_str = unicode( self._locale.toString( float(value), 
                                                            'f', 
                                                            self.precision ) )
        value_str = unicode(prefix) + u' ' + unicode(value_str) + u' ' + unicode(suffix)

        fontColor = fontColor.darker()
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


