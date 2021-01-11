# -*- coding: utf-8 -*-

import six

import datetime
import logging
import os
import sys
import unittest

from camelot.admin.action.application_action import ApplicationActionGuiContext
from camelot.admin.action.list_filter import SearchFilter
from camelot.model.party import Person

from camelot.admin.action import GuiContext
from camelot.admin.application_admin import ApplicationAdmin
from camelot.core.constants import camelot_minfloat, camelot_maxfloat
from camelot.core.item_model import FieldAttributesRole, PreviewRole
from camelot.core.orm import entities
from camelot.core.qt import Qt, QtGui, QtWidgets, QtCore, variant_to_py, q_string
from camelot.core.utils import ugettext_lazy as _
from camelot.core.files.storage import StoredFile, Storage
from camelot.test import GrabMixinCase, RunningThreadCase
from camelot.view import action_steps
from camelot.view.action_steps import OpenFormView
from camelot.view.art import ColorScheme
from camelot.view.controls.tableview import TableView, TableWidget
from camelot.view.controls import delegates
from camelot.view.controls.formview import FormEditors
from camelot.view.controls import editors
from camelot.view.controls.editors.datetimeeditor import TimeValidator
from camelot.view.controls.editors.one2manyeditor import One2ManyEditor
from camelot.view.mainwindowproxy import MainWindowProxy
from camelot.view import forms
from camelot.view.proxy import ValueLoading
from camelot.view.proxy.collection_proxy import CollectionProxy
from camelot.view.controls.delegates import DelegateManager
from camelot.view.controls.progress_dialog import ProgressDialog

from .import app_admin

from .test_item_model import A, QueryQStandardItemModelMixinCase
from .test_model import ExampleModelMixinCase

from .snippet.background_color import Admin as BackgroundColorAdmin
from .snippet.fields_with_actions import Coordinate
from .snippet.form.custom_layout import Admin as CustomLayoutAdmin
from .snippet.form.inherited_form import InheritedAdmin

