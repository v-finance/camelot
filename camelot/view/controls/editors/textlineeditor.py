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

from PyQt4 import QtGui
from customeditor import AbstractCustomEditor, draw_tooltip_visualization


class TextLineEditor(QtGui.QLineEdit, AbstractCustomEditor):

    def __init__(self, 
                 parent, 
                 length = 20, 
                 field_name = 'text_line',
                 **kwargs):
        QtGui.QLineEdit.__init__(self, parent)
        self.setObjectName( field_name )
        AbstractCustomEditor.__init__(self)
        if length:
            self.setMaxLength(length)

    def set_value(self, value):
        value = AbstractCustomEditor.set_value(self, value)
        if value is not None:
            self.setText(unicode(value))
        else:
            self.setText('')
        return value

    def get_value(self):
        value_loading = AbstractCustomEditor.get_value(self)
        if value_loading is not None:
            return value_loading

        value = unicode(self.text())
        if self.value_is_none and not value:
            return None

        return value

    def set_field_attributes(self, editable = True,
                                   background_color = None, 
                                   tooltip = None, **kwargs):
        self.set_background_color( background_color )
        self.set_enabled( editable )
        self.setToolTip(unicode(tooltip or ''))

    def set_enabled(self, editable=True):
        value = self.text()
        self.setEnabled(editable)
        self.setText(value)

    def paintEvent(self, event):
        super(TextLineEditor, self).paintEvent(event)
        
        if self.toolTip():
            draw_tooltip_visualization(self)

