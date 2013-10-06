# -*- coding: utf-8 -*-

import six

import datetime
import logging
import os
import time

from camelot.core.qt import Qt, QtGui, QtCore, py_to_variant, variant_to_py
from camelot.core.utils import ugettext_lazy as _
from camelot.core.files.storage import StoredFile, StoredImage, Storage
from camelot import test
from camelot.view.art import ColorScheme

logger = logging.getLogger('view.unittests')

static_images_path = os.path.join(os.path.dirname(__file__), '..', 'doc', 'sphinx', 'source', '_static')
storage = Storage()

def create_getter(getable):

    def getter():
        return getable

    return getter

class SignalCounter( QtCore.QObject ):

    def __init__( self ):
        super( SignalCounter, self ).__init__()
        self.counter = 0

    @QtCore.pyqtSlot()
    def signal_caught( self ):
        self.counter += 1

class EditorsTest(test.ModelThreadTestCase):
    """
  Test the basic functionality of the editors :

  - get_value
  - set_value
  - support for ValueLoading
  """

    images_path = static_images_path

    from camelot.view.controls import editors
    from camelot.view.proxy import ValueLoading

    def setUp(self):
        super(EditorsTest, self).setUp()
        self.option = QtGui.QStyleOptionViewItem()
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
        editor.set_value( self.ValueLoading )
        self.assertEqual( editor.get_value(), self.ValueLoading )
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
                          QtGui.QSizePolicy.Fixed )

    def test_ChartEditor(self):
        import math
        from camelot.container import chartcontainer
        editor = self.editors.ChartEditor()
        x_data = [x/100.0 for x in range(1, 700, 1)]
        y_data = [math.sin(x) for x in x_data]
        plot = chartcontainer.PlotContainer( x_data, y_data )
        editor.set_value( plot )
        editor.setMaximumSize( 400, 200 )
        self.grab_widget( editor, 'editable' )
        editor.set_field_attributes( editable=False )
        self.grab_widget( editor, 'disabled' )
        self.assert_valid_editor( editor, plot )

    def test_DateEditor(self):
        editor = self.editors.DateEditor()
        self.assert_vertical_size( editor )
        self.assertEqual( editor.get_value(), self.ValueLoading )
        editor.set_value( None )
        self.assertEqual( editor.get_value(), None )
        editor.set_value( datetime.date(1980, 12, 31) )
        self.grab_default_states( editor )
        self.assertEqual( editor.get_value(), datetime.date(1980, 12, 31) )
        self.assert_valid_editor( editor, datetime.date(1980, 12, 31) )

    def test_TextLineEditor(self):
        editor = self.editors.TextLineEditor(parent=None, length=10)
        self.assert_vertical_size( editor )
        self.assertEqual( editor.get_value(), self.ValueLoading )
        editor.set_value( u'za coś tam' )
        self.grab_default_states( editor )
        self.assertEqual( editor.get_value(), u'za coś tam' )
        editor.set_value( self.ValueLoading )
        self.assertEqual( editor.get_value(), self.ValueLoading )
        editor = self.editors.TextLineEditor(parent=None, length=10)
        editor.set_field_attributes( editable=False )
        self.assertEqual( editor.get_value(), self.ValueLoading )
        editor.set_value( u'za coś tam' )
        self.assertEqual( editor.get_value(), u'za coś tam' )
        editor.set_value( None )
        self.assertEqual( editor.get_value(), None )
        editor.set_value( '' )
        self.assertEqual( editor.get_value(), '' )
        # pretend the user has entered some text
        editor.setText( u'foo' )
        self.assertTrue( editor.get_value() != None )
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
        editor = self.editors.LocalFileEditor( parent=None )
        self.assert_vertical_size( editor )
        self.assertEqual( editor.get_value(), self.ValueLoading )
        editor.set_value( '/home/lancelot/quests.txt' )
        self.grab_default_states( editor )
        self.assertEqual( editor.get_value(), '/home/lancelot/quests.txt' )
        self.assert_valid_editor( editor, '/home/lancelot/quests.txt' )

    def test_StarEditor(self):
        editor = self.editors.StarEditor(parent=None, maximum=5)
        self.assert_vertical_size( editor )
        self.assertEqual( editor.get_value(), self.ValueLoading )
        editor.set_value( 4 )
        self.grab_default_states( editor )
        self.assertEqual( editor.get_value(), 4 )
        self.assert_valid_editor( editor, 4 )

    def test_SmileyEditor(self):
        editor = self.editors.SmileyEditor(parent=None)
        self.assert_vertical_size( editor )
        self.assertEqual( editor.get_value(), self.ValueLoading )
        editor.set_value( 'face-kiss' )
        self.grab_default_states( editor )
        self.assertEqual( editor.get_value(), 'face-kiss' )
        self.assert_valid_editor( editor, 'face-kiss' )

    def test_BoolEditor(self):
        editor = self.editors.BoolEditor(parent=None, editable=False, nullable=True)
        self.assert_vertical_size( editor )
        self.assertEqual( editor.get_value(), self.ValueLoading )
        editor.set_value( True )
        self.grab_default_states( editor )
        self.assertEqual( editor.get_value(), True )
        editor.set_value( False )
        self.assertEqual( editor.get_value(), False )
        editor.set_value( self.ValueLoading )
        self.assertEqual( editor.get_value(), self.ValueLoading )
        editor = self.editors.BoolEditor(parent=None, editable=False)
        self.assertEqual( editor.get_value(), self.ValueLoading )
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

    def test_CodeEditor(self):
        editor = self.editors.CodeEditor(parent=None, parts=['AAA', '999'])
        self.assert_vertical_size( editor )
        self.assertEqual( editor.get_value(), self.ValueLoading )
        editor.set_value( ['XYZ', '123'] )
        self.grab_default_states( editor )
        self.assertEqual( editor.get_value(), ['XYZ', '123'] )
        self.assert_valid_editor( editor, ['XYZ', '123'] )

    def test_ColorEditor(self):
        editor = self.editors.ColorEditor(parent=None, editable=True)
        self.assert_vertical_size( editor )
        self.assertEqual( editor.get_value(), self.ValueLoading )
        editor.set_value( (255, 200, 255, 255) )
        self.grab_default_states( editor )
        self.assertEqual( editor.get_value(), (255, 200, 255, 255) )
        self.assert_valid_editor( editor, (255, 200, 255, 255) )

    def test_ColoredFloatEditor(self):
        editor = self.editors.ColoredFloatEditor(parent=None, editable=True)
        self.assert_vertical_size( editor )
        self.assertEqual( editor.get_value(), self.ValueLoading )
        editor.set_value( 0.0 )
        self.assertEqual( editor.get_value(), 0.0 )
        editor.set_value( 3.14 )
        self.grab_default_states( editor )
        self.assertEqual( editor.get_value(), 3.14 )
        self.assert_valid_editor( editor, 3.14 )

    def test_ChoicesEditor(self):
        editor = self.editors.ChoicesEditor(parent=None, editable=True)
        self.assert_vertical_size( editor )
        choices1 = [(1,u'A'), (2,u'B'), (3,u'C')]
        editor.set_choices( choices1 )
        self.assertEqual( editor.get_value(), self.ValueLoading )
        editor.set_value( 2 )
        self.assertEqual(editor.get_choices(), choices1 + [(None,'')] )
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
        self.assertEqual( editor.get_choices(), choices2 + [(2,u'B')] + [(None,'')])
        # set a value that is not in the list, the value should become
        # ValueLoading, to prevent damage to the actual data
        editor.set_value( 33 )
        self.assertEqual( editor.get_value(), self.ValueLoading )
        # try strings as keys
        editor = self.editors.ChoicesEditor(parent=None, editable=True)
        editor.set_choices( [('a',u'A'), ('b',u'B'), ('c',u'C')] )
        editor.set_value( 'c' )
        self.assertEqual( editor.get_value(), 'c' )
        self.assert_valid_editor( editor, 'c' )

    def test_FileEditor(self):
        editor = self.editors.FileEditor(parent=None, editable=True)
        self.assert_vertical_size( editor )
        self.assertEqual( editor.get_value(), self.ValueLoading )
        self.grab_default_states( editor )
        self.assert_valid_editor( editor, StoredFile( storage, 'test.txt') )

    def test_DateTimeEditor(self):
        from camelot.view.controls.editors.datetimeeditor import TimeValidator
        validator = TimeValidator()
        self.assertEqual(validator.validate('22', 0), (QtGui.QValidator.Intermediate, 0))
        self.assertEqual(validator.validate('59', 0), (QtGui.QValidator.Intermediate, 0))
        self.assertEqual(validator.validate('22:', 0), (QtGui.QValidator.Intermediate, 0))
        self.assertEqual(validator.validate(':17', 0), (QtGui.QValidator.Intermediate, 0))
        self.assertEqual(validator.validate('22:7', 0), (QtGui.QValidator.Acceptable, 0))
        self.assertEqual(validator.validate('22:17', 0), (QtGui.QValidator.Acceptable, 0))
        self.assertEqual(validator.validate('1:17', 0), (QtGui.QValidator.Acceptable, 0))
        self.assertEqual(validator.validate('22:7:', 0), (QtGui.QValidator.Invalid, 0))
        self.assertEqual(validator.validate('61', 0), (QtGui.QValidator.Invalid, 0))
        self.assertEqual(validator.validate('611', 0), (QtGui.QValidator.Invalid, 0))
        editor = self.editors.DateTimeEditor(parent=None, editable=True)
        self.assert_vertical_size( editor )
        self.assertEqual( editor.get_value(), self.ValueLoading )
        editor.set_value( datetime.datetime(2009, 7, 19, 21, 5, 10, 0) )
        self.assertEqual( editor.get_value(), datetime.datetime(2009, 7, 19, 21, 5, 0 ) )
        self.grab_default_states( editor )
        self.assert_valid_editor( editor, datetime.datetime(2009, 7, 19, 21, 5, 0 ) )
        editor.set_value(None)
        self.assertEqual(editor.get_value(), None)

    def test_FloatEditor(self):
        from camelot.core.constants import camelot_minfloat, camelot_maxfloat
        editor = self.editors.FloatEditor(parent=None)
        editor.set_field_attributes(prefix='prefix')
        self.assert_vertical_size( editor )
        self.assertEqual( editor.get_value(), self.ValueLoading )
        editor.set_value( 0.0 )
        self.assertEqual( editor.get_value(), 0.0 )
        editor.set_value( 3.14 )
        self.grab_default_states( editor )
        self.assertEqual( editor.get_value(), 3.14 )
        editor = self.editors.FloatEditor(parent=None, option=self.option)
        editor.set_field_attributes(suffix='suffix')
        self.assertEqual( editor.get_value(), self.ValueLoading )
        editor.set_value( 0.0 )
        self.assertEqual( editor.get_value(), 0.0 )
        editor.set_value( 3.14 )
        self.assertEqual( editor.get_value(), 3.14 )
        editor.set_value( 5.45 )
        editor.set_value( None )
        self.assertEqual( editor.get_value(), None )
        up = QtGui.QKeyEvent(QtCore.QEvent.KeyPress, Qt.Key_Up, Qt.NoModifier)
        spinbox = editor.findChild(QtGui.QWidget, 'spinbox')
        self.assertEqual(spinbox.minimum(), camelot_minfloat-1)
        self.assertEqual(spinbox.maximum(), camelot_maxfloat)
        spinbox.keyPressEvent(up)
        self.assertEqual(editor.get_value(), 0.0)
        # pretend the user has entered something
        editor = self.editors.FloatEditor(parent=None)
        editor.set_field_attributes(prefix='prefix', suffix='suffix')
        spinbox = editor.findChild(QtGui.QWidget, 'spinbox')
        spinbox.setValue( 0.0 )
        self.assertTrue( editor.get_value() != None )
        self.assertEqual(spinbox.validate(QtCore.QString('prefix 0 suffix'), 1)[0], QtGui.QValidator.Acceptable)
        self.assertEqual(spinbox.validate(QtCore.QString('prefix  suffix'), 1)[0], QtGui.QValidator.Acceptable)
        # verify if the calculator button is turned off
        editor = self.editors.FloatEditor(parent=None,
                                          calculator=False)
        editor.set_field_attributes( editable=True )
        editor.set_value( 3.14 )
        self.grab_widget( editor, 'no_calculator' )
        self.assertTrue( editor.calculatorButton.isHidden() )
        self.assert_valid_editor( editor, 3.14 )

    def test_ImageEditor(self):
        editor = self.editors.ImageEditor(parent=None, editable=True)
        self.assertEqual( editor.get_value(), self.ValueLoading )
        self.grab_default_states( editor )
        self.assert_valid_editor( editor, StoredImage( storage, 'test.png') )

    def test_IntegerEditor(self):
        editor = self.editors.IntegerEditor(parent=None, editable=True)
        self.assert_vertical_size( editor )
        self.assertEqual( editor.get_value(), self.ValueLoading )
        editor.set_value( 0 )
        self.assertEqual( editor.get_value(), 0 )
        editor.set_value( 3 )
        self.grab_default_states( editor )
        self.assertEqual( editor.get_value(), 3 )
        editor.set_value( None )
        # pretend the user changed the value
        editor.spinBox.setValue( 0 )
        self.assertEqual( editor.get_value(), 0 )
        editor.set_value( None )
        self.assertEqual( editor.get_value(), None )
        # turn off the calculator
        editor = self.editors.IntegerEditor(parent=None,
                                            calculator=False)
        editor.set_field_attributes( editable=True )
        editor.set_value( 3 )
        self.grab_widget( editor, 'no_calculator' )
        self.assertTrue( editor.calculatorButton.isHidden() )
        self.assert_valid_editor( editor, 3 )

    def test_NoteEditor(self):
        editor = self.editors.NoteEditor(parent=None)
        editor.set_value('A person with this name already exists')
        self.grab_widget( editor )
        self.grab_default_states( editor )
        self.assert_valid_editor( editor, 'A person with this name already exists' )

    def test_LabelEditor(self):
        editor = self.editors.LabelEditor(parent=None)
        editor.set_value('Dynamic label')
        self.grab_default_states( editor )

    def test_LanguageEditor(self):
        editor = self.editors.LanguageEditor(parent=None)
        self.assert_vertical_size( editor )
        self.assertEqual( editor.get_value(), self.ValueLoading )
        editor.set_value( 'en_US' )
        self.grab_default_states( editor )
        self.assertEqual( editor.get_value(), 'en_US' )
        self.assert_valid_editor( editor, 'en_US' )

    def test_Many2OneEditor(self):
        editor = self.editors.Many2OneEditor(parent=None)
        self.assert_vertical_size( editor )
        self.grab_default_states( editor )
        self.assert_valid_editor( editor, lambda:object )

    def test_RichTextEditor(self):
        editor = self.editors.RichTextEditor(parent=None)
        self.assertEqual( editor.get_value(), self.ValueLoading )
        editor.set_value( u'<h1>Rich Text Editor</h1>' )
        self.grab_default_states( editor )
        self.assertTrue( u'Rich Text Editor' in editor.get_value() )
        self.assert_valid_editor( editor, u'<h1>Rich Text Editor</h1>' )

    def test_TimeEditor(self):

        import datetime
        editor = self.editors.TimeEditor(parent=None, editable=True)
        self.assert_vertical_size( editor )
        self.assertEqual( editor.get_value(), self.ValueLoading )
        editor.set_value( datetime.time(21, 5, 0) )
        self.grab_default_states( editor )
        self.assertEqual( editor.get_value(), datetime.time(21, 5, 0) )
        self.assert_valid_editor( editor, datetime.time(21, 5, 0) )

    def test_TextEditEditor(self):
        editor = self.editors.TextEditEditor(parent=None, editable=True)
        self.assertEqual( editor.get_value(), self.ValueLoading )
        editor.set_value( 'Plain text' )
        self.grab_default_states( editor )
        self.assertEqual( editor.get_value(), 'Plain text' )
        self.assert_valid_editor( editor, 'Plain text' )

    def test_VirtualAddressEditor(self):
        editor = self.editors.VirtualAddressEditor(parent=None)
        self.assert_vertical_size( editor )
        self.assertEqual( editor.get_value(), self.ValueLoading )
        editor.set_value( ('im','test') )
        self.grab_default_states( editor )
        self.assertEqual( editor.get_value(),  ('im','test') )
        self.assert_valid_editor( editor, ('im','test') )

    def test_MonthsEditor(self):
        editor = self.editors.MonthsEditor(parent=None)
        self.assert_vertical_size( editor )
        self.assertEqual(editor.get_value(), self.ValueLoading)
        editor.set_value(12)
        self.grab_default_states( editor )
        self.assertEqual(editor.get_value(),  12)
        self.assert_valid_editor( editor, 12 )

