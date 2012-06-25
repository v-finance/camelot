# -*- coding: utf-8 -*-
from PyQt4 import QtGui

import logging
import unittest
import os
import time

from camelot.core.utils import ugettext_lazy as _
from camelot.core.files.storage import StoredFile, StoredImage, Storage
from camelot.test import ModelThreadTestCase, EntityViewsTest
from camelot.view.art import ColorScheme

from PyQt4 import QtGui, QtCore
from PyQt4.QtGui import *
from PyQt4.QtCore import *

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
        
class EditorsTest(ModelThreadTestCase):
    """
  Test the basic functionality of the editors :

  - get_value
  - set_value
  - support for ValueLoading
  """

    images_path = static_images_path

    from camelot.view.controls import editors
    from camelot.view.proxy import ValueLoading

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
        editor.set_field_attributes(editable=False)
        self.grab_widget( editor, 'disabled' )
        self.assert_valid_editor( editor, plot )
        
    def test_DateEditor(self):
        import datetime
        editor = self.editors.DateEditor()
        self.assertEqual( editor.get_value(), self.ValueLoading )
        editor.set_value( None )
        self.assertEqual( editor.get_value(), None )
        editor.set_value( datetime.date(1980, 12, 31) )
        self.grab_default_states( editor )
        self.assertEqual( editor.get_value(), datetime.date(1980, 12, 31) )
        self.assert_valid_editor( editor, datetime.date(1980, 12, 31) )

    def test_TextLineEditor(self):
        editor = self.editors.TextLineEditor(parent=None, length=10)
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
        self.assertEqual( editor.get_value(), self.ValueLoading )
        editor.set_value( '/home/lancelot/quests.txt' )
        self.grab_default_states( editor )
        self.assertEqual( editor.get_value(), '/home/lancelot/quests.txt' )
        self.assert_valid_editor( editor, '/home/lancelot/quests.txt' )
        
    def test_StarEditor(self):
        editor = self.editors.StarEditor(parent=None, maximum=5)
        self.assertEqual( editor.get_value(), self.ValueLoading )
        editor.set_value( 4 )
        self.grab_default_states( editor )
        self.assertEqual( editor.get_value(), 4 )
        self.assert_valid_editor( editor, 4 )

    def test_SmileyEditor(self):
        editor = self.editors.SmileyEditor(parent=None)
        self.assertEqual( editor.get_value(), self.ValueLoading )
        editor.set_value( 'face-kiss' )
        self.grab_default_states( editor )
        self.assertEqual( editor.get_value(), 'face-kiss' )
        self.assert_valid_editor( editor, 'face-kiss' )
        
    def test_BoolEditor(self):
        editor = self.editors.BoolEditor(parent=None, editable=False, nullable=True)
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
        self.assertEqual( editor.get_value(), self.ValueLoading )
        editor.set_value( ['XYZ', '123'] )
        self.grab_default_states( editor )
        self.assertEqual( editor.get_value(), ['XYZ', '123'] )
        self.assert_valid_editor( editor, ['XYZ', '123'] )

    def test_ColorEditor(self):
        editor = self.editors.ColorEditor(parent=None, editable=True)
        self.assertEqual( editor.get_value(), self.ValueLoading )
        editor.set_value( (255, 200, 255, 255) )
        self.grab_default_states( editor )
        self.assertEqual( editor.get_value(), (255, 200, 255, 255) )
        self.assert_valid_editor( editor, (255, 200, 255, 255) )

    def test_ColoredFloatEditor(self):
        editor = self.editors.ColoredFloatEditor(parent=None, editable=True)
        self.assertEqual( editor.get_value(), self.ValueLoading )
        editor.set_value( 0.0 )
        self.assertEqual( editor.get_value(), 0.0 )
        editor.set_value( 3.14 )
        self.grab_default_states( editor )
        self.assertEqual( editor.get_value(), 3.14 )
        self.assert_valid_editor( editor, 3.14 )

    def test_ChoicesEditor(self):
        editor = self.editors.ChoicesEditor(parent=None, editable=True)
        choices1 = [(1,u'A'), (2,u'B'), (3,u'C')]
        editor.set_choices( choices1 )
        self.assertEqual( editor.get_value(), self.ValueLoading )
        editor.set_value( 2 )
        self.assertEqual(editor.get_choices(), choices1 )
        self.grab_default_states( editor )
        self.assertEqual( editor.get_value(), 2 )
        # now change the choices
        choices2 = [(4,u'D'), (5,u'E'), (6,u'F')]
        editor.set_choices( choices2 )
        self.assertEqual( editor.get_choices(), choices2 + [(2,u'B')] )
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
        self.assertEqual( editor.get_value(), self.ValueLoading )
        self.grab_default_states( editor )
        self.assert_valid_editor( editor, StoredFile( storage, 'test.txt') )

    def test_DateTimeEditor(self):
        import datetime
        editor = self.editors.DateTimeEditor(parent=None, editable=True)
        self.assertEqual( editor.get_value(), self.ValueLoading )
        editor.set_value( datetime.datetime(2009, 7, 19, 21, 5, 10, 0) )
        self.assertEqual( editor.get_value(), datetime.datetime(2009, 7, 19, 21, 5, 0 ) )
        self.grab_default_states( editor )
        self.assert_valid_editor( editor, datetime.datetime(2009, 7, 19, 21, 5, 0 ) )

    def test_FloatEditor(self):
        editor = self.editors.FloatEditor(parent=None, 
                                          prefix='prefix')
        self.assertEqual( editor.get_value(), self.ValueLoading )
        editor.set_value( 0.0 )
        self.assertEqual( editor.get_value(), 0.0 )
        editor.set_value( 3.14 )
        self.grab_default_states( editor )
        self.assertEqual( editor.get_value(), 3.14 )
        editor = self.editors.FloatEditor(parent=None,  
                                          suffix='suffix')
        self.assertEqual( editor.get_value(), self.ValueLoading )
        editor.set_value( 0.0 )
        self.assertEqual( editor.get_value(), 0.0 )
        editor.set_value( 3.14 )
        self.assertEqual( editor.get_value(), 3.14 )
        editor.set_value( 5.45 )
        editor.set_value( None )
        self.assertEqual( editor.get_value(), None )
        # pretend the user has entered something
        editor.spinBox.setValue( 0.0 )
        self.assertTrue( editor.get_value() != None )
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
        self.assertEqual( editor.get_value(), self.ValueLoading )
        editor.set_value( 'en_US' )
        self.grab_default_states( editor )
        self.assertEqual( editor.get_value(), 'en_US' )
        self.assert_valid_editor( editor, 'en_US' )

    def test_Many2OneEditor(self):
        editor = self.editors.Many2OneEditor(parent=None)
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
        self.assertEqual( editor.get_value(), self.ValueLoading )
        editor.set_value( ('im','test') )
        self.grab_default_states( editor )
        self.assertEqual( editor.get_value(),  ('im','test') )
        self.assert_valid_editor( editor, ('im','test') )

    def test_MonthsEditor(self):
        editor = self.editors.MonthsEditor(parent=None)
        self.assertEqual(editor.get_value(), self.ValueLoading)
        editor.set_value(12)
        self.grab_default_states( editor )
        self.assertEqual(editor.get_value(),  12)
        self.assert_valid_editor( editor, 12 )

