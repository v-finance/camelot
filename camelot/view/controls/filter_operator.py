#  ============================================================================
#
#  Copyright (C) 2007-2008 Conceptive Engineering bvba. All rights reserved.
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

from PyQt4 import QtGui, QtCore

from camelot.core.utils import ugettext
from camelot.view.utils import operator_names
from camelot.view.controls import editors
from camelot.view.controls.filterlist import filter_changed_signal

class FilterOperator(QtGui.QGroupBox):
    """Widget that allows applying various filter operators on a field"""
    
    def __init__(self, entity, field_name, field_attributes, parent):
        QtGui.QGroupBox.__init__(self, unicode(field_attributes['name']), parent)
        self._entity, self._field_name, self._field_attributes = entity, field_name, field_attributes
        self._field_attributes['editable'] = True
        layout = QtGui.QVBoxLayout()
        self._operators = field_attributes.get('operators', [])
        self._choices = [(0, ugettext('All')), (1, ugettext('None')),] + [(i+2, ugettext(operator_names[operator])) for i,operator in enumerate(self._operators)]
        combobox = QtGui.QComboBox(self)
        layout.addWidget(combobox)
        for i,name in self._choices:
            combobox.insertItem(i, unicode(name))
        self.connect(combobox, QtCore.SIGNAL('currentIndexChanged(int)'), self.combobox_changed)
        delegate = self._field_attributes['delegate'](**self._field_attributes)
        option = QtGui.QStyleOptionViewItem()
        option.version = 5
        self._editor = delegate.createEditor( self, option, None )
        # explicitely set a value, otherways the current value remains ValueLoading
        self._editor.set_value(None)
        self.connect(self._editor, editors.editingFinished, self.editor_editing_finished)
        layout.addWidget(self._editor)
        self.setLayout(layout)
        self._editor.setEnabled(False)
        self._index = 0
        self._value = None
        
    def combobox_changed(self, index):
        self._index = index
        if index>=2:
            self._editor.setEnabled(True)
        else:
            self._editor.setEnabled(False)
        self.emit(filter_changed_signal)
        
    def editor_editing_finished(self):
        self._value = self._editor.get_value()
        self.emit(filter_changed_signal)
    
    def decorate_query(self, query):
        if self._index==0:
            return query
        if self._index==1:
            return query.filter(getattr(self._entity, self._field_name)==None)
        return query.filter(self._operators[self._index-2](getattr(self._entity, self._field_name), self._value))
