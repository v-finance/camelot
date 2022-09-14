# -*- coding: utf-8 -*-

import datetime
import json
import logging
import os
import sys
import unittest

from . import app_admin
from .snippet.background_color import Admin as BackgroundColorAdmin
from .snippet.fields_with_actions import Coordinate
from .snippet.form.inherited_form import InheritedAdmin
from .test_item_model import A, QueryQStandardItemModelMixinCase
from .test_model import ExampleModelMixinCase
from camelot.admin.action import GuiContext
from camelot.admin.action.application_action import ApplicationActionGuiContext
from camelot.admin.action.field_action import FieldActionModelContext
from camelot.admin.icon import CompletionValue
from camelot.admin.application_admin import ApplicationAdmin
from camelot.core.constants import camelot_maxfloat, camelot_minfloat
from camelot.core.exception import UserException
from camelot.core.files.storage import Storage, StoredFile
from camelot.core.item_model import FieldAttributesRole, PreviewRole
from camelot.core.naming import initial_naming_context
from camelot.core.qt import Qt, QtCore, QtGui, QtWidgets, q_string, variant_to_py
from camelot.model.party import Person
from camelot.test import GrabMixinCase, RunningThreadCase
from camelot.view import forms
from camelot.view.action_steps import OpenFormView
from camelot.view.art import ColorScheme
from camelot.view.controls import delegates, editors
from camelot.view.controls.busy_widget import BusyWidget
from camelot.view.controls.delegates import DelegateManager
from camelot.view.controls.editors.datetimeeditor import TimeValidator
from camelot.view.controls.editors.one2manyeditor import One2ManyEditor
from camelot.view.controls.exception import ExceptionDialog, register_exception
from camelot.view.controls.formview import FormEditors
from camelot.view.controls.progress_dialog import ProgressDialog
from camelot.view.controls.tableview import TableWidget
from camelot.view.proxy import ValueLoading
from camelot.view.proxy.collection_proxy import CollectionProxy
from camelot_example.application_admin import MyApplicationAdmin

logger = logging.getLogger('view.unittests')

static_images_path = os.path.join(os.path.dirname(__file__), '..', 'doc', 'sphinx', 'source', '_static')
storage = Storage()

admin = app_admin.get_related_admin(A)

class SignalCounter( QtCore.QObject ):

    def __init__( self ):
        super( SignalCounter, self ).__init__()
        self.counter = 0

    @QtCore.qt_slot()
    def signal_caught( self ):
        self.counter += 1

