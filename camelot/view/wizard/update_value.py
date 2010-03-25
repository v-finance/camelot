#  ==================================================================================
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
#  ==================================================================================

"""A wizard to update a field on a collection of objects"""

from PyQt4 import QtGui, QtCore

from camelot.view.controls.editors import ChoicesEditor, editingFinished
from camelot.core.utils import ugettext_lazy as _
from camelot.view.model_thread import post

class SelectValuePage(QtGui.QWizardPage):
    """Page to select a value to update"""

    title = _('Replace field contents')
    sub_title = _('Select the field to update and enter its new value')
    
    def __init__(self, parent, model):
        super(SelectValuePage, self).__init__(parent)
        self.setTitle( unicode(self.title) )
        self.setSubTitle( unicode(self.sub_title) )

        self.editor = ChoicesEditor()
        layout = QtGui.QVBoxLayout()
        layout.addWidget(self.editor)
        self.setLayout(layout)
        self._fields = {}
        self.connect(self.editor, QtCore.SIGNAL('currentIndexChanged(int)'), self.field_changed)
        self._value_editor = None
        
        post(model.get_admin().get_all_fields_and_attributes, self.set_fields)
        
    def set_fields(self, fields):
        self._fields = fields
        choices = [(field, attributes['name']) for field, attributes in fields.items() if attributes['editable']]
        self.editor.set_choices(choices)
        self.editor.set_value((choices+[(None,None)])[1][0])
        self.field_changed(0)
        
    def field_changed(self, index):
        if self._value_editor:
            self.layout().removeWidget(self._value_editor)
            self._value_editor.deleteLater()
            self._value_editor = None
        field_attributes = self._fields[self.editor.get_value()]
        delegate = field_attributes['delegate'](**field_attributes)
        option = QtGui.QStyleOptionViewItem()
        option.version = 5
        self._value_editor = delegate.createEditor( self, option, None )
        self.layout().addWidget(self._value_editor)
        self._value_editor.set_value(None)

class UpdateValueWizard(QtGui.QWizard):
    """This wizard presents the user with a selection of the possible fields to
    update and a new value.  Then this field is changed for all objects in a given
    collection"""

    select_value_page = SelectValuePage
    
    window_title = _('Replace')

    def __init__(self, parent=None, model=None):
        """:param model: a collection proxy on which to replace the field contents"""
        super(UpdateValueWizard, self).__init__(parent)
        self.setWindowTitle( unicode(self.window_title) )
        assert model
        self.addPage(SelectValuePage(parent=self, model=model))