from camelot.view import forms

class FormTest(test.ModelThreadTestCase):

    images_path = static_images_path

    def setUp(self):
        test.ModelThreadTestCase.setUp(self)
        from camelot.view.controls.formview import FormEditors
        from camelot.core.orm import entities
        self.entities = [e for e in entities]
        from camelot.admin.action import GuiContext
        from camelot.admin.application_admin import ApplicationAdmin
        from camelot.view.proxy.queryproxy import QueryTableProxy
        from camelot.view.controls.delegates import DelegateManager
        from camelot.model.party import Person
        from camelot_example.model import Movie
        self.app_admin = ApplicationAdmin()
        self.movie_admin = self.app_admin.get_related_admin( Movie )

        self.movie_model = QueryTableProxy( self.movie_admin)
        self.movie_model.set_value(self.movie_admin.get_query())
        self.movie_model.set_columns(self.movie_admin.get_fields())

        delegate = DelegateManager(self.movie_admin.get_fields())
        widget_mapper = QtGui.QDataWidgetMapper()
        widget_mapper.setModel( self.movie_model )
        widget_mapper.setItemDelegate(delegate)
        self.widgets = FormEditors( self.movie_admin.get_fields(),
                                    widget_mapper,
                                    self.movie_admin )

        self.person_entity = Person
        self.gui_context = GuiContext()

    def tearDown(self):
        #
        # The global list of entities should remain clean for subsequent tests
        #
        from camelot.core.orm import entities
        for e in entities:
            if e not in self.entities:
                entities.remove(e)

    def test_form(self):
        from .snippet.form.simple_form import Movie
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
        from camelot.view.action_steps import OpenFormView
        person_admin = Admin(self.app_admin, self.person_entity)
        open_form_view = OpenFormView([self.person_entity()], person_admin)
        self.grab_widget( open_form_view.render(self.gui_context) )

    def test_inherited_form(self):
        from camelot.view.action_steps import OpenFormView
        person_admin = InheritedAdmin(self.app_admin, self.person_entity)
        open_form_view = OpenFormView([self.person_entity()], person_admin)
        self.grab_widget( open_form_view.render(self.gui_context) )

    def test_custom_layout(self):
        from camelot.view.action_steps import OpenFormView
        person_admin = Admin(self.app_admin, self.person_entity)
        open_form_view = OpenFormView([self.person_entity()], person_admin)
        self.grab_widget( open_form_view.render(self.gui_context) )