from camelot_example.model import Movie
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

    def assert_valid_editor( self, editor, value ):
        """Test the basic functions of an editor that are needed to integrate
        well with Camelot and Qt
        """
        #
        # The editor should remember its when its value is ValueLoading
        #
        editor.set_value( ValueLoading )
        self.assertEqual( editor.get_value(), ValueLoading )
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
                          QtWidgets.QSizePolicy.Fixed )

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
        editor = editors.TextLineEditor(parent=None, length=10)
        self.assert_vertical_size( editor )
        self.assertEqual( editor.get_value(), ValueLoading )
        editor.set_value( u'za coś tam' )
        self.grab_default_states( editor )
        self.assertEqual( editor.get_value(), u'za coś tam' )
        editor.set_value( ValueLoading )
        self.assertEqual( editor.get_value(), ValueLoading )
        editor = editors.TextLineEditor(parent=None, length=10)
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
        editor = editors.ChoicesEditor(parent=None, editable=True)
        self.assert_vertical_size( editor )
        choices1 = [(1,u'A'), (2,u'B'), (3,u'C')]
        editor.set_choices( choices1 )
        self.assertEqual( editor.get_value(), ValueLoading )
        editor.set_value( 2 )
        # None equals space for qml compatibility
        self.assertEqual(editor.get_choices(), choices1 + [(None,' ')] )
        self.grab_default_states( editor )
        self.assertEqual( editor.get_value(), 2 )
        # None is not in the list of choices, but we should still be able
        # to set it's value to it
        editor.set_value( None )
        self.assertEqual( editor.get_value(), None )
        # now change the choices, while the current value is not in the
        # list of new choices
        editor.set_value( 2 )
        choices2 = [(4,u'D'), (5,u'E'), (6,u'F')]
        editor.set_choices( choices2 )
        self.assertEqual(editor.get_choices(), choices2 + [(None,' '), (2,u'B')])
        editor.set_value(4)
        self.assertEqual(editor.get_choices(), choices2 + [(None,' ')])
        # set a value that is not in the list, the value should be
        # accepted, to prevent damage to the actual data
        editor.set_value(33)
        self.assertEqual(editor.get_value(), 33)
        number_of_choices = len(editor.get_choices())
        # set the value back to valid one, the invalid one should be no longer
        # in the list of choices
        editor.set_value(4)
        self.assertEqual(number_of_choices-1, len(editor.get_choices()))
        # try strings as keys
        editor = editors.ChoicesEditor(parent=None, editable=True)
        editor.set_choices( [('a',u'A'), ('b',u'B'), ('c',u'C')] )
        editor.set_value( 'c' )
        self.assertEqual( editor.get_value(), 'c' )
        self.assert_valid_editor( editor, 'c' )

    def test_FileEditor(self):
        editor = editors.FileEditor(parent=None, editable=True)
        self.assert_vertical_size( editor )
        self.assertEqual( editor.get_value(), ValueLoading )
        self.grab_default_states( editor )
        self.assert_valid_editor( editor, StoredFile( storage, 'test.txt') )

    def test_DateTimeEditor(self):
        validator = TimeValidator()
        self.assertEqual(validator._validate('22', 0), (QtGui.QValidator.Intermediate, '22', 0))
        self.assertEqual(validator._validate('59', 0), (QtGui.QValidator.Intermediate, '59', 0))
        self.assertEqual(validator._validate('22:', 0), (QtGui.QValidator.Intermediate,'22:',  0))
        self.assertEqual(validator._validate(':17', 0), (QtGui.QValidator.Intermediate, ':17', 0))
        self.assertEqual(validator._validate('22:7', 0), (QtGui.QValidator.Acceptable, '22:7', 0))
        self.assertEqual(validator._validate('22:17', 0), (QtGui.QValidator.Acceptable, '22:17', 0))
        self.assertEqual(validator._validate('1:17', 0), (QtGui.QValidator.Acceptable, '1:17', 0))
        self.assertEqual(validator._validate('22:7:', 0), (QtGui.QValidator.Invalid, '22:7:', 0))
        self.assertEqual(validator._validate('61', 0), (QtGui.QValidator.Invalid, '61', 0))
        self.assertEqual(validator._validate('611', 0), (QtGui.QValidator.Invalid, '611', 0))
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
        item = delegate.get_standard_item(QtCore.QLocale(), 3, {})
        field_attributes = item.data(FieldAttributesRole)
        
        editor = editors.FloatEditor(parent=None)
        editor.set_field_attributes(prefix='prefix', editable=True, **field_attributes)
        self.assert_vertical_size( editor )
        self.assertEqual( editor.get_value(), ValueLoading )
        editor.set_value( 0.0 )
        self.assertEqual( editor.get_value(), 0.0 )
        editor.set_value( 3.14 )
        self.grab_default_states( editor )
        self.assertEqual( editor.get_value(), 3.14 )
        editor = editors.FloatEditor(parent=None, option=self.option)
        editor.set_field_attributes(suffix=' suffix', editable=True, **field_attributes)
        self.assertEqual( editor.get_value(), ValueLoading )
        editor.set_value( 0.0 )
        self.assertEqual( editor.get_value(), 0.0 )
        editor.set_value( 3.14 )
        self.assertEqual( editor.get_value(), 3.14 )
        editor.set_value( 5.45 )
        editor.set_value( None )
        self.assertEqual( editor.get_value(), None )
        up = QtGui.QKeyEvent(QtCore.QEvent.KeyPress, Qt.Key_Up, Qt.NoModifier)
        spinbox = editor.findChild(QtWidgets.QWidget, 'spinbox')
        self.assertEqual(spinbox.minimum(), camelot_minfloat-1)
        self.assertEqual(spinbox.maximum(), camelot_maxfloat)
        spinbox.keyPressEvent(up)
        self.assertEqual(editor.get_value(), 0.0)
        # pretend the user has entered something
        editor = editors.FloatEditor(parent=None)
        editor.set_field_attributes(prefix='prefix ', suffix=' suffix', editable=True, **field_attributes)
        spinbox = editor.findChild(QtWidgets.QWidget, 'spinbox')
        spinbox.setValue( 0.0 )
        self.assertTrue( editor.get_value() != None )
        self.assertEqual(spinbox.validate(q_string('prefix 0 suffix'), 1)[0], QtGui.QValidator.Acceptable)
        self.assertEqual(spinbox.validate(q_string('prefix  suffix'), 1)[0], QtGui.QValidator.Acceptable)
        # verify if the calculator button is turned off
        editor = editors.FloatEditor(parent=None,
                                          calculator=False)
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
        editor = editors.Many2OneEditor(parent=None)
        self.assert_vertical_size( editor )
        self.grab_default_states( editor )
        self.assert_valid_editor( editor, lambda:object )

    def test_RichTextEditor(self):
        editor = editors.RichTextEditor(parent=None)
        self.assertEqual( editor.get_value(), ValueLoading )
        editor.set_value( u'<h1>Rich Text Editor</h1>' )
        self.grab_default_states( editor )
        self.assertTrue( u'Rich Text Editor' in editor.get_value() )
        self.assert_valid_editor( editor, u'<h1>Rich Text Editor</h1>' )

    def test_TimeEditor(self):
        editor = editors.TimeEditor(parent=None, editable=True)
        self.assert_vertical_size( editor )
        self.assertEqual( editor.get_value(), ValueLoading )
        editor.set_value( datetime.time(21, 5, 0) )
        self.grab_default_states( editor )
        self.assertEqual( editor.get_value(), datetime.time(21, 5, 0) )
        self.assert_valid_editor( editor, datetime.time(21, 5, 0) )

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