from camelot.view import forms

class FormTest(ModelThreadTestCase):

    images_path = static_images_path

    def setUp(self):
        ModelThreadTestCase.setUp(self)
        from camelot.view.controls.formview import FormEditors
        from elixir import entities
        self.entities = [e for e in entities]
        from camelot.admin.application_admin import ApplicationAdmin
        from camelot.view.proxy.queryproxy import QueryTableProxy
        from camelot.model.party import Person
        from camelot_example.model import Movie
        self.app_admin = ApplicationAdmin()
        self.movie_admin = self.app_admin.get_related_admin( Movie )
        
        self.movie_model = QueryTableProxy( self.movie_admin, 
                                            lambda:Movie.query,
                                            self.movie_admin.get_fields )
        
        widget_mapper = QtGui.QDataWidgetMapper()
        widget_mapper.setModel( self.movie_model )
        widget_mapper.setItemDelegate( self.movie_model.getItemDelegate() )
        self.widgets = FormEditors( self.movie_admin.get_fields(),
                                    widget_mapper,
                                    self.movie_model.getItemDelegate(),
                                    self.movie_admin )
        
        self.person_entity = Person
        self.collection_getter = lambda:[Person()]

    def tearDown(self):
        #
        # The global list of entities should remain clean for subsequent tests
        #
        from elixir import entities
        for e in entities:
            if e not in self.entities:
                entities.remove(e)

    def test_form(self):
        from snippet.form.simple_form import Movie
        self.grab_widget(Movie.Admin.form_display.render(self.widgets))

    def test_tab_form(self):
        form = forms.TabForm([('First tab', ['title', 'short_description']),
                              ('Second tab', ['director', 'releasedate'])])
        self.grab_widget(form.render(self.widgets))

    def test_group_box_form(self):
        form = forms.GroupBoxForm('Movie', ['title', 'short_description'])
        self.grab_widget(form.render(self.widgets))

    def test_grid_form(self):
        form = forms.GridForm([['title', 'short_description'], ['director','releasedate']])
        self.grab_widget(form.render(self.widgets))

    def test_vbox_form(self):
        form = forms.VBoxForm([['title', 'short_description'], ['director', 'releasedate']])
        self.grab_widget(form.render(self.widgets))

    def test_hbox_form(self):
        form = forms.HBoxForm([['title', 'short_description'], ['director', 'releasedate']])
        self.grab_widget(form.render(self.widgets))

    def test_nested_form(self):
        from snippet.form.nested_form import Admin
        person_admin = Admin(self.app_admin, self.person_entity)
        self.grab_widget( person_admin.create_new_view() )

    def test_inherited_form(self):
        from snippet.form.inherited_form import InheritedAdmin
        person_admin = InheritedAdmin(self.app_admin, self.person_entity)
        self.grab_widget( person_admin.create_new_view() )

    def test_custom_layout(self):
        from snippet.form.custom_layout import Admin
        person_admin = Admin(self.app_admin, self.person_entity)
        self.grab_widget( person_admin.create_new_view() )

