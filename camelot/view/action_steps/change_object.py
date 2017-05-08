#  ============================================================================
#
#  Copyright (C) 2007-2016 Conceptive Engineering bvba.
#  www.conceptive.be / info@conceptive.be
#
#  Redistribution and use in source and binary forms, with or without
#  modification, are permitted provided that the following conditions are met:
#      * Redistributions of source code must retain the above copyright
#        notice, this list of conditions and the following disclaimer.
#      * Redistributions in binary form must reproduce the above copyright
#        notice, this list of conditions and the following disclaimer in the
#        documentation and/or other materials provided with the distribution.
#      * Neither the name of Conceptive Engineering nor the
#        names of its contributors may be used to endorse or promote products
#        derived from this software without specific prior written permission.
#  
#  THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
#  ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
#  WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
#  DISCLAIMED. IN NO EVENT SHALL <COPYRIGHT HOLDER> BE LIABLE FOR ANY
#  DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
#  (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
#  LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
#  ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
#  (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
#  SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#
#  ============================================================================

import six
from six import moves

from ...core.qt import QtCore, QtGui, QtWidgets, Qt, variant_to_py
from ..workspace import apply_form_state

from camelot.admin.action import ActionStep
from camelot.admin.action.form_action import FormActionGuiContext
from camelot.core.item_model import ValidRole, ValidMessageRole
from camelot.core.exception import CancelRequest
from camelot.core.utils import ugettext_lazy as _
from camelot.core.utils import ugettext
from camelot.view.action_runner import hide_progress_dialog
from camelot.view.art import Icon
from camelot.view.controls import delegates, editors
from camelot.view.controls.formview import FormWidget
from camelot.view.controls.actionsbox import ActionsBox
from camelot.view.controls.standalone_wizard_page import StandaloneWizardPage
from camelot.view.proxy import ValueLoading
from camelot.view.proxy.collection_proxy import CollectionProxy

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
                  form_display,
                  columns,
                  form_actions,
                  accept,
                  reject,
                  title =  _('Please complete'),
                  subtitle = _('Complete the form and press the OK button'),
                  icon = Icon('tango/22x22/categories/preferences-system.png'),
                  parent=None,
                  flags=QtCore.Qt.Dialog ):
        super(ChangeObjectDialog, self).__init__( '', parent, flags )
        self.setWindowTitle( admin.get_verbose_name() )
        self.set_banner_logo_pixmap( icon.getQPixmap() )
        self.set_banner_title( six.text_type(title) )
        self.set_banner_subtitle( six.text_type(subtitle) )
        self.banner_widget().setStyleSheet('background-color: white;')

        model = CollectionProxy(admin)

        layout = QtWidgets.QHBoxLayout()
        layout.setObjectName( 'form_and_actions_layout' )
        form_widget = FormWidget(admin=admin,
                                 model=model,
                                 form_display=form_display,
                                 columns=columns,
                                 parent=self)
        layout.addWidget( form_widget )
        model.headerDataChanged.connect(self.header_data_changed)
        form_widget.setObjectName( 'form' )
        if hasattr(admin, 'form_size') and admin.form_size:
            form_widget.setMinimumSize(admin.form_size[0], admin.form_size[1])
        self.main_widget().setLayout(layout)

        self.gui_context = FormActionGuiContext()
        self.gui_context.workspace = self
        self.gui_context.admin = admin
        self.gui_context.view = self
        self.gui_context.widget_mapper = self.findChild( QtWidgets.QDataWidgetMapper,
                                                         'widget_mapper' )

        cancel_button = QtWidgets.QPushButton(six.text_type(reject))
        cancel_button.setObjectName( 'cancel' )
        ok_button = QtWidgets.QPushButton(six.text_type(accept))
        ok_button.setObjectName( 'ok' )
        layout = QtWidgets.QHBoxLayout()
        layout.setDirection( QtWidgets.QBoxLayout.RightToLeft )
        layout.addWidget( ok_button )
        layout.addWidget( cancel_button )
        layout.addStretch()
        self.buttons_widget().setLayout( layout )
        self._change_complete(False)
        cancel_button.pressed.connect( self.reject )
        ok_button.pressed.connect( self.accept )
        # set the actions in the actions panel
        self.set_actions(form_actions)
        # set the value last, so the validity can be updated
        model.set_value(admin.get_proxy([obj]))
        list(model.add_columns((fn for fn, _fa in columns)))

    @QtCore.qt_slot(list)
    def set_actions(self, actions):
        layout = self.findChild(QtWidgets.QLayout, 'form_and_actions_layout' )
        if actions and layout:
            side_panel_layout = QtWidgets.QVBoxLayout()
            actions_widget = ActionsBox( parent = self,
                                         gui_context = self.gui_context )
            actions_widget.setObjectName('actions')
            actions_widget.set_actions( actions )
            side_panel_layout.addWidget( actions_widget )
            side_panel_layout.addStretch()
            layout.addLayout( side_panel_layout )

    @QtCore.qt_slot(int, int, int)
    def header_data_changed(self, orientation, first, last):
        if orientation == Qt.Vertical:
            model = self.sender()
            valid = variant_to_py(model.headerData(0, orientation, ValidRole))
            self._change_complete(valid or False)

    def _change_complete(self, complete):
        ok_button = self.findChild( QtWidgets.QPushButton, 'ok' )
        cancel_button = self.findChild( QtWidgets.QPushButton, 'cancel' )
        if ok_button is not None:
            ok_button.setEnabled( complete )
            ok_button.setDefault( complete )
        if cancel_button is not None:
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
                  invalid_rows,
                  parent = None,
                  flags = QtCore.Qt.Window ):
        super(ChangeObjectsDialog, self).__init__( '', parent, flags )
        self.banner_widget().setStyleSheet('background-color: white;')
        table_widget = editors.One2ManyEditor(
            admin = admin,
            parent = self,
            create_inline = True,
        )
        self.invalid_rows = invalid_rows
        model = table_widget.get_model()
        model.headerDataChanged.connect(self.header_data_changed)
        table_widget.set_value(objects)
        table_widget.setObjectName( 'table_widget' )
        note = editors.NoteEditor( parent=self )
        note.set_value(None)
        note.setObjectName( 'note' )
        layout = QtWidgets.QVBoxLayout()
        layout.addWidget( table_widget )
        layout.addWidget( note )
        self.main_widget().setLayout( layout )
        self.set_default_buttons()
        self.update_complete(model)

    @QtCore.qt_slot(int, int, int)
    def header_data_changed(self, orientation, first, last):
        if orientation == Qt.Vertical:
            model = self.sender()
            for row in moves.xrange(first, last+1):
                valid = variant_to_py(model.headerData(row, orientation, ValidRole))
                if (valid==True) and (row in self.invalid_rows):
                    self.invalid_rows.remove(row)
                    self.update_complete(model)
                elif (valid==False) and (row not in self.invalid_rows):
                    self.invalid_rows.add(row)
                    self.update_complete(model)
                elif (valid==False) and (row==min(self.invalid_rows)):
                    self.update_complete(model)

    def update_complete(self, model):
        complete = (len(self.invalid_rows)==0)
        note = self.findChild( QtWidgets.QWidget, 'note' )
        ok = self.findChild( QtWidgets.QWidget, 'accept' )
        if note != None and ok != None:
            ok.setEnabled(complete)
            if complete:
                note.set_value( None )
            else:
                row = min(self.invalid_rows)
                note.set_value(u'{0}<br/>{1}'.format(
                    ugettext(u'Please correct row {0} before proceeding.').format(row+1),
                    variant_to_py(model.headerData(row, Qt.Vertical, ValidMessageRole))
                ))