class EditorsTest(unittest.TestCase, GrabMixinCase):
    """
  Test the basic functionality of the editors :

  - get_value
  - set_value
  - support for ValueLoading
  """

    images_path = static_images_path

    def setUp(self):
        super(EditorsTest, self).setUp()
        self.option = QtWidgets.QStyleOptionViewItem()
        # set version to 5 to indicate the widget will appear on a
        # a form view and not on a table view, so it should not
        # set its background
        self.option.version = 5
        self.editable_kwargs = dict(editable=True, action_routes=[])

    def assert_valid_editor( self, editor, value ):
        """Test the basic functions of an editor that are needed to integrate
        well with Camelot and Qt
        """
        #
        # The editor should remember its when its value is ValueLoading
        #
        #editor.set_value( ValueLoading )
        #self.assertEqual( editor.get_value(), ValueLoading )
        #
        # When a value is set, no editingFinished should be called
        #
        signal_counter = SignalCounter()
        editor.editingFinished.connect( signal_counter.signal_caught )
        editor.set_value( value )
        self.assertEqual( signal_counter.counter, 0 )
        #
        # when the up or down arrow is pressed, the event should be ignored
        # by the editor, to allow the table view to move to the row above or
        # below
        #
        #up_event = QtGui.QKeyEvent( QtCore.QEvent.KeyPress,
        #                            Qt.Key_Up,
        #                            Qt.NoModifier )
        #editor.keyPressEvent( up_event )
        #self.assertFalse( up_event.isAccepted() )

    def assert_vertical_size( self, editor ):
        self.assertEqual( editor.sizePolicy().verticalPolicy(),
                          QtWidgets.QSizePolicy.Policy.Fixed )

    def test_DateEditor(self):
        editor = editors.DateEditor()
        self.assert_vertical_size( editor )
        self.assertEqual( editor.get_value(), ValueLoading )
        editor.set_value( None )
        self.assertEqual( editor.get_value(), None )
        editor.set_value( datetime.date(1980, 12, 31) )
        self.grab_default_states( editor )
        self.assertEqual( editor.get_value(), datetime.date(1980, 12, 31) )
        self.assert_valid_editor( editor, datetime.date(1980, 12, 31) )

    def test_TextLineEditor(self):
        editor = editors.TextLineEditor(parent=None, length=10, **self.editable_kwargs)
        self.assert_vertical_size( editor )
        self.assertEqual( editor.get_value(), ValueLoading )
        editor.set_value( u'za coś tam' )
        self.grab_default_states( editor )
        self.assertEqual( editor.get_value(), u'za coś tam' )
        editor.set_value( ValueLoading )
        self.assertEqual( editor.get_value(), ValueLoading )
        editor = editors.TextLineEditor(parent=None, length=10, **self.editable_kwargs)
        editor.set_field_attributes( editable=False )
        self.assertEqual( editor.get_value(), ValueLoading )
        editor.set_value( u'za coś tam' )
        self.assertEqual( editor.get_value(), u'za coś tam' )
        editor.set_value( None )
        self.assertEqual( editor.get_value(), None )
        editor.set_value( '' )
        self.assertEqual( editor.get_value(), '' )
        # pretend the user has entered some text
        editor.set_value(None)
        editor.findChild(QtWidgets.QLineEdit).setText( u'foo' )
        self.assertTrue( editor.get_value() is not None )
        self.assert_valid_editor( editor, u'za coś tam' )

    def grab_default_states( self, editor ):
        editor.set_field_attributes( editable = True, background_color=ColorScheme.green )
        self.grab_widget( editor, 'editable_background_color')

        editor.set_field_attributes( editable = False, tooltip = 'tooltip' )
        self.grab_widget( editor, 'disabled_tooltip')

        editor.set_field_attributes( editable = False, background_color=ColorScheme.green )
        self.grab_widget( editor, 'disabled_background_color' )

        editor.set_field_attributes( editable = True )
        self.grab_widget( editor, 'editable' )

        editor.set_field_attributes( editable = False )
        self.grab_widget( editor, 'disabled' )

        editor.set_field_attributes( editable = True, tooltip = 'tooltip')
        self.grab_widget( editor, 'editable_tooltip')

    def test_LocalFileEditor( self ):
        editor = editors.LocalFileEditor( parent=None )
        self.assert_vertical_size( editor )
        self.assertEqual( editor.get_value(), ValueLoading )
        editor.set_value( '/home/lancelot/quests.txt' )
        self.grab_default_states( editor )
        self.assertEqual( editor.get_value(), '/home/lancelot/quests.txt' )
        self.assert_valid_editor( editor, '/home/lancelot/quests.txt' )

    def test_BoolEditor(self):
        editor = editors.BoolEditor(parent=None, editable=False, nullable=True)
        self.assert_vertical_size( editor )
        self.assertEqual( editor.get_value(), ValueLoading )
        editor.set_value( True )
        self.grab_default_states( editor )
        self.assertEqual( editor.get_value(), True )
        editor.set_value( False )
        self.assertEqual( editor.get_value(), False )
        editor.set_value( ValueLoading )
        self.assertEqual( editor.get_value(), ValueLoading )
        editor = editors.BoolEditor(parent=None, editable=False)
        self.assertEqual( editor.get_value(), ValueLoading )
        editor.set_value( True )
        self.assertEqual( editor.get_value(), True )
        editor.set_value( False )
        self.assertEqual( editor.get_value(), False )
        # changing the editable state should preserve the value
        editor.set_value( True )
        editor.set_field_attributes( editable = False )
        self.assertEqual( editor.get_value(), True )
        editor.set_field_attributes( editable = True )
        self.assertEqual( editor.get_value(), True )
        self.assert_valid_editor( editor, True )

    def test_ColorEditor(self):
        editor = editors.ColorEditor(parent=None, editable=True)
        self.assert_vertical_size( editor )
        self.assertEqual(editor.get_value(), None)
        editor.set_value('green')
        self.grab_default_states(editor)
        self.assertEqual(editor.get_value(), 'green')

    def test_ChoicesEditor(self):
        editor = editors.ChoicesEditor(parent=None, **self.editable_kwargs)
        self.assert_vertical_size( editor )
        # None equals space for qml compatibility
        none_completion = CompletionValue(
            initial_naming_context._bind_object(None), ' '
        )
        name_2 = initial_naming_context._bind_object(2)
        choices1 = [c._to_dict() for c in [
            CompletionValue(initial_naming_context._bind_object(1), 'A'),
            CompletionValue(name_2, 'B'),
            CompletionValue(initial_naming_context._bind_object(3), 'C'),
        ]]
        editor.set_choices(json.loads(json.dumps(choices1)))
        self.assertEqual(editor.get_value(), ['constant', 'null'])
        editor.set_value(name_2)
        self.assertEqual(editor.get_choices(), choices1 + [
            none_completion._to_dict()
        ])
        self.grab_default_states(editor)
        self.assertEqual(editor.get_value(), list(name_2))
        # None is not in the list of choices, but we should still be able
        # to set it's value to it
        editor.set_value(None )
        self.assertEqual(editor.get_value(), ['constant', 'null'])
        # now change the choices, while the current value is not in the
        # list of new choices
        editor.set_value(name_2)
        name_4 = initial_naming_context._bind_object(4)
        choices2 = [c._to_dict() for c in [
            CompletionValue(name_4, 'D'),
            CompletionValue(initial_naming_context._bind_object(5), 'E'),
            CompletionValue(initial_naming_context._bind_object(6), 'F'),
        ]]
        editor.set_choices(choices2)
        self.assertEqual(editor.get_choices(), choices2 + [
            none_completion._to_dict(),
            CompletionValue(name_2, 'B')._to_dict()
        ])
        editor.set_value(name_4)
        self.assertEqual(editor.get_choices(), choices2 + [
            none_completion._to_dict()
        ])
        # set a value that is not in the list, the value should be
        # accepted, to prevent damage to the actual data
        name_33 = initial_naming_context._bind_object(33)
        editor.set_value(name_33)
        self.assertEqual(editor.get_value(), list(name_33))
        number_of_choices = len(editor.get_choices())
        # set the value back to valid one, the invalid one should be no longer
        # in the list of choices
        editor.set_value(name_4)
        self.assertEqual(number_of_choices-1, len(editor.get_choices()))
        # try strings as keys
        editor = editors.ChoicesEditor(parent=None, **self.editable_kwargs)
        name_c = initial_naming_context._bind_object('c')
        choices3 = [c._to_dict() for c in [
            CompletionValue(initial_naming_context._bind_object('a'), 'A'),
            CompletionValue(initial_naming_context._bind_object('b'), 'A'),
            CompletionValue(name_c, 'C'),
        ]]
        editor.set_choices(choices3)
        editor.set_value(name_c)
        self.assertEqual(editor.get_value(), list(name_c))
        self.assert_valid_editor(editor, name_c)

    def test_FileEditor(self):
        editor = editors.FileEditor(parent=None, **self.editable_kwargs)
        self.assert_vertical_size( editor )
        self.assertEqual( editor.get_value(), ValueLoading )
        self.grab_default_states( editor )
        self.assert_valid_editor( editor, StoredFile( storage, 'test.txt') )

    def test_DateTimeEditor(self):
        validator = TimeValidator()
        self.assertEqual(validator._validate('22', 0), (QtGui.QValidator.State.Intermediate, '22', 0))
        self.assertEqual(validator._validate('59', 0), (QtGui.QValidator.State.Intermediate, '59', 0))
        self.assertEqual(validator._validate('22:', 0), (QtGui.QValidator.State.Intermediate,'22:',  0))
        self.assertEqual(validator._validate(':17', 0), (QtGui.QValidator.State.Intermediate, ':17', 0))
        self.assertEqual(validator._validate('22:7', 0), (QtGui.QValidator.State.Acceptable, '22:7', 0))
        self.assertEqual(validator._validate('22:17', 0), (QtGui.QValidator.State.Acceptable, '22:17', 0))
        self.assertEqual(validator._validate('1:17', 0), (QtGui.QValidator.State.Acceptable, '1:17', 0))
        self.assertEqual(validator._validate('22:7:', 0), (QtGui.QValidator.State.Invalid, '22:7:', 0))
        self.assertEqual(validator._validate('61', 0), (QtGui.QValidator.State.Invalid, '61', 0))
        self.assertEqual(validator._validate('611', 0), (QtGui.QValidator.State.Invalid, '611', 0))
        editor = editors.DateTimeEditor(parent=None, editable=True)
        self.assert_vertical_size( editor )
        self.assertEqual( editor.get_value(), ValueLoading )
        editor.set_value( datetime.datetime(2009, 7, 19, 21, 5, 10, 0) )
        self.assertEqual( editor.get_value(), datetime.datetime(2009, 7, 19, 21, 5, 0 ) )
        self.grab_default_states( editor )
        self.assert_valid_editor( editor, datetime.datetime(2009, 7, 19, 21, 5, 0 ) )
        editor.set_value(None)
        self.assertEqual(editor.get_value(), None)

    def test_FloatEditor(self):
        # Default or explicitly set behaviour of the minimum and maximum of the float editor was moved to the float delegate
        delegate = delegates.FloatDelegate(parent=None, suffix='euro', editable=True)
        field_action_model_context = FieldActionModelContext(
            app_admin.get_related_admin(Person)
        )
        field_action_model_context.value = 3
        field_action_model_context.field_attributes = {}
        item = delegate.get_standard_item(QtCore.QLocale(), field_action_model_context)
        field_attributes = item.data(FieldAttributesRole)
        
        editor = editors.FloatEditor(parent=None, **self.editable_kwargs)
        editor.set_field_attributes(prefix='prefix', editable=True, **field_attributes)
        self.assert_vertical_size( editor )
        self.assertEqual( editor.get_value(), ValueLoading )
        editor.set_value( 0.0 )
        self.assertEqual( editor.get_value(), 0.0 )
        editor.set_value( 3.14 )
        self.grab_default_states( editor )
        self.assertEqual( editor.get_value(), 3.14 )
        editor = editors.FloatEditor(parent=None, option=self.option, **self.editable_kwargs)
        editor.set_field_attributes(suffix=' suffix', editable=True, **field_attributes)
        self.assertEqual( editor.get_value(), ValueLoading )
        editor.set_value( 0.0 )
        self.assertEqual( editor.get_value(), 0.0 )
        editor.set_value( 3.14 )
        self.assertEqual( editor.get_value(), 3.14 )
        editor.set_value( 5.45 )
        editor.set_value( None )
        self.assertEqual( editor.get_value(), None )
        up = QtGui.QKeyEvent(QtCore.QEvent.Type.KeyPress, Qt.Key.Key_Up, Qt.KeyboardModifier.NoModifier)
        spinbox = editor.findChild(QtWidgets.QWidget, 'spinbox')
        self.assertEqual(spinbox.minimum(), camelot_minfloat-1)
        self.assertEqual(spinbox.maximum(), camelot_maxfloat)
        spinbox.keyPressEvent(up)
        self.assertEqual(editor.get_value(), 0.0)
        # pretend the user has entered something
        editor = editors.FloatEditor(parent=None, **self.editable_kwargs)
        editor.set_field_attributes(prefix='prefix ', suffix=' suffix', editable=True, **field_attributes)
        spinbox = editor.findChild(QtWidgets.QWidget, 'spinbox')
        spinbox.setValue( 0.0 )
        self.assertTrue( editor.get_value() != None )
        self.assertEqual(spinbox.validate(q_string('prefix 0 suffix'), 1)[0], QtGui.QValidator.State.Acceptable)
        self.assertEqual(spinbox.validate(q_string('prefix  suffix'), 1)[0], QtGui.QValidator.State.Acceptable)
        # verify if the calculator button is turned off
        editor = editors.FloatEditor(
            parent=None, calculator=False, **self.editable_kwargs
        )
        editor.set_field_attributes( editable=True, **field_attributes )
        editor.set_value( 3.14 )
        self.grab_widget( editor, 'no_calculator' )
        self.assertTrue( editor.calculatorButton.isHidden() )
        self.assert_valid_editor( editor, 3.14 )

    def test_IntegerEditor(self):
        editor = editors.IntegerEditor(parent=None, editable=True)
        self.assert_vertical_size( editor )
        self.assertEqual( editor.get_value(), ValueLoading )
        editor.set_value( 0 )
        self.assertEqual( editor.get_value(), 0 )
        editor.set_value( 3 )
        self.grab_default_states( editor )
        self.assertEqual( editor.get_value(), 3 )
        editor.set_value( None )
        # pretend the user changed the value
        spinbox = editor.findChild(QtWidgets.QWidget, 'spin_box')
        spinbox.setValue( 0 )
        self.assertEqual( editor.get_value(), 0 )
        editor.set_value( None )
        self.assertEqual( editor.get_value(), None )
        # turn off the calculator
        editor = editors.IntegerEditor(parent=None,
                                            calculator=False)
        editor.set_field_attributes( editable=True )
        editor.set_value( 3 )
        self.grab_widget( editor, 'no_calculator' )
        self.assertTrue( editor.calculatorButton.isHidden() )
        self.assert_valid_editor( editor, 3 )

    def test_NoteEditor(self):
        editor = editors.NoteEditor(parent=None)
        editor.set_value('A person with this name already exists')
        self.grab_widget( editor )
        self.grab_default_states( editor )
        self.assert_valid_editor( editor, 'A person with this name already exists' )

    def test_LabelEditor(self):
        editor = editors.LabelEditor(parent=None)
        editor.set_value('Dynamic label')
        self.grab_default_states( editor )

    def test_LanguageEditor(self):
        editor = editors.LanguageEditor(parent=None)
        self.assert_vertical_size( editor )
        self.assertEqual( editor.get_value(), ValueLoading )
        editor.set_value( 'en_US' )
        self.grab_default_states( editor )
        self.assertEqual( editor.get_value(), 'en_US' )
        self.assert_valid_editor( editor, 'en_US' )

    def test_Many2OneEditor(self):
        editor = editors.Many2OneEditor(parent=None, **self.editable_kwargs)
        self.assert_vertical_size( editor )
        self.grab_default_states( editor )
        self.assert_valid_editor(editor, initial_naming_context._bind_object(3))

    def test_RichTextEditor(self):
        editor = editors.RichTextEditor(parent=None)
        self.assertEqual( editor.get_value(), ValueLoading )
        editor.set_value( u'<h1>Rich Text Editor</h1>' )
        self.grab_default_states( editor )
        self.assertTrue( u'Rich Text Editor' in editor.get_value() )
        self.assert_valid_editor( editor, u'<h1>Rich Text Editor</h1>' )

    def test_TextEditEditor(self):
        editor = editors.TextEditEditor(parent=None, editable=True)
        self.assertEqual( editor.get_value(), ValueLoading )
        editor.set_value( 'Plain text' )
        self.grab_default_states( editor )
        self.assertEqual( editor.get_value(), 'Plain text' )
        self.assert_valid_editor( editor, 'Plain text' )

    def test_VirtualAddressEditor(self):
        editor = editors.VirtualAddressEditor(parent=None)
        self.assert_vertical_size( editor )
        self.assertEqual( editor.get_value(), ValueLoading )
        editor.set_value( ('im','test') )
        self.grab_default_states( editor )
        self.assertEqual( editor.get_value(),  ('im','test') )
        self.assert_valid_editor( editor, ('im','test') )

    def test_MonthsEditor(self):
        editor = editors.MonthsEditor(parent=None)
        self.assert_vertical_size( editor )
        self.assertEqual(editor.get_value(), ValueLoading)
        editor.set_value(12)
        self.grab_default_states( editor )
        self.assertEqual(editor.get_value(),  12)
        self.assert_valid_editor( editor, 12 )