class DelegateTest(test.ModelThreadTestCase):
    """Test the basic functionallity of the delegates :
  - createEditor
  - setEditorData
  - setModelData
  """

    from camelot.view.controls import delegates
    from camelot.view.controls import editors

    def setUp(self):
        super(DelegateTest, self).setUp()
        self.kwargs = dict(editable=True)
        self.option = QtGui.QStyleOptionViewItem()
        # set version to 5 to indicate the widget will appear on a
        # a form view and not on a table view, so it should not
        # set its background
        self.option.version = 5

    def grab_delegate(self, delegate, data, suffix='editable'):
        import sys
        from camelot.view.controls.tableview import TableWidget

        model = QtGui.QStandardItemModel(1, 1)
        index = model.index(0, 0, QtCore.QModelIndex())
        model.setData( index, py_to_variant( data ) )
        model.setData( index, py_to_variant( QtGui.QColor('white') ), Qt.BackgroundRole )
        model.setData( index, py_to_variant( dict(editable=True) ), Qt.UserRole )

        option = QtGui.QStyleOptionViewItem()

        if suffix == 'editable':
            self.assertTrue(delegate.sizeHint(option, index).height()>1)

        tableview = TableWidget()
        tableview.setModel(model)
        tableview.setItemDelegate(delegate)

        test_case_name = sys._getframe(1).f_code.co_name[4:]

        for state_name, state in zip(('selected', 'unselected'),
                                     (QtGui.QStyle.State_Selected, 
                                      QtGui.QStyle.State_None)):
            tableview.adjustSize()

            if state == QtGui.QStyle.State_Selected:
                tableview.selectionModel().select(index, QtGui.QItemSelectionModel.Select)
            else:
                tableview.selectionModel().select(index, QtGui.QItemSelectionModel.Clear)

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
            pixmap = QtGui.QPixmap.grabWidget(tableview)
            pixmap.save(os.path.join(delegate_images_path, '%s_%s_%s.png'%(test_case_name, state_name, suffix)),
                        'PNG')

    def testPlainTextDelegate(self):
        delegate = self.delegates.PlainTextDelegate(parent=None,
                                                    length=30,
                                                    editable=True)
        editor = delegate.createEditor(None, self.option, None)
        self.assertEqual(editor.maxLength(), 30)
        self.assertTrue(isinstance(editor, self.editors.TextLineEditor))
        self.grab_delegate(delegate, 'Plain Text')
        delegate = self.delegates.PlainTextDelegate(parent=None,
                                                    length=20,
                                                    editable=False)
        editor = delegate.createEditor(None, self.option, None)
        self.assertTrue(isinstance(editor, self.editors.TextLineEditor))
        self.grab_delegate(delegate, 'Plain Text', 'disabled')
        small_text_delegate = self.delegates.PlainTextDelegate( length = 3 )
        wide_text_delegate = self.delegates.PlainTextDelegate( length = 30 )
        small_size = small_text_delegate.sizeHint( None, 0 ).width()
        wide_size = wide_text_delegate.sizeHint( None, 0 ).width()
        self.assertTrue( small_size < wide_size )

    def testTextEditDelegate(self):
        from PyQt4.QtGui import QTextEdit
        delegate = self.delegates.TextEditDelegate(parent=None, **self.kwargs)
        editor = delegate.createEditor(None, self.option, None)
        self.assertTrue(isinstance(editor, QTextEdit))
        self.grab_delegate(delegate, 'Plain Text')
        delegate = self.delegates.TextEditDelegate(parent=None, editable=False)
        editor = delegate.createEditor(None, self.option, None)
        self.assertTrue(isinstance(editor, QTextEdit))
        self.grab_delegate(delegate, 'Plain Text', 'disabled')

    def testRichTextDelegate(self):
        delegate = self.delegates.RichTextDelegate(parent=None, **self.kwargs)
        editor = delegate.createEditor(None, self.option, None)
        self.assertTrue(isinstance(editor, self.editors.RichTextEditor))
        self.grab_delegate(delegate, '<b>Rich Text</b>')
        delegate = self.delegates.RichTextDelegate(parent=None, editable=False)
        editor = delegate.createEditor(None, self.option, None)
        self.assertTrue(isinstance(editor, self.editors.RichTextEditor))
        self.grab_delegate(delegate, '<b>Rich Text</b>', 'disabled')

    def testBoolDelegate(self):
        delegate = self.delegates.BoolDelegate(parent=None, **self.kwargs)
        editor = delegate.createEditor(None, self.option, None)
        self.assertTrue(isinstance(editor, self.editors.BoolEditor))
        self.grab_delegate(delegate, True)
        delegate = self.delegates.BoolDelegate(parent=None, editable=False)
        editor = delegate.createEditor(None, self.option, None)
        self.assertTrue(isinstance(editor, self.editors.BoolEditor))
        self.grab_delegate(delegate, True, 'disabled')

    def testDateDelegate(self):
        from datetime import date
        delegate = self.delegates.DateDelegate(parent=None, **self.kwargs)
        editor = delegate.createEditor(None, self.option, None)
        self.assertTrue(isinstance(editor, self.editors.DateEditor))
        date = date.today()
        self.grab_delegate(delegate, date)
        delegate = self.delegates.DateDelegate(parent=None, editable=False)
        editor = delegate.createEditor(None, self.option, None)
        self.assertTrue(isinstance(editor, self.editors.DateEditor))
        date = date.today()
        self.grab_delegate(delegate, date, 'disabled')
        #TODO  !!

    def testDateTimeDelegate(self):
        from datetime import datetime
        delegate = self.delegates.DateTimeDelegate(parent=None, **self.kwargs)
        editor = delegate.createEditor(None, self.option, None)
        self.assertTrue(isinstance(editor, self.editors.DateTimeEditor))
        DateTime = datetime.now()
        self.grab_delegate(delegate, DateTime)
        delegate = self.delegates.DateTimeDelegate(parent=None, editable=False)
        editor = delegate.createEditor(None, self.option, None)
        self.assertTrue(isinstance(editor, self.editors.DateTimeEditor))
        self.grab_delegate(delegate, DateTime, 'disabled')

    def testLocalFileDelegate(self):
        delegate = self.delegates.LocalFileDelegate(parent=None)
        self.grab_delegate(delegate, '/home/lancelot/quests.txt')
        delegate = self.delegates.LocalFileDelegate(parent=None, editable=False)
        self.grab_delegate(delegate, '/home/lancelot/quests.txt', 'disabled')

    def testLabelDelegate(self):
        delegate = self.delegates.LabelDelegate(parent=None)
        self.grab_delegate(delegate, 'dynamic label')
        delegate = self.delegates.LabelDelegate(parent=None, editable=False)
        self.grab_delegate(delegate, 'dynamic label', 'disabled')

    def testNoteDelegate(self):
        delegate = self.delegates.NoteDelegate(parent=None)
        self.grab_delegate(delegate, 'important note')
        delegate = self.delegates.NoteDelegate(parent=None, editable=False)
        self.grab_delegate(delegate, 'important note', 'disabled')

    def testMonthsDelegate(self):
        delegate = self.delegates.MonthsDelegate(parent=None)
        self.grab_delegate(delegate, 15)
        delegate = self.delegates.MonthsDelegate(parent=None, editable=False)
        self.grab_delegate(delegate, 15, 'disabled')

    def testMany2OneDelegate(self):
        delegate = self.delegates.Many2OneDelegate(parent=None, admin=object())
        self.grab_delegate(delegate, None)
        delegate = self.delegates.Many2OneDelegate(parent=None, editable=False, admin=object())
        self.grab_delegate(delegate, None, 'disabled')

    def testOne2ManyDelegate(self):
        delegate = self.delegates.One2ManyDelegate(parent=None, admin=object())
        self.grab_delegate(delegate, [])
        delegate = self.delegates.One2ManyDelegate(parent=None, editable=False, admin=object())
        self.grab_delegate(delegate, [], 'disabled')

    def testTimeDelegate(self):
        from datetime import time
        delegate = self.delegates.TimeDelegate(parent=None, editable=True)
        editor = delegate.createEditor(None, self.option, None)
        self.assertTrue(isinstance(editor, self.editors.TimeEditor))
        time = time(10, 30, 15)
        self.grab_delegate(delegate, time)
        delegate = self.delegates.TimeDelegate(parent=None, editable=False)
        editor = delegate.createEditor(None, self.option, None)
        self.assertTrue(isinstance(editor, self.editors.TimeEditor))
        #time = time(10, 30, 15)
        self.grab_delegate(delegate, time, 'disabled')

    def testIntegerDelegate(self):
        delegate = self.delegates.IntegerDelegate(parent=None, editable=True)
        editor = delegate.createEditor(None, self.option, None)
        self.assertTrue(isinstance(editor, self.editors.IntegerEditor))
        self.grab_delegate(delegate, 3)
        delegate = self.delegates.IntegerDelegate(parent=None, editable=False)
        editor = delegate.createEditor(None, self.option, None)
        self.assertTrue(isinstance(editor, self.editors.IntegerEditor))
        self.grab_delegate(delegate, 0, 'disabled')

    def testIntervalsDelegate(self):
        from camelot.container import IntervalsContainer, Interval
        intervals = IntervalsContainer(0, 24, [Interval(8, 18, 'work', QtGui.QColor(255,0,0,255)), Interval(19, 21, 'play', QtGui.QColor(0,255,0,255))])
        delegate = self.delegates.IntervalsDelegate(parent=None, editable=True)
        self.grab_delegate(delegate, intervals)
        delegate = self.delegates.IntervalsDelegate(parent=None, editable=False)
        self.grab_delegate(delegate, intervals, 'disabled')

    def testFloatDelegate(self):
        delegate = self.delegates.FloatDelegate(parent=None, suffix='euro', editable=True)
        editor = delegate.createEditor(None, self.option, None)
        self.assertTrue(isinstance(editor, self.editors.FloatEditor))
        self.grab_delegate(delegate, 3.145)
        delegate = self.delegates.FloatDelegate(parent=None, prefix='prefix', editable=False)
        editor = delegate.createEditor(None, self.option, None)
        self.assertTrue(isinstance(editor, self.editors.FloatEditor))
        self.grab_delegate(delegate, 0, 'disabled')

    def testColoredFloatDelegate(self):
        delegate = self.delegates.ColoredFloatDelegate(parent=None, precision=3, editable=True)
        editor = delegate.createEditor(None, self.option, None)
        self.assertTrue(isinstance(editor, self.editors.ColoredFloatEditor))
        self.grab_delegate(delegate, 3.14456)
        delegate = self.delegates.ColoredFloatDelegate(parent=None, editable=False)
        editor = delegate.createEditor(None, self.option, None)
        self.assertTrue(isinstance(editor, self.editors.ColoredFloatEditor))
        self.grab_delegate(delegate, 3.1, 'disabled')

    def testStarDelegate(self):
        delegate = self.delegates.StarDelegate(parent=None, **self.kwargs)
        editor = delegate.createEditor(None, self.option, None)
        self.assertTrue(delegate.maximum, 5)
        self.assertTrue(isinstance(editor, self.editors.StarEditor))
        self.grab_delegate(delegate, 5)
        delegate = self.delegates.StarDelegate(parent=None, editable=False)
        editor = delegate.createEditor(None, self.option, None)
        self.assertTrue(delegate.maximum, 5)
        self.assertTrue(isinstance(editor, self.editors.StarEditor))
        self.grab_delegate(delegate, 5, 'disabled')

    def testSmileyDelegate(self):
        delegate = self.delegates.SmileyDelegate(parent=None, **self.kwargs)
        editor = delegate.createEditor(None, self.option, None)
        self.assertTrue(isinstance(editor, self.editors.SmileyEditor))
        self.grab_delegate(delegate, 'face-glasses')
        delegate = self.delegates.SmileyDelegate(parent=None, editable=False)
        editor = delegate.createEditor(None, self.option, None)
        self.assertTrue(isinstance(editor, self.editors.SmileyEditor))
        self.grab_delegate(delegate, 'face-glasses', 'disabled')

    def testFileDelegate(self):
        from camelot.core.files.storage import StoredFile
        delegate = self.delegates.FileDelegate(parent=None)
        file = StoredFile(None, 'agreement.pdf')
        editor = delegate.createEditor(None, self.option, None)
        self.assertTrue(isinstance(editor, self.editors.FileEditor))
        self.grab_delegate(delegate, file)
        delegate = self.delegates.FileDelegate(parent=None, editable=False)
        self.grab_delegate(delegate, file, 'disabled')

    def testColorDelegate(self):
        delegate = self.delegates.ColorDelegate(parent=None, **self.kwargs)
        editor = delegate.createEditor(None, self.option, None)
        self.assertTrue(isinstance(editor, self.editors.ColorEditor))
        color = [255, 255, 0]
        self.grab_delegate(delegate, color)
        delegate = self.delegates.ColorDelegate(parent=None, editable=False)
        editor = delegate.createEditor(None, self.option, None)
        self.assertTrue(isinstance(editor, self.editors.ColorEditor))
        self.grab_delegate(delegate, color, 'disabled')

    def testCodeDelegate(self):
        delegate = self.delegates.CodeDelegate(parent=None, parts=['99','AA'], **self.kwargs)
        editor = delegate.createEditor(None, self.option, None)
        self.assertTrue(isinstance(editor, self.editors.CodeEditor))
        self.grab_delegate(delegate, ['76','AB'])
        delegate = self.delegates.CodeDelegate(parent=None, parts=['99','AA', '99', 'AA'], editable=False)
        editor = delegate.createEditor(None, self.option, None)
        self.assertTrue(isinstance(editor, self.editors.CodeEditor))
        self.grab_delegate(delegate, ['76','AB', '12', '34'], 'disabled')

    def testCurrencyDelegate(self):
        delegate = self.delegates.CurrencyDelegate(parent=None, suffix='euro', **self.kwargs)
        editor = delegate.createEditor(None, self.option, None)
        self.assertTrue(isinstance(editor, self.editors.FloatEditor))
        self.grab_delegate(delegate, 1000000.12)
        delegate = self.delegates.CurrencyDelegate(parent=None, prefix='prefix', editable=False)
        self.grab_delegate(delegate, 1000000.12, 'disabled')

    def testComboBoxDelegate(self):
        CHOICES = (('1','A'), ('2','B'), ('3','C'))
        delegate = self.delegates.ComboBoxDelegate(parent=None,
                                                   choices=CHOICES,
                                                   **self.kwargs)
        editor = delegate.createEditor(None, self.option, None)
        self.assertTrue(isinstance(editor, self.editors.ChoicesEditor))
        self.grab_delegate(delegate, 1)
        delegate = self.delegates.ComboBoxDelegate(parent=None,
                                                   choices=CHOICES,
                                                   editable=False)
        self.grab_delegate(delegate, 1, 'disabled')

    def testImageDelegate(self):
        delegate = self.delegates.ImageDelegate(parent=None, **self.kwargs)
        editor = delegate.createEditor(None, self.option, None)
        self.assertTrue(isinstance(editor, self.editors.ImageEditor))

    def testVirtualAddressDelegate(self):
        delegate = self.delegates.VirtualAddressDelegate(parent=None,
                                                         **self.kwargs)
        editor = delegate.createEditor(None, self.option, None)
        self.assertTrue(isinstance(editor, self.editors.VirtualAddressEditor))
        self.grab_delegate(delegate, ('email', 'project-camelot@conceptive.be'))
        delegate = self.delegates.VirtualAddressDelegate(parent=None, editable=False)
        self.grab_delegate(delegate, ('email', 'project-camelot@conceptive.be'), 'disabled')

    def testMonthsDelegate(self):
        delegate = self.delegates.MonthsDelegate(parent=None, **self.kwargs)
        editor = delegate.createEditor(None, self.option, None)
        self.assertTrue(isinstance(editor, self.editors.MonthsEditor))
        self.grab_delegate(delegate, 12)
        delegate = self.delegates.MonthsDelegate(parent=None, editable=False)
        self.grab_delegate(delegate, 12, 'disabled')


