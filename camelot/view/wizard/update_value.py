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

"""A wizard to update a field on a collection of objects"""

from PyQt4 import QtGui, QtCore

from camelot.view.controls.editors import ChoicesEditor
from camelot.view.controls import delegates
from camelot.core.utils import ugettext_lazy as _
from camelot.view.model_thread import post
from camelot.view.proxy import ValueLoading
from camelot.view.wizard.pages.update_entities_page import UpdateEntitiesPage

class ReplaceContentsData(object):
    
    def __init__(self):
        self.field = None
        self.value = None
        
class SelectValuePage(QtGui.QWizardPage):
    """Page to select a value to update"""

    title = _('Replace field contents')
    sub_title = _('Select the field to update and enter its new value')
    
    def __init__(self, parent, admin, data):
        super(SelectValuePage, self).__init__(parent)
        self.setTitle( unicode(self.title) )
        self.setSubTitle( unicode(self.sub_title) )

        self.editor = ChoicesEditor()
        layout = QtGui.QVBoxLayout()
        layout.addWidget(self.editor)
        self.setLayout(layout)
        self._fields = {}
        self._data = data
        self.editor.currentIndexChanged.connect( self.field_changed )
        self._value_editor = None
        
        post(admin.get_all_fields_and_attributes, self.set_fields)
        
    def set_fields(self, fields):
        self._fields = fields
        
        def filter(attributes):
            if not attributes['editable']:
                return False
            if attributes['delegate'] in (delegates.One2ManyDelegate, delegates.ManyToManyDelegate):
                return False
            return True
        
        choices = [(field, attributes['name']) for field, attributes in fields.items() if filter(attributes)]
        self.editor.set_choices(choices)
        self.editor.set_value((choices+[(None,None)])[1][0])
        self.field_changed(0)
        
    def value_changed(self):
        if self._value_editor:
            self._data.value = self._value_editor.get_value()
            
    @QtCore.pyqtSlot(int)
    def field_changed(self, index):
        if self._value_editor:
            self.layout().removeWidget(self._value_editor)
            self._value_editor.deleteLater()
            self._value_editor = None
        selected_field = self.editor.get_value()
        if selected_field!=ValueLoading:
            self._data.field = selected_field
            self._data.value = None
            field_attributes = self._fields[selected_field]
            delegate = field_attributes['delegate'](**field_attributes)
            option = QtGui.QStyleOptionViewItem()
            option.version = 5
            self._value_editor = delegate.createEditor( self, option, None )
            self._value_editor.editingFinished.connect( self.value_changed )
            self.layout().addWidget(self._value_editor)
            if isinstance(delegate, delegates.Many2OneDelegate):
                self._value_editor.set_value(lambda:None)
            else:
                self._value_editor.set_value(None)

class ReplaceContentsPage(UpdateEntitiesPage):
    
    title = _('Replace field contents')
    
    def __init__(self, parent, collection_getter, data):
        super(ReplaceContentsPage, self).__init__(parent=parent, collection_getter=collection_getter)
        self._data = data
        
    def update_entity(self, obj):
        setattr(obj, self._data.field, self._data.value)
    
class UpdateValueWizard(QtGui.QWizard):
    """This wizard presents the user with a selection of the possible fields to
    update and a new value.  Then this field is changed for all objects in a given
    collection"""

    select_value_page = SelectValuePage
    
    window_title = _('Replace')

    def __init__(self, parent=None, selection_getter=None, admin=None):
        """:param model: a collection proxy on which to replace the field contents"""
        super(UpdateValueWizard, self).__init__(parent)
        self.setWindowTitle( unicode(self.window_title) )
        data = ReplaceContentsData()
        assert selection_getter
        assert admin
        self.addPage(SelectValuePage(parent=self, admin=admin, data=data))
        self.addPage(ReplaceContentsPage(parent=self, collection_getter=selection_getter, data=data))