class FormTest(
    RunningThreadCase,
    GrabMixinCase, QueryQStandardItemModelMixinCase, ExampleModelMixinCase
    ):

    images_path = static_images_path
    model_context_name = ('form_test_model_context',)

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.thread.post(cls.setup_sample_model)
        cls.thread.post(cls.load_example_data)
        cls.process()

    @classmethod
    def tearDownClass(cls):
        cls.thread.post(cls.tear_down_sample_model)
        cls.process()
        super().tearDownClass()

    def setUp(self):
        super().setUp()
        self.app_admin = ApplicationAdmin()
        self.person_admin = self.app_admin.get_related_admin(Person)
        self.admin_route = self.person_admin.get_admin_route()
        self.person_model = CollectionProxy(self.admin_route)
        self.thread.post(self.setup_proxy)
        self.person_model.set_value(self.model_context_name)
        list(self.person_model.add_columns(
            [fn for fn,fa in self.person_admin.get_fields()]
        ))
        self._load_data(self.person_model)
        self.qt_parent = QtCore.QObject()
        delegate = DelegateManager(self.qt_parent)
        widget_mapper = QtWidgets.QDataWidgetMapper(self.qt_parent)
        widget_mapper.setModel( self.person_model )
        widget_mapper.setItemDelegate(delegate)
        fields = dict((f, {
            'hide_title':fa.get('hide_title', False),
            'verbose_name':str(fa['name']),
            }) for f, fa in self.person_admin.get_fields())
        self.widgets = FormEditors(self.qt_parent, fields)
        self.person_entity = Person
        self.gui_context = GuiContext()
        
    def _get_serialized_form_display_data(self, form_display):
        serialized_form_display = form_display._to_bytes()
        form_data = json.loads(serialized_form_display)
        self.assertIsInstance(form_data, list)
        self.assertEqual(len(form_data), 2)
        self.assertEqual(form_data[0], form_display.__class__.__name__)
        self.assertIsInstance(form_data[1], dict)
        return form_data[1]
        
    def test_form(self):
        form_data = self._get_serialized_form_display_data(self.person_admin.form_display)
        self.grab_widget(self.person_admin.form_display.render(self.widgets, form_data))
        form = forms.Form( ['first_name', 'last_name',
                            'birthdate', 'passport_number',
                            'picture', forms.Break(),
                             forms.Label('End')] )
        self.assertTrue( str( form ) )

    def test_tab_form(self):
        form = forms.TabForm([('First tab', ['first_name', 'last_name']),
                              ('Second tab', ['birthdate', 'passport_number'])])
        form_data = self._get_serialized_form_display_data(form)
        self.grab_widget(form.render(self.widgets, form_data))
        form.add_tab_at_index( 'Main', forms.Form(['picture']), 0 )
        self.assertTrue( form.get_tab( 'Second tab' ) )
        self.assertTrue( str( form ) )

    def test_group_box_form(self):
        form = forms.GroupBoxForm('Person', ['first_name', 'last_name'])
        form_data = self._get_serialized_form_display_data(form)
        self.grab_widget(forms.GroupBoxForm.render(self.widgets, form_data))

    def test_grid_form(self):
        form = forms.GridForm([['first_name',          'last_name'],
                               ['birthdate',           'passport_number'],
                               [forms.ColumnSpan('picture', 2)              ]
                               ])
        form_data = self._get_serialized_form_display_data(form)
        self.grab_widget(forms.GridForm.render(self.widgets, form_data))
        self.assertTrue( str( form ) )
        form.append_row( ['personal_title', 'suffix'] )
        form.append_column( [ forms.Label( str(i) ) for i in range(4) ] )

    def test_vbox_form(self):
        form = forms.VBoxForm([['first_name', 'last_name'], ['birthdate', 'passport_number']])
        form_data = self._get_serialized_form_display_data(form)
        self.grab_widget(forms.VBoxForm.render(self.widgets, form_data))
        self.assertTrue( str( form ) )

    def test_hbox_form(self):
        form = forms.HBoxForm([['first_name', 'last_name'], ['birthdate', 'passport_number']])
        form_data = self._get_serialized_form_display_data(form)
        self.grab_widget(forms.HBoxForm.render(self.widgets, form_data))
        self.assertTrue( str( form ) )

    def test_inherited_form(self):
        person_admin = InheritedAdmin(self.app_admin, self.person_entity)
        person = self.person_entity()
        open_form_view = OpenFormView(person, person_admin)
        self.grab_widget(
            open_form_view.render(self.gui_context, open_form_view._to_dict())
        )