class DelegateTest(ModelThreadTestCase):
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
        from PyQt4.QtCore import Qt

        model = QStandardItemModel(1, 1)
        index = model.index(0, 0, QModelIndex())
        model.setData( index, QtCore.QVariant( data ) )
        model.setData( index, QtCore.QVariant( QtGui.QColor('white') ), Qt.BackgroundRole )
        model.setData( index, QtCore.QVariant( dict(editable=True) ), Qt.UserRole )

        option = QtGui.QStyleOptionViewItem()

        if suffix == 'editable':
            self.assertTrue(delegate.sizeHint(option, index).height()>1)

        tableview = TableWidget()
        tableview.setModel(model)
        tableview.setItemDelegate(delegate)

        test_case_name = sys._getframe(1).f_code.co_name[4:]

        for state_name, state in zip(('selected', 'unselected'),
                                     (QStyle.State_Selected, QStyle.State_None)):
            tableview.adjustSize()

            if state == QStyle.State_Selected:
                tableview.selectionModel().select(index, QItemSelectionModel.Select)
            else:
                tableview.selectionModel().select(index, QItemSelectionModel.Clear)

            cell_size = tableview.visualRect(index).size()

            headers_size = QSize(tableview.verticalHeader().width(),
                                 tableview.horizontalHeader().height())

            tableview.setHorizontalScrollBarPolicy( Qt.ScrollBarAlwaysOff )
            tableview.setVerticalScrollBarPolicy( Qt.ScrollBarAlwaysOff )

            tableview.resize(cell_size + headers_size)

            # TODO checks if path exists
            delegate_images_path = os.path.join(static_images_path, 'delegates')
            if not os.path.exists(delegate_images_path):
                os.makedirs(delegate_images_path)
            pixmap = QPixmap.grabWidget(tableview)
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
        from camelot.core.constants import camelot_minfloat, camelot_maxfloat
        delegate = self.delegates.FloatDelegate(parent=None, suffix='euro', editable=True)
        editor = delegate.createEditor(None, self.option, None)
        self.assertTrue(isinstance(editor, self.editors.FloatEditor))
        self.assertEqual(editor.spinBox.minimum(), camelot_minfloat)
        self.assertEqual(editor.spinBox.maximum(), camelot_maxfloat)
        self.grab_delegate(delegate, 3.145)
        delegate = self.delegates.FloatDelegate(parent=None, prefix='prefix', editable=False)
        editor = delegate.createEditor(None, self.option, None)
        self.assertTrue(isinstance(editor, self.editors.FloatEditor))
        self.assertEqual(editor.spinBox.minimum(), camelot_minfloat)
        self.assertEqual(editor.spinBox.maximum(), camelot_maxfloat)
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


class FilterTest(ModelThreadTestCase):
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
        table_view.set_filters_and_actions( (items, None) )