class FormTest(unittest.TestCase, GrabMixinCase):

    images_path = static_images_path

    def setUp(self):
        self.entities = [e for e in entities]
        self.app_admin = ApplicationAdmin()
        self.movie_admin = self.app_admin.get_related_admin( Movie )
        self.admin_route = self.movie_admin.get_admin_route()
        self.movie_model = CollectionProxy(self.admin_route)
        self.movie_model.set_value(self.movie_admin.get_proxy(self.movie_admin.get_query()))
        list(self.movie_model.add_columns(
            [fn for fn,fa in self.movie_admin.get_fields()]
        ))

        delegate = DelegateManager(self.movie_admin.get_fields())
        self.qt_parent = QtCore.QObject()
        widget_mapper = QtWidgets.QDataWidgetMapper(self.qt_parent)
        widget_mapper.setModel( self.movie_model )
        widget_mapper.setItemDelegate(delegate)
        self.widgets = FormEditors(
            self.qt_parent, self.movie_admin.get_fields(), self.movie_admin
        )
        self.person_entity = Person
        self.gui_context = GuiContext()

    def tearDown(self):
        #
        # The global list of entities should remain clean for subsequent tests
        #
        for e in entities:
            if e not in self.entities:
                entities.remove(e)

    def test_form(self):
        self.grab_widget(Movie.Admin.form_display.render(self.widgets))
        form = forms.Form( ['title', 'short_description',
                            'director', 'releasedate'] )
        form.remove_field( 'releasedate' )
        form.replace_field( 'director', 'rating' )
        form.add_field( 'tags' )
        form.add_field( forms.Break() )
        form.add_field( forms.Label('End') )
        self.assertTrue( six.text_type( form ) )

    def test_tab_form(self):
        form = forms.TabForm([('First tab', ['title', 'short_description']),
                              ('Second tab', ['director', 'releasedate'])])
        self.grab_widget(form.render(self.widgets))
        form.add_tab_at_index( 'Main', forms.Form(['rating']), 0 )
        self.assertTrue( form.get_tab( 'Second tab' ) )
        form.replace_field( 'short_description', 'script' )
        form.remove_field( 'director' )
        self.assertTrue( six.text_type( form ) )

    def test_group_box_form(self):
        form = forms.GroupBoxForm('Movie', ['title', 'short_description'])
        self.grab_widget(form.render(self.widgets))

    def test_grid_form(self):
        form = forms.GridForm([['title',                      'short_description'],
                               ['director',                   'releasedate'],
                               [forms.ColumnSpan('rating', 2)              ]
                               ])
        self.grab_widget(form.render(self.widgets))
        self.assertTrue( six.text_type( form ) )
        form.append_row( ['cover', 'script'] )
        form.append_column( [ forms.Label( str(i) ) for i in range(4) ] )

    def test_vbox_form(self):
        form = forms.VBoxForm([['title', 'short_description'], ['director', 'releasedate']])
        self.grab_widget(form.render(self.widgets))
        self.assertTrue( six.text_type( form ) )
        form.replace_field( 'releasedate', 'rating' )

    def test_hbox_form(self):
        form = forms.HBoxForm([['title', 'short_description'], ['director', 'releasedate']])
        self.grab_widget(form.render(self.widgets))
        self.assertTrue( six.text_type( form ) )
        form.replace_field( 'releasedate', 'rating' )

    def test_nested_form(self):
        person_admin = CustomLayoutAdmin(self.app_admin, self.person_entity)
        open_form_view = OpenFormView([self.person_entity()], person_admin)
        self.grab_widget( open_form_view.render(self.gui_context) )

    def test_inherited_form(self):
        person_admin = InheritedAdmin(self.app_admin, self.person_entity)
        open_form_view = OpenFormView([self.person_entity()], person_admin)
        self.grab_widget( open_form_view.render(self.gui_context) )

    def test_custom_layout(self):
        person_admin = CustomLayoutAdmin(self.app_admin, self.person_entity)
        open_form_view = OpenFormView([self.person_entity()], person_admin)
        self.grab_widget( open_form_view.render(self.gui_context) )