class ChangeObject( ActionStep ):
    """
    Pop up a form for the user to change an object

    :param obj: the object to change
    :param admin: an instance of an admin class to use to edit the
        object, None if the default is to be taken

    .. attribute:: accept

        The text shown in the accept button

    .. attribute:: reject

        The text shown in the reject button

    """

    def __init__( self, obj, admin=None ):
        self.obj = obj
        self.admin = admin
        self.accept = _('OK')
        self.reject = _('Cancel')

    def get_object( self ):
        """Use this method to get access to the object to change in unit tests

        :return: the object to change
        """
        return self.obj

    def render( self, gui_context ):
        """create the dialog. this method is used to unit test
        the action step."""
        super(ChangeObject, self).gui_run(gui_context)
        dialog = ChangeObjectDialog(self.obj,
                                    self.admin,
                                    self.form_display,
                                    self.columns,
                                    self.form_actions,
                                    self.accept,
                                    self.reject)
        return dialog

    def gui_run( self, gui_context ):
        dialog = self.render(gui_context)
        apply_form_state(dialog, None, self.admin.form_state)
        with hide_progress_dialog( gui_context ):
            result = dialog.exec_()
            if result == QtWidgets.QDialog.Rejected:
                raise CancelRequest()
            return self.obj

    def model_run(self, model_context):
        cls = self.obj.__class__
        self.admin = self.admin or model_context.admin.get_related_admin( cls )
        self.form_display = self.admin.get_form_display()
        self.columns = self.admin.get_fields()
        self.form_actions = self.admin.get_form_actions(None)
        
