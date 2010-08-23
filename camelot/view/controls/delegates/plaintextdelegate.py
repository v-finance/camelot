#  ============================================================================
#
#  Copyright (C) 2007-2010 Conceptive Engineering bvba. All rights reserved.
#  www.conceptive.be / project-camelot@conceptive.be
#
#  This file is part of the Camelot Library.
#
#  This file may be used under the terms of the GNU General Public
#  License version 2.0 as published by the Free Software Foundation
#  and appearing in the file LICENSE.GPL included in the packaging of
#  this file.  Please review the following information to ensure GNU
#  General Public Licensing requirements will be met:
#  http://www.trolltech.com/products/qt/opensource.html
#
#  If you are unsure which license is appropriate for your use, please
#  review the following information:
#  http://www.trolltech.com/products/qt/licensing.html or contact
#  project-camelot@conceptive.be.
#
#  This file is provided AS IS with NO WARRANTY OF ANY KIND, INCLUDING THE
#  WARRANTY OF DESIGN, MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE.
#
#  For use of this library in commercial applications, please contact
#  project-camelot@conceptive.be
#
#  ============================================================================

import logging
logger = logging.getLogger('camelot.view.controls.delegates.plaintextdelegate')

from PyQt4 import QtGui
from PyQt4 import QtCore
from PyQt4.QtCore import Qt

from customdelegate import CustomDelegate
from customdelegate import DocumentationMetaclass

from camelot.core.utils import ugettext
from camelot.core.utils import variant_to_pyobject

from camelot.view.controls import editors
from camelot.view.proxy import ValueLoading


class PlainTextDelegate(CustomDelegate):
    """Custom delegate for simple string values"""

    __metaclass__ = DocumentationMetaclass

    editor = editors.TextLineEditor

    def __init__(
        self, parent=None, length=20,
        editable=True, translate_content=False, **kw
    ):
        CustomDelegate.__init__(self, parent, editable, length=length, **kw)
        self.length = length
        self.editable = editable
        self._translate_content = translate_content

    def paint(self, painter, option, index):
        painter.save()
        self.drawBackground(painter, option, index)
        value = variant_to_pyobject(index.model().data(index, Qt.EditRole))
        bgcolor = QtGui.QColor(index.model().data(index, Qt.BackgroundRole))

        #if (option.state & QtGui.QStyle.State_Selected):
        #    painter.fillRect(option.rect, option.palette.highlight())
        #    fontColor = QtGui.QColor()
        #    if self.editable:
        #        Color = option.palette.highlightedText().color()
        #        fontColor.setRgb(Color.red(), Color.green(), Color.blue())
        #    else:
        #        fontColor.setRgb(130,130,130)
        #else:
        #    if self.editable:
        #        painter.fillRect(option.rect, bgcolor)
        #        fontColor = QtGui.QColor()
        #        fontColor.setRgb(0,0,0)
        #    else:
        #        painter.fillRect(option.rect, option.palette.window())
        #        fontColor = QtGui.QColor()
        #        fontColor.setRgb(130,130,130)

        fontcolor = QtGui.QColor(0, 0, 0)
        selected = option.state & QtGui.QStyle.State_Selected

        if selected:
            bgcolor = option.palette.highlight()
        elif not self.editable:
            bgcolor = option.palette.window()

        if not self.editable:
            fontcolor = QtGui.QColor(130, 130, 130)
        elif selected:
            fontcolor = option.palette.highlightedText().color()

        painter.fillRect(option.rect, bgcolor)

        #if text not in (None, ValueLoading):
        #    if self._translate_content:
        #        text = ugettext(text)
        #else:
        #    text = u''

        if value in (None, ValueLoading):
            value = unicode()

        if self._translate_content:
            value = ugettext(value)

        painter.setPen(fontcolor)
        rect = QtCore.QRect(option.rect)
        rect.adjust(2, 0, -4, 0)
        painter.drawText(rect, Qt.AlignVCenter | Qt.AlignLeft, unicode(value))
        painter.restore()
