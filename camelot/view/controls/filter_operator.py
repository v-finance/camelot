#  ============================================================================
#
#  Copyright (C) 2007-2011 Conceptive Engineering bvba. All rights reserved.
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

from PyQt4 import QtGui, QtCore

from camelot.core.utils import ugettext
from camelot.view.utils import operator_names
from camelot.view.controls.user_translatable_label import UserTranslatableLabel

class FilterOperator( QtGui.QWidget ):
    """Widget that allows applying various filter operators on a field"""
    
    filter_changed_signal = QtCore.pyqtSignal()
        
    def __init__(self, entity, field_name, field_attributes, parent):
        super( FilterOperator, self ).__init__( parent )        
        self._entity, self._field_name, self._field_attributes = entity, field_name, field_attributes
        self._field_attributes['editable'] = True
        layout = QtGui.QVBoxLayout()
        layout.setSpacing( 2 )
        layout.addWidget( UserTranslatableLabel( field_attributes['name'] ) )
        self._operators = field_attributes.get('operators', [])
        self._choices = [(0, ugettext('All')), (1, ugettext('None'))] + \
                        [(i+2, unicode(operator_names[operator])) for i, operator in enumerate(self._operators)]
        combobox = QtGui.QComboBox(self)
        layout.addWidget(combobox)
        for i, name in self._choices:
            combobox.insertItem(i, unicode(name))
        combobox.currentIndexChanged.connect( self.combobox_changed )
        delegate = self._field_attributes['delegate'](**self._field_attributes)
        option = QtGui.QStyleOptionViewItem()
        option.version = 5
        self._editor = delegate.createEditor( self, option, None )
        self._editor2 = delegate.createEditor( self, option, None )
        # explicitely set a value, otherways the current value remains 
        # ValueLoading
        self._editor.set_value(None)
        self._editor2.set_value(None)
        editing_finished_slot = self.editor_editing_finished
        self._editor.editingFinished.connect( editing_finished_slot )
        self._editor2.editingFinished.connect( editing_finished_slot )
        layout.addWidget(self._editor)
        layout.addWidget(self._editor2)
        layout.addStretch()
        self.setLayout(layout)
        self._editor.setEnabled(False)
        self._editor2.setEnabled(False)
        self._editor.hide()
        self._editor2.hide()
        self._index = 0
        self._value = None
        self._value2 = None
        
    @QtCore.pyqtSlot(int)
    def combobox_changed(self, index):
        """Whenever the combobox changes, show or hide the
        appropriate editors and emit the filter_changed signal """
        self._index = index
        if index >= 2:
            _, arity = self.get_operator_and_arity()
            self._editor.setEnabled(True)
            if arity > 0:
                self._editor.setEnabled(True)
                self._editor.show()
            else:
                self._editor.setEnabled(False)
                self._editor.hide()
            if arity > 1:
                self._editor2.setEnabled(True)
                self._editor2.show()
            else:
                self._editor2.setEnabled(False)
                self._editor2.hide()
        else:
            self._editor.setEnabled(False)
            self._editor.hide()
            self._editor2.setEnabled(False)
            self._editor2.hide()
        self.filter_changed_signal.emit()
        
    def editor_editing_finished(self):
        """Whenever one of the editors their value changes, emit
        the filters changed signal"""
        self._value = self._editor.get_value()
        self._value2 = self._editor2.get_value()
        self.filter_changed_signal.emit()
    
    def decorate_query(self, query):
        """
        :param query: an sqlalchemy query
        :returns: the input query transformed to take into account the filter of
        this widget
        """
        if self._index == 0:
            return query
        if self._index == 1:
            return query.filter(getattr(self._entity, self._field_name)==None)
        field = getattr(self._entity, self._field_name)
        operator, arity = self.get_operator_and_arity()
        if arity == 1:
            args = field, self._value
        elif arity == 2:
            args = field, self._value, self._value2
        else:
            assert False, 'Unsupported operator arity: %d' % arity
        return query.filter(operator(*args))

    def get_operator_and_arity(self):
        """:return: the current operator and its arity"""
        operator = self._operators[self._index-2]
        try:
            func_code = operator.func_code
        except AttributeError:
            arity = 1 # probably a builtin function, assume arity == 1
        else:
            arity = func_code.co_argcount - 1
        return operator, arity