class DelegateCase(unittest.TestCase, GrabMixinCase):
    """Test the basic functionallity of the delegates :
  - createEditor
  - setEditorData
  - setModelData
  """

    def setUp(self):
        super(DelegateCase, self).setUp()
        self.kwargs = dict(editable=True)
        self.option = QtWidgets.QStyleOptionViewItem()
        # set version to 5 to indicate the widget will appear on a
        # a form view and not on a table view, so it should not
        # set its background
        self.option.version = 5
        self.locale = QtCore.QLocale()

    def grab_delegate(self, delegate, value, suffix='editable', field_attributes={}):

        model = QtGui.QStandardItemModel(1, 1)
        model.setItem(0, 0, delegate.get_standard_item(self.locale, value, field_attributes))
        index = model.index(0, 0, QtCore.QModelIndex())

        option = QtWidgets.QStyleOptionViewItem()

        if suffix == 'editable':
            self.assertTrue(delegate.sizeHint(option, index).height()>1)

        tableview = TableWidget()
        tableview.setModel(model)
        tableview.setItemDelegate(delegate)

        test_case_name = sys._getframe(1).f_code.co_name[5:]

        for state_name, state in zip(('selected', 'unselected'),
                                     (QtWidgets.QStyle.State_Selected, 
                                      QtWidgets.QStyle.State_None)):
            tableview.adjustSize()

            if state == QtWidgets.QStyle.State_Selected:
                tableview.selectionModel().select(index, QtCore.QItemSelectionModel.Select)
            else:
                tableview.selectionModel().select(index, QtCore.QItemSelectionModel.Clear)

            cell_size = tableview.visualRect(index).size()

            headers_size = QtCore.QSize(tableview.verticalHeader().width(),
                                        tableview.horizontalHeader().height())

            tableview.setHorizontalScrollBarPolicy( Qt.ScrollBarAlwaysOff )
            tableview.setVerticalScrollBarPolicy( Qt.ScrollBarAlwaysOff )

            tableview.resize(cell_size + headers_size)

            # TODO checks if path exists
            delegate_images_path = os.path.join(static_images_path, 'delegates')
            if not os.path.exists(delegate_images_path):
                os.makedirs(delegate_images_path)
            pixmap = QtWidgets.QWidget.grab(tableview)
            pixmap.save(os.path.join(delegate_images_path, '%s_%s_%s.png'%(test_case_name, state_name, suffix)),
                        'PNG')

    def test_plaintextdelegate(self):
        delegate = delegates.PlainTextDelegate(parent=None,
                                                    length=30,
                                                    editable=True)
        editor = delegate.createEditor(None, self.option, None)
        self.assertEqual(editor.findChild(QtWidgets.QLineEdit).maxLength(), 30)
        self.assertTrue(isinstance(editor, editors.TextLineEditor))
        self.grab_delegate(delegate, 'Plain Text')
        delegate = delegates.PlainTextDelegate(parent=None,
                                                    length=20,
                                                    editable=False)
        editor = delegate.createEditor(None, self.option, None)
        self.assertTrue(isinstance(editor, editors.TextLineEditor))
        self.grab_delegate(delegate, 'Plain Text', 'disabled')
        small_text_delegate = delegates.PlainTextDelegate( length = 3 )
        wide_text_delegate = delegates.PlainTextDelegate( length = 30 )
        small_size = small_text_delegate.sizeHint( None, 0 ).width()
        wide_size = wide_text_delegate.sizeHint( None, 0 ).width()
        self.assertTrue( small_size < wide_size )

    def test_texteditdelegate(self):
        delegate = delegates.TextEditDelegate(parent=None, **self.kwargs)
        editor = delegate.createEditor(None, self.option, None)
        self.assertTrue(isinstance(editor, QtWidgets.QTextEdit))
        self.grab_delegate(delegate, 'Plain Text')
        delegate = delegates.TextEditDelegate(parent=None, editable=False)
        editor = delegate.createEditor(None, self.option, None)
        self.assertTrue(isinstance(editor, QtWidgets.QTextEdit))
        self.grab_delegate(delegate, 'Plain Text', 'disabled')

    def test_richtextdelegate(self):
        delegate = delegates.RichTextDelegate(parent=None, **self.kwargs)
        editor = delegate.createEditor(None, self.option, None)
        self.assertTrue(isinstance(editor, editors.RichTextEditor))
        self.grab_delegate(delegate, '<b>Rich Text</b>')
        delegate = delegates.RichTextDelegate(parent=None, editable=False)
        editor = delegate.createEditor(None, self.option, None)
        self.assertTrue(isinstance(editor, editors.RichTextEditor))
        self.grab_delegate(delegate, '<b>Rich Text</b>', 'disabled')

    def test_booldelegate(self):
        delegate = delegates.BoolDelegate(parent=None, **self.kwargs)
        editor = delegate.createEditor(None, self.option, None)
        self.assertTrue(isinstance(editor, editors.BoolEditor))
        self.grab_delegate(delegate, True)
        delegate = delegates.BoolDelegate(parent=None, editable=False)
        editor = delegate.createEditor(None, self.option, None)
        self.assertTrue(isinstance(editor, editors.BoolEditor))
        self.grab_delegate(delegate, True, 'disabled')

    def test_datedelegate(self):
        delegate = delegates.DateDelegate(parent=None, **self.kwargs)
        editor = delegate.createEditor(None, self.option, None)
        self.assertTrue(isinstance(editor, editors.DateEditor))
        today = datetime.date.today()
        self.grab_delegate(delegate, today)
        delegate = delegates.DateDelegate(parent=None, editable=False)
        editor = delegate.createEditor(None, self.option, None)
        self.assertTrue(isinstance(editor, editors.DateEditor))
        self.grab_delegate(delegate, today, 'disabled')
        item = delegate.get_standard_item(self.locale, today, {})
        self.assertTrue(variant_to_py(item.data(PreviewRole)))

    def test_datetimedelegate(self):
        delegate = delegates.DateTimeDelegate(parent=None, **self.kwargs)
        editor = delegate.createEditor(None, self.option, None)
        self.assertTrue(isinstance(editor, editors.DateTimeEditor))
        DateTime = datetime.datetime.now()
        self.grab_delegate(delegate, DateTime)
        delegate = delegates.DateTimeDelegate(parent=None, editable=False)
        editor = delegate.createEditor(None, self.option, None)
        self.assertTrue(isinstance(editor, editors.DateTimeEditor))
        self.grab_delegate(delegate, DateTime, 'disabled')

    def test_localfileDelegate(self):
        delegate = delegates.LocalFileDelegate(parent=None)
        self.grab_delegate(delegate, '/home/lancelot/quests.txt')
        delegate = delegates.LocalFileDelegate(parent=None, editable=False)
        self.grab_delegate(delegate, '/home/lancelot/quests.txt', 'disabled')

    def test_labeldelegate(self):
        delegate = delegates.LabelDelegate(parent=None)
        self.grab_delegate(delegate, 'dynamic label')
        delegate = delegates.LabelDelegate(parent=None, editable=False)
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

    def test_timedelegate(self):
        delegate = delegates.TimeDelegate(parent=None, editable=True)
        editor = delegate.createEditor(None, self.option, None)
        self.assertTrue(isinstance(editor, editors.TimeEditor))
        time = datetime.time(10, 30, 15)
        self.grab_delegate(delegate, time)
        delegate = delegates.TimeDelegate(parent=None, editable=False)
        editor = delegate.createEditor(None, self.option, None)
        self.assertTrue(isinstance(editor, editors.TimeEditor))
        #time = time(10, 30, 15)
        self.grab_delegate(delegate, time, 'disabled')

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
        delegate = delegates.FloatDelegate(parent=None, suffix='euro', editable=True)
        editor = delegate.createEditor(None, self.option, None)
        self.assertTrue(isinstance(editor, editors.FloatEditor))
        self.grab_delegate(delegate, 3.145)
        delegate = delegates.FloatDelegate(parent=None, prefix='prefix', editable=False)
        editor = delegate.createEditor(None, self.option, None)
        self.assertTrue(isinstance(editor, editors.FloatEditor))
        self.grab_delegate(delegate, 0, 'disabled')

    def test_filedelegate(self):
        delegate = delegates.FileDelegate(parent=None)
        file = StoredFile(None, 'agreement.pdf')
        editor = delegate.createEditor(None, self.option, None)
        self.assertTrue(isinstance(editor, editors.FileEditor))
        self.grab_delegate(delegate, file)
        delegate = delegates.FileDelegate(parent=None, editable=False)
        self.grab_delegate(delegate, file, 'disabled')

    def test_colordelegate(self):
        delegate = delegates.ColorDelegate(parent=None, **self.kwargs)
        editor = delegate.createEditor(None, self.option, None)
        self.assertTrue(isinstance(editor, editors.ColorEditor))
        color = [255, 255, 0]
        self.grab_delegate(delegate, color)
        delegate = delegates.ColorDelegate(parent=None, editable=False)
        editor = delegate.createEditor(None, self.option, None)
        self.assertTrue(isinstance(editor, editors.ColorEditor))
        self.grab_delegate(delegate, color, 'disabled')

    def test_comboboxdelegate(self):
        CHOICES = (('1','A'), ('2','B'), ('3','C'))
        delegate = delegates.ComboBoxDelegate(parent=None,
                                                   choices=CHOICES,
                                                   **self.kwargs)
        editor = delegate.createEditor(None, self.option, None)
        self.assertTrue(isinstance(editor, editors.ChoicesEditor))
        self.grab_delegate(delegate, 1)
        delegate = delegates.ComboBoxDelegate(parent=None,
                                                   choices=CHOICES,
                                                   editable=False)
        self.grab_delegate(delegate, 1, 'disabled')
        item = delegate.get_standard_item(self.locale, '2', {'choices':CHOICES})
        self.assertEqual(variant_to_py(item.data(PreviewRole)), 'B')

    def test_virtualaddressdelegate(self):
        delegate = delegates.VirtualAddressDelegate(parent=None,
                                                         **self.kwargs)
        editor = delegate.createEditor(None, self.option, None)
        self.assertTrue(isinstance(editor, editors.VirtualAddressEditor))
        self.grab_delegate(delegate, ('email', 'project-camelot@conceptive.be'))
        delegate = delegates.VirtualAddressDelegate(parent=None, editable=False)
        self.grab_delegate(delegate, ('email', 'project-camelot@conceptive.be'), 'disabled')

    def test_monthsdelegate(self):
        delegate = delegates.MonthsDelegate(parent=None, **self.kwargs)
        editor = delegate.createEditor(None, self.option, None)
        self.assertTrue(isinstance(editor, editors.MonthsEditor))
        self.grab_delegate(delegate, 12)
        delegate = delegates.MonthsDelegate(parent=None, editable=False)
        self.grab_delegate(delegate, 12, 'disabled')


