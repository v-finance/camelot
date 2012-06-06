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

from camelot.admin.action import ActionStep
from camelot.core.exception import CancelRequest
from camelot.core.utils import ugettext_lazy as _
from camelot.core.utils import ugettext
from camelot.view.art import Icon
from camelot.view.controls import delegates
from camelot.view.controls.standalone_wizard_page import StandaloneWizardPage
from camelot.view.model_thread import post
from camelot.view.proxy import ValueLoading

class ChangeObjectDialog( StandaloneWizardPage ):
    """A dialog to change an object.  This differs from a FormView in that
    it does not contains Actions, and has an OK button that is enabled when
    the object is valid.
    
    :param obj: The object to change
    :param admin: The admin class used to create a form
    
    .. image:: /_static/actionsteps/change_object.png
    """
        
    def __init__( self, 
                  obj, 
                  admin,
                  title =  _('Please complete'),
                  subtitle = _('Complete the form and press the OK button'),
                  icon = Icon('tango/22x22/categories/preferences-system.png'),
                  parent=None, 
                  flags=QtCore.Qt.Dialog ):
        from camelot.view.controls.formview import FormWidget
        from camelot.view.proxy.collection_proxy import CollectionProxy
        super(ChangeObjectDialog, self).__init__( '', parent, flags )
        
        self.setWindowTitle( admin.get_verbose_name() )
        self.set_banner_logo_pixmap( icon.getQPixmap() )
        self.set_banner_title( unicode(title) )
        self.set_banner_subtitle( unicode(subtitle) )
        self.banner_widget().setStyleSheet('background-color: white;')
        
        model = CollectionProxy(admin, lambda:[obj], admin.get_fields)
        validator = model.get_validator()
        layout = QtGui.QVBoxLayout()
        form_widget = FormWidget( parent=self, admin=admin )
        layout.addWidget( form_widget )
        validator.validity_changed_signal.connect( self._validity_changed )
        form_widget.set_model( model )
        form_widget.setObjectName( 'form' )
        self.main_widget().setLayout(layout)
    
        cancel_button = QtGui.QPushButton( ugettext('Cancel') )
        cancel_button.setObjectName( 'cancel' )
        ok_button = QtGui.QPushButton( ugettext('OK') )
        ok_button.setObjectName( 'ok' )
        ok_button.setEnabled( False )
        layout = QtGui.QHBoxLayout()
        layout.setDirection( QtGui.QBoxLayout.RightToLeft )
        layout.addWidget( ok_button )
        layout.addWidget( cancel_button )
        layout.addStretch()
        self.buttons_widget().setLayout( layout )
        cancel_button.pressed.connect( self.reject )
        ok_button.pressed.connect( self.accept )
        
        # do inital validation, so the validity changed signal is valid
        self._validity_changed( 0 )
        
    @QtCore.pyqtSlot(int)
    def _validity_changed(self, row):
        form = self.findChild( QtGui.QWidget, 'form' )
        if not form:
            return
        model = form.get_model()
 
        def is_valid():
            return model.get_validator().isValid(0)
        
        post(is_valid, self._change_complete)
        
    def _change_complete(self, complete):
        ok_button = self.findChild( QtGui.QPushButton, 'ok' )
        cancel_button = self.findChild( QtGui.QPushButton, 'cancel' )
        if ok_button != None:
            ok_button.setEnabled( complete )
            ok_button.setDefault( complete )
        if cancel_button != None:
            ok_button.setDefault( not complete )