class DelegateCase(unittest.TestCase, GrabMixinCase):
    """Test the basic functionallity of the delegates :
  - createEditor
  - setEditorData
  - setModelData
  """

    def setUp(self):
        super(DelegateCase, self).setUp()
        self.editable_kwargs = dict(editable=True, action_routes=[])
        self.non_editable_kwargs = dict(editable=False, action_routes=[])
        self.option = QtWidgets.QStyleOptionViewItem()
        # set version to 5 to indicate the widget will appear on a
        # a form view and not on a table view, so it should not
        # set its background
        self.option.version = 5
        self.locale = QtCore.QLocale()

    def grab_delegate(self, delegate, value, suffix='editable', field_attributes={}):

        model = QtGui.QStandardItemModel(1, 1)
        field_action_model_context = FieldActionModelContext(
            app_admin.get_related_admin(Person)
        )
        field_action_model_context.value = value
        field_action_model_context.field_attributes = field_attributes

        item = delegate.get_standard_item(
            self.locale, field_action_model_context
        )
        # make sure a DisplayRole is available in the item, the standard
        # model otherwise returns the EditRole as a DisplayRole
        item.setData(item.data(PreviewRole), Qt.ItemDataRole.DisplayRole)
        model.setItem(0, 0, item)
        index = model.index(0, 0, QtCore.QModelIndex())

        option = QtWidgets.QStyleOptionViewItem()

        if suffix == 'editable':
            self.assertTrue(delegate.sizeHint(option, index).height()>1)

        tableview = TableWidget()
        tableview.setModel(model)
        tableview.setItemDelegate(delegate)

        test_case_name = sys._getframe(1).f_code.co_name[5:]

        for state_name, state in zip(('selected', 'unselected'),
                                     (QtWidgets.QStyle.StateFlag.State_Selected,
                                      QtWidgets.QStyle.StateFlag.State_None)):
            tableview.adjustSize()

            if state == QtWidgets.QStyle.StateFlag.State_Selected:
                tableview.selectionModel().select(index, QtCore.QItemSelectionModel.SelectionFlag.Select)
            else:
                tableview.selectionModel().select(index, QtCore.QItemSelectionModel.SelectionFlag.Clear)

            cell_size = tableview.visualRect(index).size()

            headers_size = QtCore.QSize(tableview.verticalHeader().width(),
                                        tableview.horizontalHeader().height())

            tableview.setHorizontalScrollBarPolicy( Qt.ScrollBarPolicy.ScrollBarAlwaysOff )
            tableview.setVerticalScrollBarPolicy( Qt.ScrollBarPolicy.ScrollBarAlwaysOff )

            tableview.resize(cell_size + headers_size)

            # TODO checks if path exists
            delegate_images_path = os.path.join(static_images_path, 'delegates')
            if not os.path.exists(delegate_images_path):
                os.makedirs(delegate_images_path)
            pixmap = QtWidgets.QWidget.grab(tableview)
            pixmap.save(os.path.join(delegate_images_path, '%s_%s_%s.png'%(test_case_name, state_name, suffix)),
                        'PNG')

    def test_plaintextdelegate(self):
        delegate = delegates.PlainTextDelegate(
            parent=None, length=30, **self.editable_kwargs
        )
        editor = delegate.createEditor(None, self.option, None)
        self.assertEqual(editor.findChild(QtWidgets.QLineEdit).maxLength(), 30)
        self.assertTrue(isinstance(editor, editors.TextLineEditor))
        self.grab_delegate(delegate, 'Plain Text')
        delegate = delegates.PlainTextDelegate(
            parent=None, length=20, **self.non_editable_kwargs
        )
        editor = delegate.createEditor(None, self.option, None)
        self.assertTrue(isinstance(editor, editors.TextLineEditor))
        self.grab_delegate(delegate, 'Plain Text', 'disabled')
        small_text_delegate = delegates.PlainTextDelegate( length = 3 )
        wide_text_delegate = delegates.PlainTextDelegate( length = 30 )
        small_size = small_text_delegate.sizeHint( None, 0 ).width()
        wide_size = wide_text_delegate.sizeHint( None, 0 ).width()
        self.assertTrue( small_size < wide_size )

    def test_texteditdelegate(self):
        delegate = delegates.TextEditDelegate(parent=None, **self.editable_kwargs)
        editor = delegate.createEditor(None, self.option, None)
        self.assertTrue(isinstance(editor, QtWidgets.QTextEdit))
        self.grab_delegate(delegate, 'Plain Text')
        delegate = delegates.TextEditDelegate(parent=None, **self.non_editable_kwargs)
        editor = delegate.createEditor(None, self.option, None)
        self.assertTrue(isinstance(editor, QtWidgets.QTextEdit))
        self.grab_delegate(delegate, 'Plain Text', 'disabled')

    def test_richtextdelegate(self):
        delegate = delegates.RichTextDelegate(parent=None, **self.editable_kwargs)
        editor = delegate.createEditor(None, self.option, None)
        self.assertTrue(isinstance(editor, editors.RichTextEditor))
        self.grab_delegate(delegate, '<b>Rich Text</b>')
        delegate = delegates.RichTextDelegate(parent=None, **self.non_editable_kwargs)
        editor = delegate.createEditor(None, self.option, None)
        self.assertTrue(isinstance(editor, editors.RichTextEditor))
        self.grab_delegate(delegate, '<b>Rich Text</b>', 'disabled')

    def test_booldelegate(self):
        delegate = delegates.BoolDelegate(parent=None, **self.editable_kwargs)
        editor = delegate.createEditor(None, self.option, None)
        self.assertTrue(isinstance(editor, editors.BoolEditor))
        self.grab_delegate(delegate, True)
        delegate = delegates.BoolDelegate(parent=None, **self.non_editable_kwargs)
        editor = delegate.createEditor(None, self.option, None)
        self.assertTrue(isinstance(editor, editors.BoolEditor))
        self.grab_delegate(delegate, True, 'disabled')

    def test_datedelegate(self):
        delegate = delegates.DateDelegate(parent=None, **self.editable_kwargs)
        editor = delegate.createEditor(None, self.option, None)
        self.assertTrue(isinstance(editor, editors.DateEditor))
        today = datetime.date.today()
        self.grab_delegate(delegate, today)
        delegate = delegates.DateDelegate(parent=None, **self.non_editable_kwargs)
        editor = delegate.createEditor(None, self.option, None)
        self.assertTrue(isinstance(editor, editors.DateEditor))
        self.grab_delegate(delegate, today, 'disabled')
        field_action_model_context = FieldActionModelContext(
            app_admin.get_related_admin(Person)
        )
        field_action_model_context.value = today
        field_action_model_context.field_attributes = {}
        item = delegate.get_standard_item(self.locale, field_action_model_context)
        self.assertTrue(variant_to_py(item.data(PreviewRole)))

    def test_datetimedelegate(self):
        delegate = delegates.DateTimeDelegate(parent=None, **self.editable_kwargs)
        editor = delegate.createEditor(None, self.option, None)
        self.assertTrue(isinstance(editor, editors.DateTimeEditor))
        DateTime = datetime.datetime.now()
        self.grab_delegate(delegate, DateTime)
        delegate = delegates.DateTimeDelegate(parent=None, **self.non_editable_kwargs)
        editor = delegate.createEditor(None, self.option, None)
        self.assertTrue(isinstance(editor, editors.DateTimeEditor))
        self.grab_delegate(delegate, DateTime, 'disabled')

    def test_localfileDelegate(self):
        delegate = delegates.LocalFileDelegate(parent=None, **self.editable_kwargs)
        self.grab_delegate(delegate, '/home/lancelot/quests.txt')
        delegate = delegates.LocalFileDelegate(parent=None, **self.non_editable_kwargs)
        self.grab_delegate(delegate, '/home/lancelot/quests.txt', 'disabled')

    def test_labeldelegate(self):
        delegate = delegates.LabelDelegate(parent=None, **self.editable_kwargs)
        self.grab_delegate(delegate, 'dynamic label')
        delegate = delegates.LabelDelegate(parent=None, **self.non_editable_kwargs)
        self.grab_delegate(delegate, 'dynamic label', 'disabled')

    def test_notedelegate(self):
        delegate = delegates.NoteDelegate(parent=None)
        self.grab_delegate(delegate, 'important note')
        delegate = delegates.NoteDelegate(parent=None, editable=False)
        self.grab_delegate(delegate, 'important note', 'disabled')

    def test_many2onedelegate(self):
        delegate = delegates.Many2OneDelegate(parent=None, admin=object())
        self.grab_delegate(delegate, None)
        delegate = delegates.Many2OneDelegate(parent=None, editable=False, admin=object())
        self.grab_delegate(delegate, None, 'disabled')

    def test_one2manydelegate(self):
        delegate = delegates.One2ManyDelegate(parent=None, admin=object())
        self.grab_delegate(delegate, [], field_attributes={'admin': admin})
        delegate = delegates.One2ManyDelegate(parent=None, editable=False, admin=object())
        self.grab_delegate(delegate, [], field_attributes={'admin': admin})

    def test_integerdelegate(self):
        delegate = delegates.IntegerDelegate(parent=None, editable=True)
        editor = delegate.createEditor(None, self.option, None)
        self.assertTrue(isinstance(editor, editors.IntegerEditor))
        self.grab_delegate(delegate, 3)
        delegate = delegates.IntegerDelegate(parent=None, editable=False)
        editor = delegate.createEditor(None, self.option, None)
        self.assertTrue(isinstance(editor, editors.IntegerEditor))
        self.grab_delegate(delegate, 0, 'disabled')

    def test_floatdelegate(self):
        delegate = delegates.FloatDelegate(parent=None, suffix='euro', **self.editable_kwargs)
        editor = delegate.createEditor(None, self.option, None)
        self.assertTrue(isinstance(editor, editors.FloatEditor))
        self.grab_delegate(delegate, 3.145)
        delegate = delegates.FloatDelegate(parent=None, prefix='prefix', **self.non_editable_kwargs)
        editor = delegate.createEditor(None, self.option, None)
        self.assertTrue(isinstance(editor, editors.FloatEditor))
        self.grab_delegate(delegate, 0, 'disabled')

    def test_filedelegate(self):
        delegate = delegates.FileDelegate(parent=None, **self.editable_kwargs)
        file = StoredFile(None, 'agreement.pdf')
        editor = delegate.createEditor(None, self.option, None)
        self.assertTrue(isinstance(editor, editors.FileEditor))
        self.grab_delegate(delegate, file)
        delegate = delegates.FileDelegate(parent=None, **self.non_editable_kwargs)
        self.grab_delegate(delegate, file, 'disabled')

    def test_colordelegate(self):
        delegate = delegates.ColorDelegate(parent=None, **self.editable_kwargs)
        editor = delegate.createEditor(None, self.option, None)
        self.assertTrue(isinstance(editor, editors.ColorEditor))
        color = '#ffff00'
        self.grab_delegate(delegate, color)
        delegate = delegates.ColorDelegate(parent=None, **self.non_editable_kwargs)
        editor = delegate.createEditor(None, self.option, None)
        self.assertTrue(isinstance(editor, editors.ColorEditor))
        self.grab_delegate(delegate, color, 'disabled')

    def test_comboboxdelegate(self):
        CHOICES = (('1','A'), ('2','B'), ('3','C'))
        delegate = delegates.ComboBoxDelegate(parent=None,
                                                   choices=CHOICES,
                                                   **self.editable_kwargs)
        editor = delegate.createEditor(None, self.option, None)
        self.assertTrue(isinstance(editor, editors.ChoicesEditor))
        self.grab_delegate(delegate, 1)
        delegate = delegates.ComboBoxDelegate(parent=None,
                                                   choices=CHOICES,
                                                   editable=False)
        self.grab_delegate(delegate, 1, 'disabled')
        field_action_model_context = FieldActionModelContext(
            app_admin.get_related_admin(Person)
        )
        field_action_model_context.value = '2'
        field_action_model_context.field_attributes = {'choices':CHOICES}
        item = delegate.get_standard_item(self.locale, field_action_model_context)
        self.assertEqual(variant_to_py(item.data(PreviewRole)), 'B')

    def test_virtualaddressdelegate(self):
        delegate = delegates.VirtualAddressDelegate(parent=None,
                                                         **self.editable_kwargs)
        editor = delegate.createEditor(None, self.option, None)
        self.assertTrue(isinstance(editor, editors.VirtualAddressEditor))
        self.grab_delegate(delegate, ('email', 'project-camelot@conceptive.be'))
        delegate = delegates.VirtualAddressDelegate(parent=None, editable=False)
        self.grab_delegate(delegate, ('email', 'project-camelot@conceptive.be'), 'disabled')

    def test_monthsdelegate(self):
        delegate = delegates.MonthsDelegate(parent=None, **self.editable_kwargs)
        editor = delegate.createEditor(None, self.option, None)
        self.assertTrue(isinstance(editor, editors.MonthsEditor))
        self.grab_delegate(delegate, 12)
        delegate = delegates.MonthsDelegate(parent=None, **self.non_editable_kwargs)
        self.grab_delegate(delegate, 12, 'disabled')