class ControlsTest(ModelThreadTestCase):
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
        
    def test_small_column( self ):
        #create a table view for an Admin interface with small columns
        from camelot.view.controls.tableview import TableView
        from camelot.model.party import Person
        
        class SmallColumnsAdmin( Person.Admin ):
            list_display = ['first_name', 'suffix']
            
        admin = SmallColumnsAdmin( self.app_admin, Person )
        widget = TableView( self.gui_context, 
                            admin )
        self.grab_widget( widget )
        model = widget.table.model()
        header = widget.table.horizontalHeader()

        first_name_width = model.headerData( 0, Qt.Horizontal, Qt.SizeHintRole ).toSize().width()
        suffix_width = model.headerData( 1, Qt.Horizontal, Qt.SizeHintRole ).toSize().width()
        
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
        widget = TableView( self.gui_context, 
                            admin )
        self.grab_widget( widget )
        model = widget.table.model()
        header = widget.table.horizontalHeader()

        first_name_width = model.headerData( 0, Qt.Horizontal, Qt.SizeHintRole ).toSize().width()
        suffix_width = model.headerData( 1, Qt.Horizontal, Qt.SizeHintRole ).toSize().width()
        
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
        
    def test_navigation_pane(self):
        from camelot.view.controls import navpane2
        self.wait_for_animation()
        widget = navpane2.NavigationPane( self.app_admin,
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
        try:
            #begin user_exception
            from camelot.core.exception import UserException

            raise UserException( text = "Could not burn movie to non empty DVD",
                                 resolution = "Insert an empty DVD and retry" )
            #end user_exception
        except Exception, e:
            pass

        exc_info = register_exception(logger, 'unit test', e)
        dialog = ExceptionDialog( exc_info )
        self.grab_widget( dialog )   

class CamelotEntityViewsTest(EntityViewsTest):
    """Test the views of all the Entity subclasses"""

    images_path = static_images_path

class SnippetsTest(ModelThreadTestCase):

    images_path = static_images_path

    def setUp( self ):
        super( SnippetsTest, self ).setUp()
        from camelot.admin.application_admin import ApplicationAdmin
        self.app_admin = ApplicationAdmin()
        
    def test_simple_plot(self):
        from snippet.chart.simple_plot import Wave
        from camelot.view.proxy.collection_proxy import CollectionProxy
        wave = Wave()
        admin = Wave.Admin( self.app_admin, Wave )
        proxy = CollectionProxy(admin, lambda:[wave], admin.get_fields )
        form = admin.create_form_view('Wave', proxy, 0, None)
        form.setMaximumSize( 400, 200 )
        self.grab_widget(form)

    def test_advanced_plot(self):
        from snippet.chart.advanced_plot import Wave
        from camelot.view.proxy.collection_proxy import CollectionProxy
        wave = Wave()
        #wave.phase = '2.89'
        admin = Wave.Admin( self.app_admin, Wave )
        proxy = CollectionProxy(admin, lambda:[wave], admin.get_fields )
        form = admin.create_form_view('Wave', proxy, 0, None)
        form.setMaximumSize( 400, 200 )
        self.grab_widget(form)
        
    def test_fields_with_actions(self):
        from snippet.fields_with_actions import Coordinate
        from camelot.view.proxy.collection_proxy import CollectionProxy
        coordinate = Coordinate()
        admin = Coordinate.Admin( self.app_admin, Coordinate )
        proxy = CollectionProxy(admin, lambda:[coordinate], admin.get_fields )
        form = admin.create_form_view('Coordinate', proxy, 0, None)
        self.grab_widget(form)

    def test_fields_with_tooltips(self):
        from snippet.fields_with_tooltips import Coordinate
        from camelot.view.proxy.collection_proxy import CollectionProxy
        coordinate = Coordinate()
        admin = Coordinate.Admin( self.app_admin, Coordinate )
        proxy = CollectionProxy(admin, lambda:[coordinate], admin.get_fields )
        form = admin.create_form_view('Coordinate', proxy, 0, None)
        self.grab_widget(form)

    def test_entity_validator(self):
        from camelot.view.proxy.collection_proxy import CollectionProxy
        from camelot.model.party import Person
        from snippet.entity_validator import PersonValidator, Admin
        person_admin = Admin( self.app_admin, Person)
        proxy = CollectionProxy(person_admin, lambda:[Person()], person_admin.get_columns)
        validator = PersonValidator(person_admin, proxy)
        self.mt.post(lambda:validator.isValid(0))
        self.process()
        self.assertEqual(len(validator.validityMessages(0)), 3)
        self.grab_widget(validator.validityDialog(0, parent=None))

    def test_background_color(self):
        from camelot.view.proxy.collection_proxy import CollectionProxy
        from camelot.model.party import Person
        from snippet.background_color import Admin
        person_admin = Admin( self.app_admin, Person )
        proxy = CollectionProxy(person_admin, lambda:[Person(first_name='John', last_name='Cleese'),
                                                      Person(first_name='eric', last_name='Idle')],
                                                       person_admin.get_columns)
        from camelot.view.controls.editors.one2manyeditor import One2ManyEditor
        editor = One2ManyEditor(admin=person_admin)
        editor.set_value(proxy)
        self.process()
        self.grab_widget(editor)
