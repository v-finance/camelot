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
from PyQt4 import QtGui, QtCore
from PyQt4.QtCore import Qt

from camelot.core.utils import ugettext as _
from camelot.admin.object_admin import ObjectAdmin
from camelot.view.controls.editors.one2manyeditor import One2ManyEditor
from user_translatable_label import UserTranslatableLabel

class Attribute(object):
    """Helper class representing a field attribute's name and its value"""
    def __init__(self, name, value):
        self.name = unicode(name)
        self.value = unicode(value)
                
    class Admin(ObjectAdmin):
        list_display = ['name', 'value']
        field_attributes = {'name':{'minimal_column_width':25},
                            'value':{'minimal_column_width':25}}
                        
class FieldLabel(UserTranslatableLabel):
    """A Label widget used to display the name of a field on a form.
    This label provides the user with the possibility to change the translation
    of the label and review its field attributes.
    """
    
    font_width = None
    
    def __init__(self, field_name, text, field_attributes, admin, parent=None):
        """
        :param field_name: the name of the field
        :param text: user translatable string to be used as field label
        :param field_attributes: the field attributes associated with the field for which
        this is a label
        :param admin: the admin of the object of the field
        """
        super(FieldLabel, self).__init__(text, parent)
        if FieldLabel.font_width == None:
            FieldLabel.font_width = QtGui.QFontMetrics( QtGui.QApplication.font() ).size( Qt.TextSingleLine, 'A' ).width()
        show_field_attributes_action = QtGui.QAction(_('View attributes'), self)
        show_field_attributes_action.triggered.connect( self.show_field_attributes )
        self.addAction(show_field_attributes_action)
        self._field_name = field_name
        self._admin = admin
        self._field_attributes = field_attributes
        
    def sizeHint( self ):
        size_hint = super(FieldLabel, self).sizeHint()
        size_hint.setWidth( self.font_width * max( 20, len( self._field_name ) ) )
        return size_hint
    
    def get_attributes(self):
        import inspect
        
        def attribute_value_to_string(key, value):
            if inspect.isclass(value):
                return value.__name__
            return unicode(value)
        
        return [Attribute(key,attribute_value_to_string(key, value)) for key,value in self._field_attributes.items()]
    
    @QtCore.pyqtSlot()
    def show_field_attributes(self):
        from camelot.view.proxy.collection_proxy import CollectionProxy
                    
        admin = self._admin.get_related_admin( Attribute )
        attributes_collection = CollectionProxy(admin=admin, 
                                                collection_getter=self.get_attributes,
                                                columns_getter=admin.get_columns)
        
        class FieldAttributesDialog(QtGui.QDialog):
            
            def __init__(self, field_name, parent=None):
                super(FieldAttributesDialog, self).__init__(parent)
                self.setWindowTitle(_('Field Attributes'))
                layout = QtGui.QVBoxLayout()
                layout.addWidget( QtGui.QLabel(field_name) )
                editor = One2ManyEditor(admin=admin, editable=False, parent=self)
                editor.set_value(attributes_collection)
                editor.setMinimumSize(600, 400)
                layout.addWidget(editor)
                self.setLayout(layout)
        
        dialog = FieldAttributesDialog(self._field_name, self)
        dialog.exec_()