class ControlsTest(
    RunningThreadCase,
    QueryQStandardItemModelMixinCase, ExampleModelMixinCase, GrabMixinCase
    ):
    """Test some basic controls"""

    images_path = static_images_path
    model_context_name = ('controls_test_model_context',)

    @classmethod
    def setUpClass(cls):
        super(ControlsTest, cls).setUpClass()
        cls.thread.post(cls.setup_sample_model)
        cls.app_admin = MyApplicationAdmin()
        cls.process()

    def setUp(self):
        self.thread.post(self.setup_proxy)
        self.process()
        self.admin = self.app_admin.get_entity_admin(Person)
        self.admin_route = admin.get_admin_route()
        self.gui_context = ApplicationActionGuiContext()
        self.gui_context.admin_route = self.admin_route

    def tearDown(self):
        super().tearDown()

    def test_small_column( self ):
        #create a table view for an Admin interface with small columns

        class SmallColumnsAdmin( Person.Admin ):
            list_display = ['first_name', 'suffix']

        self.thread.post(self.setup_proxy, args=(SmallColumnsAdmin,))
        admin = SmallColumnsAdmin( self.app_admin, Person )
        widget = TableWidget()
        model = CollectionProxy(admin.get_admin_route())
        widget.setModel(model)
        model.set_value(self.model_context_name)
        list(model.add_columns(admin.get_columns()))
        model.timeout_slot()
        self.process()
        self.grab_widget( widget )
        model.timeout_slot()
        self.process()
        widget.horizontalHeader()

        first_name_width = self._header_data(0, Qt.Orientation.Horizontal, Qt.ItemDataRole.SizeHintRole, model).width()
        suffix_width = self._header_data(1, Qt.Orientation.Horizontal, Qt.ItemDataRole.SizeHintRole, model).width()

        self.assertTrue(first_name_width > suffix_width)

    def test_column_width( self ):
        #create a table view for an Admin interface with small columns

        class ColumnWidthAdmin( Person.Admin ):
            list_display = ['first_name', 'suffix']
            # begin column width
            field_attributes = { 'first_name':{'column_width':8},
                                 'suffix':{'column_width':8},}
            # end column width

        self.thread.post(self.setup_proxy, args=(ColumnWidthAdmin,))
        admin = ColumnWidthAdmin( self.app_admin, Person )
        widget = TableWidget()
        model = CollectionProxy(admin.get_admin_route())
        widget.setModel(model)
        model.set_value(self.model_context_name)
        list(model.add_columns(admin.get_columns()))
        model.timeout_slot()
        self.process()
        self.grab_widget(widget)
        model.timeout_slot()
        self.process()
        widget.horizontalHeader()

        first_name_width = self._header_data(0, Qt.Orientation.Horizontal, Qt.ItemDataRole.SizeHintRole, model).width()
        suffix_width = self._header_data(1, Qt.Orientation.Horizontal, Qt.ItemDataRole.SizeHintRole, model).width()

        self.assertEqual(first_name_width, suffix_width)

    def test_busy_widget(self):
        busy_widget = BusyWidget()
        busy_widget.set_busy( True )
        self.grab_widget( busy_widget )

    def test_desktop_workspace(self):
        #workspace = DesktopWorkspace(self.gui_context.admin_route, None)
        #self.grab_widget(workspace)
        pass # obsolete?

    def test_progress_dialog( self ):
        dialog = ProgressDialog(None)
        dialog.title = 'Import cover images'
        self.grab_widget(dialog)
        dialog.add_detail('toy_story.png imported')
        dialog.add_detail('matrix.png imported')
        self.grab_widget(dialog, suffix='detail')

    def test_user_exception(self):
        exc = None
        try:
            #begin user_exception

            raise UserException( text = "Could not burn movie to non empty DVD",
                                 resolution = "Insert an empty DVD and retry" )
            #end user_exception
        except Exception as e:
            exc = e

        exc_info = register_exception(logger, 'unit test', exc)
        dialog = ExceptionDialog( exc_info )
        self.grab_widget( dialog )