class ChangeObjectsDialog( StandaloneWizardPage ):
    """A dialog to change a list of objects.  This differs from a ListView in 
    that it does not contains Actions, and has an OK button that is enabled when
    all objects are valid.
    
    :param objects: The object to change
    :param admin: The admin class used to create a form
    
    .. image:: /_static/actionsteps/change_object.png
    """

    def __init__( self, 
                  objects, 
                  admin, 
                  parent = None, 
                  flags = QtCore.Qt.Window ):
        from camelot.view.controls import editors
        from camelot.view.proxy.collection_proxy import CollectionProxy
        
        super(ChangeObjectsDialog, self).__init__( '', parent, flags )
        
        self.setWindowTitle( admin.get_verbose_name_plural() )
        self.set_banner_title( _('Data Preview') )
        self.set_banner_subtitle( _('Please review the data below.') )
        self.banner_widget().setStyleSheet('background-color: white;')
        self.set_banner_logo_pixmap( Icon('tango/32x32/mimetypes/x-office-spreadsheet.png').getQPixmap() )
        model = CollectionProxy( admin, lambda:objects, admin.get_columns)
        self.validator = model.get_validator()
        self.validator.validity_changed_signal.connect( self.update_complete )
        model.layoutChanged.connect( self.validate_all_rows )

        table_widget = editors.One2ManyEditor(
            admin = admin,
            parent = self,
            create_inline = True,
        )
        table_widget.set_value( model )
        table_widget.setObjectName( 'table_widget' )
        note = editors.NoteEditor( parent=self )
        note.set_value(None)
        note.setObjectName( 'note' )
        layout = QtGui.QVBoxLayout()
        layout.addWidget( table_widget )
        layout.addWidget( note )
        self.main_widget().setLayout( layout )
    
        cancel_button = QtGui.QPushButton( ugettext('Cancel') )
        ok_button = QtGui.QPushButton( ugettext('OK') )
        ok_button.setObjectName( 'ok' )
        ok_button.setEnabled( False )
        layout = QtGui.QHBoxLayout()
        layout.setDirection( QtGui.QBoxLayout.RightToLeft )
        layout.addWidget( ok_button )
        layout.addWidget( cancel_button )
        layout.addStretch()
        self.buttons_widget().setLayout( layout )
        cancel_button.pressed.connect( self.reject )
        ok_button.pressed.connect( self.accept )
        self.validate_all_rows()

    @QtCore.pyqtSlot()
    def validate_all_rows(self):
        post( self.validator.validate_all_rows, self._all_rows_validated)

    def _all_rows_validated(self, *args):
        self.update_complete( 0 )

    @QtCore.pyqtSlot(int)
    def update_complete(self, row=0):
        complete = (self.validator.number_of_invalid_rows()==0)
        note = self.findChild( QtGui.QWidget, 'note' )
        ok = self.findChild( QtGui.QWidget, 'ok' )
        if note != None and ok != None:
            ok.setEnabled( complete )
            if complete:
                note.set_value( None )
            else:
                note.set_value(_(
                    'Please correct the data above before proceeding with the '
                    'import.<br/>Incorrect cells have a pink background.'
                ))
    
class ChangeObject( ActionStep ):
    """
    Pop up a form for the user to change an object
    
    :param obj: the object to change
    :param admin: an instance of an admin class to use to edit the
        object, None if the default is to be taken
    """
        
    def __init__( self, obj, admin=None ):
        self._obj = obj
        self._admin = admin
        
    def get_object( self ):
        """Use this method to get access to the object to change in unit tests
        
        :return: the object to change
        """
        return self._obj

    def gui_run( self, gui_context ):
        cls = self._obj.__class__
        admin = self._admin or gui_context.admin.get_related_admin( cls )
        dialog = ChangeObjectDialog( self._obj, admin )
        result = dialog.exec_()
        if result == QtGui.QDialog.Rejected:
            raise CancelRequest()
        return self._obj

class ChangeObjects( ActionStep ):
    """
    Pop up a list for the user to change objects
    
    :param objects: a list of objects to change
    :param admin: an instance of an admin class to use to edit the objects.
    
    .. image:: /_static/listactions/import_from_file_preview.png
    
    """
    
    def __init__( self, objects, admin ):
        self.objects = objects
        self.admin = admin
        
    def get_objects( self ):
        """Use this method to get access to the objects to change in unit tests
        
        :return: the object to change
        """
        return self.objects        
    
    def render( self ):
        """create the dialog. this method is used to unit test
        the action step."""
        dialog = ChangeObjectsDialog( self.objects, 
                                      self.admin )
        #
        # the dialog cannot estimate its size, so use 75% of screen estate
        #
        desktop = QtGui.QApplication.desktop()
        available_geometry = desktop.availableGeometry( dialog )
        dialog.resize( available_geometry.width() * 0.75, 
                       available_geometry.height() * 0.75 )
        return dialog
        
    def gui_run( self, gui_context ):
        dialog = self.render()
        result = dialog.exec_()
        if result == QtGui.QDialog.Rejected:
            raise CancelRequest()
        return self.objects

