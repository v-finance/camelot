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

import logging

from PyQt4 import QtGui
from PyQt4 import QtCore

from camelot.view.proxy import ValueLoading
from customeditor import AbstractCustomEditor

LOGGER = logging.getLogger('camelot.view.controls.editors.ChoicesEditor')

class ChoicesEditor( QtGui.QComboBox, AbstractCustomEditor ):
    """A ComboBox aka Drop Down box that can be assigned a list of
    keys and values"""

    editingFinished = QtCore.pyqtSignal()
    valueChanged = QtCore.pyqtSignal()
    
    def __init__( self, 
                  parent = None, 
                  nullable = True, 
                  field_name = 'choices', 
                  **kwargs ):
        QtGui.QComboBox.__init__(self, parent)
        AbstractCustomEditor.__init__(self)
        self.setObjectName( field_name )
        self.activated.connect( self._activated )
        self._nullable = nullable 

    @QtCore.pyqtSlot(int)
    def _activated(self, _index):
        self.setProperty( 'value', QtCore.QVariant( self.get_value() ) )
        self.valueChanged.emit()
        self.editingFinished.emit()

    def set_choices( self, choices ):
        """
    :param choices: a list of (value,name) tuples.  name will be displayed in the combobox,
    while value will be used within get_value and set_value.  This method changes the items
    in the combo box while preserving the current value, even if this value is not in the
    new list of choices.
        """
        current_index = self.currentIndex()
        if current_index >= 0:
            current_name = unicode(self.itemText(current_index))
        current_value = self.get_value()
        current_value_available = False
        for i in range(self.count(), 0, -1):
            self.removeItem(i-1)
        for i, (value, name) in enumerate(choices):
            self.insertItem(i, unicode(name), QtCore.QVariant(value))
            if value == current_value:
                current_value_available = True
        if not current_value_available and current_index > 0:
            self.insertItem(i+1, current_name, QtCore.QVariant(current_value))
        # to prevent loops in the onetomanychoices editor, only set the value
        # again when it's not valueloading
        if current_value != ValueLoading:
            self.set_value( current_value )

    def set_field_attributes(self, editable=True, choices=None, **kwargs):
        if choices != None:
            self.set_choices(choices)
        self.setEnabled(editable!=False)

    def get_choices(self):
        """
    :rtype: a list of (value,name) tuples
    """
        from camelot.core.utils import variant_to_pyobject
        return [(variant_to_pyobject(self.itemData(i)),
                 unicode(self.itemText(i))) for i in range(self.count())]

    def set_value(self, value):
        """Set the current value of the combobox where value, the name displayed
        is the one that matches the value in the list set with set_choices"""
        from camelot.core.utils import variant_to_pyobject
        value = AbstractCustomEditor.set_value(self, value)
        self.setProperty( 'value', QtCore.QVariant(value) )
        self.valueChanged.emit()
        if not self._value_loading and value != NotImplemented:
            for i in range(self.count()):
                if value == variant_to_pyobject(self.itemData(i)):
                    self.setCurrentIndex(i)
                    return
            # it might happen, that when we set the editor data, the set_choices
            # method has not happened yet or the choices don't contain the value
            # set
            self.setCurrentIndex( -1 )
            LOGGER.error( u'Could not set value %s in field %s because it is not in the list of choices'%( unicode( value ),
                                                                                                           unicode( self.objectName() ) ) )
            LOGGER.error( u'Valid choices include : ' )
            for i in range(self.count()):
                LOGGER.error( ' - %s'%unicode(variant_to_pyobject(self.itemData(i))) )

    def get_value(self):
        """Get the current value of the combobox"""
        from camelot.core.utils import variant_to_pyobject
        current_index = self.currentIndex()
        if current_index >= 0:
            value = variant_to_pyobject(self.itemData(self.currentIndex()))
        else:
            value = ValueLoading
        return AbstractCustomEditor.get_value(self) or value