class ChangeObjects( ActionStep ):
    """
    Pop up a list for the user to change objects

    :param objects: a list of objects to change
    :param admin: an instance of an admin class to use to edit the objects.
    :param validate: validate all objects before allowing the user to change
        them.  If objects are not validated before showing them, only the
        visible objects will be validated.  But validation of all  objects might
        take a lot of time.

    .. image:: /_static/listactions/import_from_file_preview.png

    This action step can be customised using these attributes :

    .. attribute:: window_title

        the window title of the dialog shown

    .. attribute:: title

        the title of the dialog shown

    .. attribute:: subtitle

        the subtitle of the dialog shown

    .. attribute:: icon

        the :class:`camelot.view.art.Icon` in the top right corner of
        the dialog

    """

    def __init__(self, objects, admin, validate=True):
        self.objects = objects
        self.admin = admin
        self.window_title = admin.get_verbose_name_plural()
        self.title = _('Data Preview')
        self.subtitle = _('Please review the data below.')
        self.icon = Icon('tango/32x32/mimetypes/x-office-spreadsheet.png')
        self.invalid_rows = set()
        if validate==True:
            validator = self.admin.get_validator()
            for row, obj in enumerate(objects):
                for message in validator.validate_object(obj):
                    self.invalid_rows.add(row)
                    break
                

    def get_objects( self ):
        """Use this method to get access to the objects to change in unit tests

        :return: the object to change
        """
        return self.objects

    def render( self ):
        """create the dialog. this method is used to unit test
        the action step."""
        dialog = ChangeObjectsDialog(self.admin.get_proxy(self.objects),
                                     self.admin,
                                     self.invalid_rows)
        dialog.setWindowTitle( six.text_type( self.window_title ) )
        dialog.set_banner_title( six.text_type( self.title ) )
        dialog.set_banner_subtitle( six.text_type( self.subtitle ) )
        dialog.set_banner_logo_pixmap( self.icon.getQPixmap() )
        #
        # the dialog cannot estimate its size, so use 75% of screen estate
        #
        desktop = QtWidgets.QApplication.desktop()
        available_geometry = desktop.availableGeometry( dialog )
        dialog.resize( available_geometry.width() * 0.75,
                       available_geometry.height() * 0.75 )
        return dialog

    def gui_run( self, gui_context ):
        dialog = self.render()
        with hide_progress_dialog( gui_context ):
            result = dialog.exec_()
            if result == QtWidgets.QDialog.Rejected:
                raise CancelRequest()
            return self.objects