class SnippetsTest(RunningThreadCase,
    ExampleModelMixinCase, QueryQStandardItemModelMixinCase, GrabMixinCase
    ):

    images_path = static_images_path
    model_context_name = ('snippets_test_model_context',)

    @classmethod
    def setUpClass(cls):
        super(SnippetsTest, cls).setUpClass()
        cls.thread.post(cls.setup_sample_model)
        cls.thread.post(cls.load_example_data)
        cls.thread.post(cls.setup_proxy)
        cls.app_admin = ApplicationAdmin()
        cls.gui_context = GuiContext()
        cls.process()

    def test_fields_with_actions(self):
        coordinate = Coordinate()
        admin = Coordinate.Admin( self.app_admin, Coordinate )
        open_form_view = OpenFormView(coordinate, admin)
        form = open_form_view.render(self.gui_context, open_form_view._to_dict())
        self.grab_widget(form)

    def test_fields_with_tooltips(self):
        coordinate = Coordinate()
        admin = Coordinate.Admin( self.app_admin, Coordinate )
        open_form_view = OpenFormView(coordinate, admin)
        form = open_form_view.render(self.gui_context, open_form_view._to_dict())
        self.grab_widget(form)

    def test_background_color(self):
        person_admin = BackgroundColorAdmin(self.app_admin, Person)
        person_columns = person_admin.get_columns()
        editor = One2ManyEditor(
            admin_route=person_admin.get_admin_route(),
            columns=person_columns,
            action_routes=[],
        )
        editor.set_value(self.model_context_name)
        self.process()
        editor_model = editor.get_model()
        self.assertTrue(editor_model)
        self._load_data(editor_model)
        self.grab_widget(editor)