class ChangeFieldDialog( StandaloneWizardPage ):
    """A dialog to change a field of  an object. 
    """

    def __init__( self,
                  admin,
                  field_attributes, 
                  parent = None, 
                  flags=QtCore.Qt.Dialog ):
        super(ChangeFieldDialog, self).__init__( '', parent, flags )
        from camelot.view.controls.editors import ChoicesEditor
        self.field_attributes = field_attributes
        self.field = None
        self.value = None
        self.setWindowTitle( admin.get_verbose_name_plural() )
        self.set_banner_title( _('Replace field contents') )
        self.set_banner_subtitle( _('Select the field to update and enter its new value') )
        self.banner_widget().setStyleSheet('background-color: white;')
        editor = ChoicesEditor( parent=self )
        editor.setObjectName( 'field_choice' )
        layout = QtGui.QVBoxLayout()
        layout.addWidget( editor )
        self.main_widget().setLayout( layout )
        
        def filter(attributes):
            if not attributes['editable']:
                return False
            if attributes['delegate'] in (delegates.One2ManyDelegate,):
                return False
            return True
        
        choices = [(field, attributes['name']) for field, attributes in field_attributes.items() if filter(attributes)]
        choices.sort( key = lambda choice:choice[1] )
        editor.set_choices( choices )
        editor.set_value( ( choices+[(None,None)] )[-1][0] )
        self.field_changed( 0 )  
        editor.currentIndexChanged.connect( self.field_changed )
        
        cancel_button = QtGui.QPushButton( ugettext('Cancel') )
        ok_button = QtGui.QPushButton( ugettext('OK') )
        ok_button.setObjectName( 'ok' )
        layout = QtGui.QHBoxLayout()
        layout.setDirection( QtGui.QBoxLayout.RightToLeft )
        layout.addWidget( ok_button )
        layout.addWidget( cancel_button )
        layout.addStretch()
        self.buttons_widget().setLayout( layout )
        cancel_button.pressed.connect( self.reject )
        ok_button.pressed.connect( self.accept )
        
    @QtCore.pyqtSlot(int)
    def field_changed(self, index):
        import sqlalchemy.schema
        selected_field = ValueLoading
        editor = self.findChild( QtGui.QWidget, 'field_choice' )
        value_editor = self.findChild( QtGui.QWidget, 'value_editor' )
        if editor != None:
            selected_field = editor.get_value()
        if value_editor != None:
            value_editor.deleteLater()
        if selected_field != ValueLoading:
            self.field = selected_field
            self.value = None
            field_attributes = self.field_attributes[selected_field]
            static_field_attributes = dict( (k,v) for k,v in field_attributes.items() if not callable(v) )
            delegate = field_attributes['delegate']( parent = self,
                                                     **static_field_attributes)
            option = QtGui.QStyleOptionViewItem()
            option.version = 5
            value_editor = delegate.createEditor( self, option, None )
            value_editor.setObjectName( 'value_editor' )
            value_editor.set_field_attributes( **static_field_attributes )
            self.main_widget().layout().addWidget( value_editor )
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
            
    def value_changed(self, value_editor=None):
        if not value_editor:
            value_editor = self.findChild( QtGui.QWidget, 'value_editor' )
        if value_editor != None:
            delegate = self.field_attributes[self.field]['delegate']
            value = value_editor.get_value()
            # make sure a value is always callable
            if issubclass(delegate, delegates.Many2OneDelegate):
                value_getter = value
            else:
                value_getter = lambda:value
            self.value = value_getter
            
class ChangeField( ActionStep ):
    """
    Pop up a list of fields from an object a user can change.  When the
    user selects a field, an appropriate widget is shown to change the
    value of that field.
    
    :param admin: the admin of the object of which to change the field
    :param field_attributes: a list of field attributes of the fields that
        can be changed.  If `None` is given, all fields are shown.
        
    This action step returns a tuple with the name of the selected field, and
    its new value.
    """
    
    def __init__(self, admin, field_attributes = None ):
        super( ChangeField, self ).__init__()
        self.admin = admin
        if field_attributes == None:
            field_attributes = admin.get_all_fields_and_attributes()
        self.field_attributes = field_attributes
        
    def render( self ):
        """create the dialog. this method is used to unit test
        the action step."""
        return ChangeFieldDialog( self.admin, 
                                  self.field_attributes )
    
    def gui_run( self, gui_context ):
        dialog = self.render()
        result = dialog.exec_()
        if result == QtGui.QDialog.Rejected:
            raise CancelRequest()
        return (dialog.field, dialog.value)