class ControlsTest(
    RunningThreadCase,
    QueryQStandardItemModelMixinCase, ExampleModelMixinCase, GrabMixinCase
    ):
    """Test some basic controls"""

    images_path = static_images_path

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

    def test_table_view(self):
        gui_context = GuiContext()
        widget = TableView(gui_context, self.admin_route)
        self.grab_widget(widget)

    def test_rows_widget(self):
        from camelot.view.controls.tableview import RowsWidget
        from camelot.model.party import City
        city_admin = self.app_admin.get_entity_admin(City)
        table = TableView(self.gui_context, city_admin.get_admin_route())
        table.set_admin()
        RowsWidget(table.gui_context)

    def test_small_column( self ):
        #create a table view for an Admin interface with small columns

        class SmallColumnsAdmin( Person.Admin ):
            list_display = ['first_name', 'suffix']

        admin = SmallColumnsAdmin( self.app_admin, Person )
        widget = TableView(self.gui_context, admin.get_admin_route())
        widget.set_admin()
        model = widget.get_model()
        model.set_value(self.proxy)
        list(model.add_columns((fn for fn, fa in admin.get_columns())))
        model.timeout_slot()
        self.process()
        self.grab_widget( widget )
        model.timeout_slot()
        self.process()
        widget.table.horizontalHeader()

        first_name_width = self._header_data(0, Qt.Horizontal, Qt.SizeHintRole, model).width()
        suffix_width = self._header_data(1, Qt.Horizontal, Qt.SizeHintRole, model).width()

        self.assertTrue(first_name_width > suffix_width)

    def test_column_width( self ):
        #create a table view for an Admin interface with small columns

        class ColumnWidthAdmin( Person.Admin ):
            list_display = ['first_name', 'suffix']
            # begin column width
            field_attributes = { 'first_name':{'column_width':8},
                                 'suffix':{'column_width':8},}
            # end column width

        admin = ColumnWidthAdmin( self.app_admin, Person )
        widget = TableView(self.gui_context, admin.get_admin_route())
        widget.set_admin()
        model = widget.get_model()
        model.set_value(self.proxy)
        list(model.add_columns((fn for fn, fa in admin.get_columns())))
        model.timeout_slot()
        self.process()
        self.grab_widget(widget)
        model = widget.get_model()
        model.timeout_slot()
        self.process()
        widget.table.horizontalHeader()

        first_name_width = self._header_data(0, Qt.Horizontal, Qt.SizeHintRole, model).width()
        suffix_width = self._header_data(1, Qt.Horizontal, Qt.SizeHintRole, model).width()

        self.assertEqual(first_name_width, suffix_width)

    def test_column_group( self ):
        from camelot.admin.table import ColumnGroup
        from camelot.model.party import Person

        class ColumnWidthAdmin( Person.Admin ):
            #begin column group
            list_display = [ ColumnGroup( _('Name'), ['first_name', 'last_name', 'suffix'] ),
                             ColumnGroup( _('Official'), ['birthdate', 'social_security_number', 'passport_number'] ),
                             ]
            #end column group

        admin = ColumnWidthAdmin( self.app_admin, Person )
        widget = TableView(self.gui_context, admin.get_admin_route())
        widget.setMinimumWidth( 800 )
        self.grab_widget( widget )

    def test_section_widget(self):
        action_step = action_steps.NavigationPanel(
            self.app_admin.get_sections()
        )
        widget = action_step.render(self.gui_context)
        self.grab_widget(widget)

    def test_main_window(self):
        proxy = MainWindowProxy( self.gui_context )
        self.grab_widget(proxy.parent())

    def test_reduced_main_window(self):
        from camelot_example.application_admin import MiniApplicationAdmin
        app_admin = MiniApplicationAdmin()
        proxy = MainWindowProxy(self.gui_context)
        proxy.parent().setStyleSheet( app_admin.get_stylesheet() )
        proxy.parent().show()
        self.grab_widget( proxy.parent() )

    def test_multiple_main_windows(self):
        """Make sure we can still create multiple QMainWindows"""
        from camelot.view.action_steps.application import MainWindow
        from camelot_example.application_admin import MiniApplicationAdmin

        app = QtWidgets.QApplication.instance()
        if app is None:
            app = QtWidgets.QApplication([])

        def count_main_windows():
            result = 0
            for widget in app.allWidgets():
                if isinstance(widget, QtWidgets.QMainWindow):
                    result += 1
            return result

        app_admin1 = MiniApplicationAdmin()
        action_step1 = MainWindow(app_admin1)
        main_window1 = action_step1.render(self.gui_context)

        num_main_windows1 = count_main_windows()

        app_admin2 = MiniApplicationAdmin()
        action_step2 = MainWindow(app_admin2)
        main_window2 = action_step2.render(self.gui_context)

        num_main_windows2 = count_main_windows()

        self.assertEqual( num_main_windows1 + 1, num_main_windows2 )

    def test_busy_widget(self):
        from camelot.view.controls.busy_widget import BusyWidget
        busy_widget = BusyWidget()
        busy_widget.set_busy( True )
        self.grab_widget( busy_widget )

    def test_search_control(self):
        from camelot.view.controls.search import SimpleSearchControl
        filter_action = SearchFilter(self.app_admin)
        search = SimpleSearchControl(filter_action, self.gui_context, None)
        self.grab_widget(search)

    def test_header_widget(self):
        from camelot.model.party import City
        from camelot.view.controls.tableview import HeaderWidget
        city_admin = self.app_admin.get_entity_admin(City)
        table = TableView(self.gui_context, city_admin.get_admin_route())
        table.set_admin()
        header = HeaderWidget(gui_context=table.gui_context, parent=None)
        self.grab_widget(header)

    def test_column_groups_widget(self):
        from camelot.view.controls.tableview import ColumnGroupsWidget
        from camelot_example.view import VisitorsPerDirector
        table = VisitorsPerDirector.Admin.list_display
        widget = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout()
        table_widget = QtWidgets.QTableWidget( 3, 6 )
        table_widget.setHorizontalHeaderLabels( table.get_fields() )
        column_groups = ColumnGroupsWidget( table,
                                            table_widget )
        layout.addWidget( table_widget )
        layout.addWidget( column_groups )
        widget.setLayout( layout )
        #
        # set the tab to 1 and then back to 0, to force a change
        # signal
        #
        column_groups.setCurrentIndex( 1 )
        column_groups.setCurrentIndex( 0 )
        self.assertFalse( table_widget.isColumnHidden( 0 ) )
        self.assertTrue( table_widget.isColumnHidden( 3 ) )
        self.grab_widget( widget, 'first_tab' )
        column_groups.setCurrentIndex( 1 )
        self.assertTrue( table_widget.isColumnHidden( 0 ) )
        self.assertFalse( table_widget.isColumnHidden( 3 ) )
        self.grab_widget( widget, 'second_tab' )

    def test_desktop_workspace(self):
        from camelot.view.workspace import DesktopWorkspace
        workspace = DesktopWorkspace(self.gui_context.admin_route, None)
        self.grab_widget(workspace)

    def test_progress_dialog( self ):
        dialog = ProgressDialog(None)
        dialog.title = 'Import cover images'
        self.grab_widget(dialog)
        dialog.add_detail('toy_story.png imported')
        dialog.add_detail('matrix.png imported')
        self.grab_widget(dialog, suffix='detail')

    def test_user_exception(self):
        from camelot.view.controls.exception import register_exception, ExceptionDialog
        exc = None
        try:
            #begin user_exception
            from camelot.core.exception import UserException

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
        open_form_view = OpenFormView([coordinate], admin)
        form = open_form_view.render(self.gui_context)
        self.grab_widget(form)

    def test_fields_with_tooltips(self):
        coordinate = Coordinate()
        admin = Coordinate.Admin( self.app_admin, Coordinate )
        open_form_view = OpenFormView([coordinate], admin)
        form = open_form_view.render(self.gui_context)
        self.grab_widget(form)

    def test_background_color(self):
        person_admin = BackgroundColorAdmin(self.app_admin, Person)
        person_columns = list(person_admin.get_columns())
        editor = One2ManyEditor(
            admin_route=person_admin.get_admin_route(),
            columns=person_columns,
        )
        editor.set_value(self.proxy)
        self.process()
        editor_model = editor.get_model()
        self.assertTrue(editor_model)
        self._load_data(editor_model)
        self.grab_widget(editor)
