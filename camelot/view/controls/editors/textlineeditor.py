#  ============================================================================
#
#  Copyright (C) 2007-2013 Conceptive Engineering bvba. All rights reserved.
#  www.conceptive.be / info@conceptive.be
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
#  visit www.python-camelot.com or contact info@conceptive.be
#
#  This file is provided AS IS with NO WARRANTY OF ANY KIND, INCLUDING THE
#  WARRANTY OF DESIGN, MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE.
#
#  For use of this library in commercial applications, please contact
#  info@conceptive.be
#
#  ============================================================================

import six

from ....core.qt import QtGui, variant_to_py

from .customeditor import AbstractCustomEditor, draw_tooltip_visualization

class TextLineEditor(QtGui.QLineEdit, AbstractCustomEditor):

    def __init__(self, 
                 parent, 
                 length = 20, 
                 field_name = 'text_line',
                 **kwargs):
        QtGui.QLineEdit.__init__(self, parent)
        AbstractCustomEditor.__init__(self)
        self.setObjectName( field_name )
        self.setProperty('value', None)
        if length:
            self.setMaxLength(length)

    def set_value(self, value):
        value = AbstractCustomEditor.set_value(self, value)
        self.setProperty('value', value)
        if value is not None:
            self.setText(six.text_type(value))
        else:
            self.setText('')
        return value

    def get_value(self):
        value_loading = AbstractCustomEditor.get_value(self)
        if value_loading is not None:
            return value_loading

        value = six.text_type(self.text())
        if len(value)==0:
            value = variant_to_py(self.property('value'))

        return value

    def set_field_attributes(self, **kwargs):
        super(TextLineEditor, self).set_field_attributes(**kwargs)
        self.set_enabled(kwargs.get('editable', False))
        self.setToolTip(six.text_type(kwargs.get('tooltip', '')))

    def set_enabled(self, editable=True):
        value = self.text()
        self.setEnabled(editable)
        self.setText(value)

    def paintEvent(self, event):
        super(TextLineEditor, self).paintEvent(event)
        
        if self.toolTip():
            draw_tooltip_visualization(self)