class FilterTest(test.ModelThreadTestCase):
    """Test the filters in the table view"""

    images_path = static_images_path
    from camelot.view import filters

    group_box_filter = filters.GroupBoxFilter('state')
    combo_box_filter = filters.ComboBoxFilter('state')
    test_data = filters.filter_data( name = _('Organization'),
                                    default = 1,
                                    options = [ filters.filter_option( name = 'Nokia',
                                                                       value = 1,
                                                                       decorator = None ),
                                                filters.filter_option( name = 'Apple',
                                                                       value = 2,
                                                                       decorator = None ) ] )

    def test_group_box_filter(self):
        self.grab_widget( self.group_box_filter.render( self.test_data, None ) )

    def test_combo_box_filter(self):
        self.grab_widget( self.combo_box_filter.render( self.test_data, None ) )

    def test_filter_list(self):
        from camelot.view.controls.filterlist import FilterList
        items = [ ( self.group_box_filter, self.test_data ),
                  ( self.combo_box_filter, self.test_data ) ]
        filter_list = FilterList( items, parent=None)
        self.grab_widget( filter_list )

    def test_filter_list_in_table_view(self):
        from camelot.view.controls.tableview import TableView
        from camelot.model.party import Person
        from camelot.admin.application_admin import ApplicationAdmin
        from camelot.admin.action.base import GuiContext
        gui_context = GuiContext()
        app_admin = ApplicationAdmin()
        person_admin = Person.Admin(app_admin, Person)
        table_view = TableView( gui_context, person_admin )
        items = [ (self.group_box_filter, self.test_data ),
                  (self.combo_box_filter, self.test_data ) ]
        table_view.set_filters(items)

