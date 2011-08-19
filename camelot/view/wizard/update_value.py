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

import sqlalchemy.schema

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

        editor = ChoicesEditor( parent=self )
        editor.setObjectName( 'field_choice' )
        layout = QtGui.QVBoxLayout()
        layout.addWidget( editor )
        self.setLayout( layout )
        self._fields = {}
        self._data = data
        editor.currentIndexChanged.connect( self.field_changed )
        if admin:
            post( admin.get_all_fields_and_attributes, 
                  self.set_fields )
        
    def set_fields(self, fields):
        self._fields = fields
        
        def filter(attributes):
            if not attributes['editable']:
                return False
            if attributes['delegate'] in (delegates.One2ManyDelegate, delegates.ManyToManyDelegate):
                return False
            return True
        
        choices = [(field, attributes['name']) for field, attributes in fields.items() if filter(attributes)]
        editor = self.findChild( QtGui.QWidget, 'field_choice' )
        if editor != None:
            editor.set_choices(choices)
            editor.set_value((choices+[(None,None)])[1][0])
            self.field_changed(0)
        
    def value_changed(self, value_editor=None):
        if not value_editor:
            value_editor = self.findChild( QtGui.QWidget, 'value_editor' )
        if value_editor != None:
            delegate = self._fields[self._data.field]['delegate']
            value = value_editor.get_value()
            # make sure a value is always callable
            if issubclass(delegate, delegates.Many2OneDelegate):
                value_getter = value
            else:
                value_getter = lambda:value
            self._data.value = value_getter
            
    @QtCore.pyqtSlot(int)
    def field_changed(self, index):
        selected_field = ValueLoading
        editor = self.findChild( QtGui.QWidget, 'field_choice' )
        value_editor = self.findChild( QtGui.QWidget, 'value_editor' )
        if editor != None:
            selected_field = editor.get_value()
        if value_editor != None:
            value_editor.deleteLater()
        if selected_field != ValueLoading:
            self._data.field = selected_field
            self._data.value = None
            field_attributes = self._fields[selected_field]
            static_field_attributes = dict( (k,v) for k,v in field_attributes.items() if not callable(v) )
            delegate = field_attributes['delegate']( parent = self,
                                                     **static_field_attributes)
            option = QtGui.QStyleOptionViewItem()
            option.version = 5
            value_editor = delegate.createEditor( self, option, None )
            value_editor.setObjectName( 'value_editor' )
            value_editor.set_field_attributes( **static_field_attributes )
            self.layout().addWidget( value_editor )
            value_editor.editingFinished.connect( self.value_changed )
            # try to set sensible defaults for value
            if isinstance(delegate, delegates.Many2OneDelegate):
                value_editor.set_value(lambda:None)
            else:
                default = static_field_attributes.get('default', None)
                choices = static_field_attributes.get('choices', None)
                if default != None and not isinstance(default, sqlalchemy.schema.ColumnDefault):
                    value_editor.set_value( default )
                elif choices and len(choices):
                    value_editor.set_value( choices[0][0] )
                else:
                    value_editor.set_value( None )
            # force the value editor, since the previous one is still around
            self.value_changed( value_editor )

class ReplaceContentsPage(UpdateEntitiesPage):
    
    title = _('Replace field contents')
    
    def __init__(self, parent, collection_getter, data):
        super(ReplaceContentsPage, self).__init__(parent=parent, collection_getter=collection_getter)
        self._data = data
        
    def update_entity(self, obj):
        value = self._data.value()
        setattr(obj, self._data.field, value)
    
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
        self.addPage(SelectValuePage(parent=self, admin=admin, data=data))
        self.addPage(ReplaceContentsPage(parent=self, collection_getter=selection_getter, data=data))