class ChangeFieldDialog( StandaloneWizardPage ):
    """A dialog to change a field of  an object.
    """

    def __init__( self,
                  admin,
                  field_attributes,
                  field_name,
                  field_value = None,
                  parent = None,
                  flags=QtCore.Qt.Dialog ):
        super(ChangeFieldDialog, self).__init__( '', parent, flags )
        from camelot.view.controls.editors import ChoicesEditor
        self.field_attributes = field_attributes
        self.field = field_name
        self.value = None
        self.static_field_attributes = admin.get_static_field_attributes
        self.banner_widget().setStyleSheet('background-color: white;')
        editor = ChoicesEditor( parent=self )
        editor.setObjectName( 'field_choice' )
        layout = QtWidgets.QVBoxLayout()
        layout.addWidget( editor )
        self.main_widget().setLayout( layout )
        choices = [(field, six.text_type(attributes['name'])) for field, attributes in six.iteritems(field_attributes)]
        choices.sort( key = lambda choice:choice[1] )
        editor.set_choices( choices + [(None,'')] )
        editor.set_value(self.field)
        self.field_changed(field_value)
        editor.editingFinished.connect( self.field_changed )
        self.set_default_buttons()
        if self.field is not None:
            value_editor = self.findChild(QtWidgets.QWidget, 'value_editor')
            if value_editor is not None:
                value_editor.setFocus()

    @QtCore.qt_slot()
    def field_changed(self, value=None):
        selected_field = ValueLoading
        editor = self.findChild( QtWidgets.QWidget, 'field_choice' )
        value_editor = self.findChild( QtWidgets.QWidget, 'value_editor' )
        if editor != None:
            selected_field = editor.get_value()
        if value_editor != None:
            value_editor.deleteLater()
        if selected_field not in (None, ValueLoading):
            self.field = selected_field
            self.value = value
            static_field_attributes = list(self.static_field_attributes([selected_field]))[0]
            # if the field is displayed in this dialog, it should be editable
            static_field_attributes['editable'] = True
            delegate = static_field_attributes['delegate'](parent = self,
                                                            **static_field_attributes)
            option = QtGui.QStyleOptionViewItem()
            option.version = 5
            value_editor = delegate.createEditor( self, option, None )
            value_editor.setObjectName( 'value_editor' )
            value_editor.set_field_attributes( **static_field_attributes )
            self.main_widget().layout().addWidget( value_editor )
            value_editor.editingFinished.connect( self.value_changed )
            value_editor.set_value(value)
            self.value_changed( value_editor )

    def value_changed(self, value_editor=None):
        if not value_editor:
            value_editor = self.findChild( QtWidgets.QWidget, 'value_editor' )
        if value_editor != None:
            self.value = value_editor.get_value()

class ChangeField( ActionStep ):
    """
    Pop up a list of fields from an object a user can change.  When the
    user selects a field, an appropriate widget is shown to change the
    value of that field.

    :param admin: the admin of the object of which to change the field
    :param field_attributes: a list of field attributes of the fields that
        can be changed.  If `None` is given, all editable fields are shown.
    :param field_name: the name of the selected field when opening the dialog
    :param field_value: the value of the selected field when opening the dialog

    This action step returns a tuple with the name of the selected field, and
    its new value.

    This action step can be customised using these attributes :

    .. attribute:: window_title

        the window title of the dialog shown

    .. attribute:: title

        the title of the dialog shown

    .. attribute:: subtitle

        the subtitle of the dialog shown

    """

    def __init__(self,
                 admin,
                 field_attributes = None,
                 field_name = None,
                 field_value = None,
                 ):
        super( ChangeField, self ).__init__()
        self.admin = admin
        self.field_name = field_name
        self.field_value = field_value
        if field_attributes is None:
            field_attributes = dict(admin.get_all_fields_and_attributes())
            not_editable_fields = []
            for key, attributes in six.iteritems(field_attributes):
                if not attributes.get('editable', False):
                    not_editable_fields.append(key)
                elif attributes.get('delegate', None) in (delegates.One2ManyDelegate,):
                    not_editable_fields.append(key)
            for key in not_editable_fields:
                field_attributes.pop(key)
        self.field_attributes = field_attributes
        self.window_title = admin.get_verbose_name_plural()
        self.title = _('Replace field contents')
        self.subtitle = _('Select the field to update and enter its new value')

    def render( self ):
        """create the dialog. this method is used to unit test
        the action step."""
        dialog = ChangeFieldDialog(
            self.admin, self.field_attributes, self.field_name, self.field_value
        )
        dialog.setWindowTitle( six.text_type( self.window_title ) )
        dialog.set_banner_title( six.text_type( self.title ) )
        dialog.set_banner_subtitle( six.text_type( self.subtitle ) )
        return dialog

    def gui_run( self, gui_context ):
        dialog = self.render()
        with hide_progress_dialog( gui_context ):
            result = dialog.exec_()
            if result == QtWidgets.QDialog.Rejected:
                raise CancelRequest()
            return (dialog.field, dialog.value)