class ControlsTest(test.ModelThreadTestCase):
    """Test some basic controls"""

    images_path = static_images_path

    def setUp(self):
        super(ControlsTest, self).setUp()
        from camelot_example.application_admin import MyApplicationAdmin
        from camelot.admin.action.application_action import ApplicationActionGuiContext
        self.app_admin = MyApplicationAdmin()
        self.gui_context = ApplicationActionGuiContext()
        self.gui_context.admin = self.app_admin

    def wait_for_animation( self ):
        # wait a while to make sure all animations are finished
        for i in range(10):
            time.sleep(0.1)
            self.app.processEvents()

    def test_table_view(self):
        from camelot.view.controls.tableview import TableView
        from camelot.model.party import Person
        from camelot.admin.action.base import GuiContext
        gui_context = GuiContext()
        widget = TableView( gui_context,
                            self.app_admin.get_entity_admin(Person) )
        self.grab_widget(widget)

    def test_rows_widget(self):
        from camelot.view.controls.tableview import RowsWidget
        model = QtGui.QStringListModel(['one', 'two', 'three'])
        
        widget = RowsWidget()
        widget.set_model(model)
        self.assertTrue('3' in str(widget.text()))
        
        model.setStringList(['one', 'two'])
        self.assertTrue('2' in str(widget.text()))
        
    def test_small_column( self ):
        #create a table view for an Admin interface with small columns
        from camelot.view.controls.tableview import TableView
        from camelot.model.party import Person

        class SmallColumnsAdmin( Person.Admin ):
            list_display = ['first_name', 'suffix']

        admin = SmallColumnsAdmin( self.app_admin, Person )
        widget = TableView( self.gui_context,
                            admin )
        widget.set_admin(admin)
        widget.get_model().set_columns(admin.get_columns())
        self.grab_widget( widget )
        model = widget.get_model()
        header = widget.table.horizontalHeader()

        first_name_width = variant_to_py( model.headerData( 0, Qt.Horizontal, Qt.SizeHintRole ) ).width()
        suffix_width = variant_to_py( model.headerData( 1, Qt.Horizontal, Qt.SizeHintRole ) ).width()

        self.assertTrue( first_name_width > suffix_width )

    def test_column_width( self ):
        #create a table view for an Admin interface with small columns
        from camelot.view.controls.tableview import TableView
        from camelot.model.party import Person

        class ColumnWidthAdmin( Person.Admin ):
            list_display = ['first_name', 'suffix']
            # begin column width
            field_attributes = { 'first_name':{'column_width':8},
                                 'suffix':{'column_width':8},}
            # end column width

        admin = ColumnWidthAdmin( self.app_admin, Person )
        widget = TableView(self.gui_context, admin)
        widget.set_admin(admin)
        widget.get_model().set_columns(admin.get_columns())
        self.grab_widget( widget )
        model = widget.get_model()
        header = widget.table.horizontalHeader()

        first_name_width = variant_to_py( model.headerData( 0, Qt.Horizontal, Qt.SizeHintRole ) ).width()
        suffix_width = variant_to_py( model.headerData( 1, Qt.Horizontal, Qt.SizeHintRole ) ).width()

        self.assertEqual( first_name_width, suffix_width )

    def test_column_group( self ):
        from camelot.admin.table import ColumnGroup
        from camelot.view.controls.tableview import TableView
        from camelot.model.party import Person

        class ColumnWidthAdmin( Person.Admin ):
            #begin column group
            list_display = [ ColumnGroup( _('Name'), ['first_name', 'last_name', 'suffix'] ),
                             ColumnGroup( _('Official'), ['birthdate', 'social_security_number', 'passport_number'] ),
                             ]
            #end column group

        admin = ColumnWidthAdmin( self.app_admin, Person )
        widget = TableView( self.gui_context,
                            admin )
        widget.setMinimumWidth( 800 )
        self.grab_widget( widget )

    def test_section_widget(self):
        from camelot.view.controls import section_widget
        self.wait_for_animation()
        widget = section_widget.NavigationPane( self.app_admin,
                                                workspace = None,
                                                parent = None )
        widget.set_sections( self.app_admin.get_sections() )
        self.grab_widget(widget)

    def test_main_window(self):
        from camelot.view.mainwindow import MainWindow
        widget = MainWindow( self.gui_context )
        self.wait_for_animation()
        self.grab_widget(widget)

    def test_reduced_main_window(self):
        from camelot.view.mainwindow import MainWindow
        from camelot_example.application_admin import MiniApplicationAdmin
        from camelot.admin.action.application_action import ApplicationActionGuiContext
        app_admin = MiniApplicationAdmin()
        gui_context = ApplicationActionGuiContext()
        gui_context.admin = app_admin
        widget = MainWindow( gui_context )
        widget.setStyleSheet( app_admin.get_stylesheet() )
        widget.show()
        self.wait_for_animation()
        self.grab_widget( widget )

    def test_busy_widget(self):
        from camelot.view.controls.busy_widget import BusyWidget
        busy_widget = BusyWidget()
        busy_widget.set_busy( True )
        self.grab_widget( busy_widget )

    def test_search_control(self):
        from camelot.view.controls.search import SimpleSearchControl
        search = SimpleSearchControl(None)
        self.grab_widget(search)

    def test_header_widget(self):
        from camelot.model.party import City
        from camelot.view.controls.tableview import HeaderWidget
        person_admin = self.app_admin.get_entity_admin(City)
        header = HeaderWidget(parent=None, admin=person_admin)
        header.expand_search_options()
        self.grab_widget(header)

    def test_column_groups_widget(self):
        from camelot.view.controls.tableview import ColumnGroupsWidget
        from camelot_example.view import VisitorsPerDirector
        table = VisitorsPerDirector.Admin.list_display
        widget = QtGui.QWidget()
        layout = QtGui.QVBoxLayout()
        table_widget = QtGui.QTableWidget( 3, 6 )
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
        from camelot.admin.action import Action
        from camelot.view.art import Icon

        action1 = Action()
        action1.icon=Icon('tango/32x32/places/network-server.png')
        action2 = Action()
        action2.icon=Icon('tango/32x32/places/user-trash.png')
        action3 = Action()
        action3.icon=Icon('tango/32x32/places/start-here.png')
        desktopWorkspace = DesktopWorkspace(self.app_admin, None)
        actions = [ action1, action2, action3 ]

        desktopWorkspace._background_widget.set_actions( actions )
        self.grab_widget(desktopWorkspace)

    def test_progress_dialog( self ):
        from camelot.view.controls.progress_dialog import ProgressDialog
        dialog = ProgressDialog( 'Import cover images' )
        self.grab_widget( dialog )

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

class CamelotEntityViewsTest(test.EntityViewsTest):
    """Test the views of all the Entity subclasses"""

    images_path = static_images_path

    def get_admins(self):
        for admin in super(CamelotEntityViewsTest, self).get_admins():
            if admin.entity.__module__.startswith('camelot.model'):
                yield admin

class SnippetsTest(test.ModelThreadTestCase):

    images_path = static_images_path

    def setUp( self ):
        super( SnippetsTest, self ).setUp()
        from camelot.admin.action.base import GuiContext
        from camelot.admin.application_admin import ApplicationAdmin
        self.app_admin = ApplicationAdmin()
        self.gui_context = GuiContext()

    def test_simple_plot(self):
        from .snippet.chart.simple_plot import Wave
        from camelot.view.action_steps import OpenFormView
        wave = Wave()
        admin = Wave.Admin( self.app_admin, Wave )
        open_form_view = OpenFormView([wave], admin)
        form = open_form_view.render(self.gui_context)
        form.setMaximumSize( 400, 200 )
        self.grab_widget(form)

    def test_advanced_plot(self):
        from .snippet.chart.advanced_plot import Wave
        from camelot.view.action_steps import OpenFormView
        wave = Wave()
        #wave.phase = '2.89'
        admin = Wave.Admin( self.app_admin, Wave )
        open_form_view = OpenFormView([wave], admin)
        form = open_form_view.render(self.gui_context)
        form.setMaximumSize( 400, 200 )
        self.grab_widget(form)

    def test_fields_with_actions(self):
        from .snippet.fields_with_actions import Coordinate
        from camelot.view.action_steps import OpenFormView
        coordinate = Coordinate()
        admin = Coordinate.Admin( self.app_admin, Coordinate )
        open_form_view = OpenFormView([coordinate], admin)
        form = open_form_view.render(self.gui_context)
        self.grab_widget(form)

    def test_fields_with_tooltips(self):
        from .snippet.fields_with_tooltips import Coordinate
        from camelot.view.action_steps import OpenFormView
        coordinate = Coordinate()
        admin = Coordinate.Admin( self.app_admin, Coordinate )
        open_form_view = OpenFormView([coordinate], admin)
        form = open_form_view.render(self.gui_context)
        self.grab_widget(form)

    def test_background_color(self):
        from camelot.model.party import Person
        from .snippet.background_color import Admin
        person_admin = Admin( self.app_admin, Person )
        from camelot.view.controls.editors.one2manyeditor import One2ManyEditor
        editor = One2ManyEditor(admin=person_admin)
        editor.set_value([Person(first_name='John', last_name='Cleese'),
                          Person(first_name='eric', last_name='Idle')])
        self.process()
        self.grab_widget(editor)
