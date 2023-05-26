import datetime
import io
import logging
import os
import unittest
import openpyxl
import itertools

import camelot.types

from camelot.core.dataclasses import dataclass
from camelot.core.exception import UserException
from camelot.core.naming import initial_naming_context
from camelot.core.item_model import ObjectRole
from camelot.core.item_model.query_proxy import QueryModelProxy
from camelot.admin.action import Action, ActionStep, State, GuiContext
from camelot.admin.action import (
    list_action, application_action, form_action, list_filter, Mode
)
from camelot.admin.action import export_mapping
from camelot.admin.action.logging import ChangeLogging
from camelot.admin.action.field_action import DetachFile, SelectObject, UploadFile, add_existing_object
from camelot.admin.action.list_action import SetFilters
from camelot.admin.model_context import ObjectsModelContext
from camelot.admin.application_admin import ApplicationAdmin
from camelot.admin.icon import CompletionValue
from camelot.admin.entity_admin import EntityAdmin
from camelot.core.qt import QtCore, QtGui, QtWidgets, Qt, delete, is_deleted
from camelot.core.orm import EntityBase, Session
from camelot.core.utils import ugettext_lazy as _
from camelot.model.party import Person
from camelot.test import GrabMixinCase, RunningProcessCase, test_context
from camelot.test.action import MockModelContext
from camelot.view import action_steps, import_utils, utils, gui_naming_context
from camelot.view.action_runner import hide_progress_dialog
from camelot.view.action_steps import SelectItem
from camelot.view.action_steps.change_object import ChangeObject
from camelot.view.controls.action_widget import AbstractActionWidget
from camelot.view.controls import delegates
from camelot.view.controls.formview import FormView
from camelot.view.controls.editors.one2manyeditor import One2ManyEditor
from camelot.view.forms import Form
from camelot.view.crud_action import UpdateMixin
from camelot.view.import_utils import (ColumnMapping, ColumnMappingAdmin, MatchNames)
from camelot.view.qml_view import get_qml_root_backend
from camelot_example.importer import ImportCovers
from camelot_example.model import Movie, Tag

from sqlalchemy import MetaData, orm, schema, types
from sqlalchemy.ext.declarative import declarative_base

from . import app_admin, test_core, test_view, unit_test_context
from .test_item_model import QueryQStandardItemModelMixinCase, setup_query_proxy_name
from .test_orm import TestMetaData, EntityMetaMock
from .test_model import (
    ExampleModelMixinCase, LoadSampleData,
    load_sample_data_name, setup_session_name, dirty_session_action_name,
    setup_sample_model_name
)

test_images = [os.path.join( os.path.dirname(__file__), '..', 'camelot_example', 'media', 'covers', 'circus.png') ]

LOGGER = logging.getLogger(__name__)
context_counter = itertools.count()

class SerializableMixinCase(object):

    def _write_read(self, step):
        """
        Serialize and deserialize an object, return the deserialized object
        """
        stream = io.BytesIO()
        step.write_object(stream)
        stream.seek(0)
        step_type = type(step)
        deserialized_object = step_type.__new__(step_type)
        deserialized_object.read_object(stream)
        return deserialized_object

class CustomAction(Action):
    name = 'custom_test_action'
    verbose_name = 'Custom Action'
    shortcut = QtGui.QKeySequence.StandardKey.New
    modes = [
        Mode('mode_1', _('First mode')),
        Mode('mode_2', _('Second mode')),
    ]


custom_action_name = test_context.bind((CustomAction.name,), CustomAction())


class ActionBaseCase(RunningProcessCase, SerializableMixinCase):

    model_context_name = ('constant', 'null')

    def setUp(self):
        super().setUp()
        self.admin_route = app_admin.get_admin_route()
        self.gui_context_obj = GuiContext()
        self.gui_context_name = gui_naming_context.bind(
            ('transient', str(id(self.gui_context_obj))), self.gui_context_obj
        )

    def test_action_step(self):
        ActionStep()

    def test_action(self):
        self.gui_run(custom_action_name, self.gui_context_name, 'mode_1')
        state = self.get_state(custom_action_name, self.gui_context_name)
        self.assertTrue(state['verbose_name'])
        self.assertTrue(len(state['modes']))


class ActionWidgetsCase(unittest.TestCase, GrabMixinCase):
    """Test widgets related to actions.
    """

    images_path = test_view.static_images_path

    @classmethod
    def setUpClass(cls):
        cls.action = ImportCovers()
        cls.action_name = initial_naming_context.bind(('import_covers',), cls.action)

    def setUp(self):
        get_qml_root_backend().setVisible(True, False)
        self.gui_context_obj = GuiContext()
        self.gui_context = gui_naming_context.bind(
            ('transient', str(id(self.gui_context_obj))), self.gui_context_obj
        )
        self.parent = QtWidgets.QWidget()
        enabled = State()
        disabled = State()
        disabled.enabled = False
        notification = State()
        notification.notification = True
        self.states = [ ( 'enabled', enabled),
                        ( 'disabled', disabled),
                        ( 'notification', notification) ]

    def grab_widget_states( self, widget, suffix ):
        for state_name, state in self.states:
            AbstractActionWidget.set_pushbutton_state(
                widget, state._to_dict(), None, None
            )
            self.grab_widget( widget, suffix='%s_%s'%( suffix,
                                                       state_name ) )

    def test_action_push_botton( self ):
        widget = QtWidgets.QPushButton()
        self.grab_widget_states( widget, 'application' )

    def test_hide_progress_dialog( self ):
        dialog = self.gui_context_obj.get_progress_dialog()
        dialog.show()
        with hide_progress_dialog(self.gui_context):
            self.assertTrue( dialog.isHidden() )
        self.assertFalse( dialog.isHidden() )

# begin select item
class SendDocumentAction( Action ):

    def model_run( self, model_context, mode ):
        methods = [
            CompletionValue(
                initial_naming_context._bind_object('email'),
                'By E-mail'),
            CompletionValue(
                initial_naming_context._bind_object('email'),
                'By Fax'),
            CompletionValue(
                initial_naming_context._bind_object('email'),
                'By postal mail')
        ]
        method = yield SelectItem(
            methods,
            value=initial_naming_context._bind_object('email')
        )
        # handle sending of the document
        LOGGER.info('selected {}'.format(method))

# end select item

send_document_action_name = unit_test_context.bind(('send_document_action',), SendDocumentAction())

class ActionStepsCase(RunningProcessCase, GrabMixinCase, ExampleModelMixinCase, SerializableMixinCase):
    """Test the various steps that can be executed during an
    action.
    """

    model_context_name = ('constant', 'null')
    images_path = test_view.static_images_path

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.gui_run(setup_sample_model_name)
        cls.gui_run(load_sample_data_name, mode=True)

    def setUp(self):
        super(ActionStepsCase, self).setUp()
        get_qml_root_backend().setVisible(True, False)
        self.admin_route = app_admin.get_admin_route()
        self.gui_context = ('cpp_gui_context', 'root_backend')

    def test_change_object(self):

        @dataclass
        class Options(object):
            name: str

        admin = app_admin.get_related_admin(Options)
        options = Options('Videostore')
        change_object = ChangeObject(options, admin)
        dialog = change_object.render(
            self.gui_context, change_object._to_dict()
        )
        self.grab_widget(dialog)

    def test_select_file( self ):
        action_steps.SelectFile('Image Files (*.png *.jpg);;All Files (*)')

    def test_select_item( self ):
        step = self.gui_run(
            send_document_action_name,
            self.gui_context,
            model_context_name=self.model_context_name
        )[-2]
        self.assertEqual(step[0], SelectItem.__name__)
        dialog = SelectItem.render(step[1])
        self.grab_widget(dialog)
        self.assertTrue(dialog)

    def test_open_file( self ):
        stream = io.BytesIO(b'1, 2, 3, 4')
        open_stream = action_steps.OpenStream( stream, suffix='.csv' )
        self.assertTrue( str( open_stream ) )
        action_steps.OpenString(b'1, 2, 3, 4')
        context = { 'columns':['width', 'height'],
                    'table':[[1,2],[3,4]] }
        action_steps.WordJinjaTemplate( 'list.html', context )

    def test_update_progress( self ):
        update_progress = action_steps.UpdateProgress(
            20, 100, _('Importing data')
        )
        self.assertTrue( str( update_progress ) )
        update_progress = self._write_read(update_progress)
        update_progress.gui_run(self.gui_context, update_progress._to_bytes())

    def test_message_box( self ):
        step = action_steps.MessageBox('Hello World')
        serialized_step = step._to_dict()
        dialog = step.render(serialized_step)
        dialog.show()
        self.grab_widget(dialog)

group_box_filter_name = unit_test_context.bind(('group_box',), list_filter.GroupBoxFilter(Person.last_name, exclusive=True))
combo_box_filter_name = unit_test_context.bind(('combo_box',), list_filter.ComboBoxFilter(Person.last_name))
to_first_row_name = unit_test_context.bind(('to_first_row',), list_action.ToFirstRow())
to_last_row_name = unit_test_context.bind(('to_last_row',), list_action.ToLastRow())
export_spreadsheet_name = unit_test_context.bind(('export_spreadsheet',), list_action.ExportSpreadsheet())
import_from_file_name = unit_test_context.bind(('import_from_file',), list_action.ImportFromFile())
set_filters_name = unit_test_context.bind(('set_filters',), list_action.SetFilters())
open_form_view_name = unit_test_context.bind(('open_form_view',), list_action.OpenFormView())
remove_selection_name = unit_test_context.bind(('remove_selection',), list_action.RemoveSelection())


class ModelContextAction(Action):
    name = 'model_context_action'
    verbose_name = 'Model context methods'

    def model_run(model_context, mode):
        for obj in model_context.get_collection():
            yield action_steps.UpdateProgress('obj in collection {}'.format(obj))
        for obj in model_context.get_selection():
            yield action_steps.UpdateProgress('obj in selection {}'.format(obj))
        model_context.get_object()

model_context_action_name = test_context.bind((ModelContextAction.name,), ModelContextAction())



class ListActionsCase(
    RunningProcessCase,
    GrabMixinCase, ExampleModelMixinCase, QueryQStandardItemModelMixinCase):
    """Test the standard list actions.
    """

    images_path = test_view.static_images_path

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.gui_run(setup_sample_model_name, ('constant', 'null'), mode=True)
        cls.gui_run(load_sample_data_name, mode=True)

    def setUp( self ):
        super(ListActionsCase, self).setUp()
        self.model_context_name = ('test_list_actions_model_context_{0}'.format(next(context_counter)),)
        self.gui_run(setup_session_name, mode=True)
        self.gui_run(setup_query_proxy_name, mode=self.model_context_name)
        self.admin = app_admin.get_related_admin(Person)
        self.admin_route = self.admin.get_admin_route()
        self.setup_item_model(self.admin_route, self.admin.get_name())
        self.movie_admin = app_admin.get_related_admin(Movie)
        # make sure the model has rows and header data
        self._load_data(self.item_model)
        self.view = One2ManyEditor(admin_route=self.admin_route)
        table_view = self.view.item_view
        table_view.setModel(self.item_model)
        self.gui_context = self.view.list_gui_context_name
        
        # select the first row
        table_view.setCurrentIndex(self.item_model.index(0, 0))
        # Make sure to ChangeSelection action step is executed
        self.item_model.onTimeout()
        # create a model context
        self.example_folder = os.path.join( os.path.dirname(__file__), '..', 'camelot_example' )

    def tearDown( self ):
        Session().expunge_all()
        if not is_deleted(self.qt_parent):
            delete(self.qt_parent)
        self.qt_parent = None
        self.item_model = None

    def test_model_context(self):
        list(self.gui_run(model_context_action_name, self.gui_context, None, model_context_name=self.model_context_name))

    def test_change_row_actions( self ):
        # FIXME: this unit test does not work with the new ToFirstRow/ToNextRow action steps...
        # the state does not change when the current row changes,
        # to make the actions usable in the main window toolbar
        list(self.gui_run(to_first_row_name, self.gui_context, None, model_context_name=self.model_context_name))
        #self.assertFalse( get_state( to_last ).enabled )
        #self.assertFalse( get_state( to_next ).enabled )
        list(self.gui_run(to_last_row_name, self.gui_context, None, model_context_name=self.model_context_name))
        #self.assertFalse( get_state( to_first ).enabled )
        #self.assertFalse( get_state( to_previous ).enabled )

    def test_export_spreadsheet( self ):
        for step in self.gui_run(export_spreadsheet_name, self.gui_context, None, model_context_name=self.model_context_name):
            if step[0] == 'OpenFile':
                filename = step[1]["path"]
        self.assertTrue(filename)
        # see if the generated file can be parsed
        openpyxl.load_workbook(filename)

    def test_save_restore_export_mapping(self):
        admin = app_admin.get_related_admin(Movie)

        settings = utils.get_settings(admin.get_admin_route()[-1])
        settings.beginGroup('export_mapping')
        # make sure there are no previous settings
        settings.remove('')

        save_export_mapping = export_mapping.SaveExportMapping(settings)
        restore_export_mapping = export_mapping.RestoreExportMapping(settings)

        model_context = MockModelContext()
        
        field_choices = [('field_{0}'.format(i), 'Field {0}'.format(i)) for i in range(10)]
        model_context.admin = import_utils.ColumnSelectionAdmin(
            admin,
            field_choices = field_choices
        )
        model_context.selection = [import_utils.ColumnMapping(0, [], 'field_1'),
                                   import_utils.ColumnMapping(1, [], 'field_2')]

        for step in save_export_mapping.model_run(model_context, None):
            if isinstance(step, action_steps.ChangeObject):
                options = step.get_object()
                options.name = 'mapping 1'

        stored_mappings = settings.beginReadArray('mappings')
        settings.endArray()
        self.assertTrue(stored_mappings)

        mappings = save_export_mapping.read_mappings()
        self.assertTrue('mapping 1' in mappings)
        self.assertEqual(mappings['mapping 1'], ['field_1', 'field_2'])

        model_context.selection =  [import_utils.ColumnMapping(0, [], 'field_3'),
                                   import_utils.ColumnMapping(1, [], 'field_4')]

        generator = restore_export_mapping.model_run(model_context, None)
        for step in generator:
            if isinstance(step, action_steps.SelectItem):
                generator.send(step.items[1].value)

        self.assertEqual(model_context.selection[0].field, 'field_1')

    def test_match_names(self):
        rows = [
            ['first_name', 'last_name'],
            ['Unknown',    'Unknown'],
        ]
        fields = self.admin.get_columns()
        mapping = ColumnMapping(0, rows)
        self.assertNotEqual(mapping.field, 'first_name' )
        
        match_names = MatchNames()
        model_context = MockModelContext()
        model_context.obj = mapping
        model_context.admin = ColumnMappingAdmin(
            self.admin,
            field_choices=[(f,f) for f in fields]
        )
        list(match_names.model_run(model_context, None))
        self.assertEqual(mapping.field, 'first_name')

    def test_import_from_xls_file( self ):
        exception_step, pop_progress_step = self.test_import_from_file('import_example.xls')[-2:]
        self.assertEqual(exception_step[0], action_steps.MessageBox.__name__)
        self.assertIn('xls is not a supported', exception_step[1]['text'])
        self.assertEqual(pop_progress_step[0], action_steps.PopProgressLevel.__name__)

    def test_import_from_xlsx_file( self ):
        self.test_import_from_file( 'import_example.xlsx' )

    def test_import_from_xlsx_formats( self ):
        reader = import_utils.XlsReader(os.path.join(
            self.example_folder, 'excel_formats_example.xlsx'
        ))
        rows = [row for row in reader]
        self.assertEqual(len(rows), 1)
        row = rows[0]
        self.assertEqual(utils.string_from_string(row[0]), u'Test')
        self.assertEqual(utils.date_from_string(row[1]), datetime.date(2017,4,1))
        self.assertEqual(utils.int_from_string(row[2]), 234567)
        self.assertEqual(utils.float_from_string(row[3]), 3.15)
        self.assertEqual(utils.float_from_string(row[4]), 3.145)
        self.assertEqual(utils.bool_from_string(row[5]), True)
        self.assertEqual(utils.bool_from_string(row[6]), False)

    def test_import_from_file(self, filename='import_example.csv'):
        replies = {
            action_steps.SelectFile: [os.path.join(self.example_folder, filename)]
        }
        steps = self.gui_run(import_from_file_name, self.gui_context, None, replies, model_context_name=self.model_context_name)
        for step in steps:
            if isinstance(step, action_steps.ChangeObject):
                dialog = step.render(self.gui_context)
                dialog.show()
                self.grab_widget(dialog, suffix='column_selection')
            if isinstance(step, action_steps.ChangeObjects):
                dialog = step.render()
                dialog.show()
                self.grab_widget(dialog, suffix='preview')
            if isinstance(step, action_steps.MessageBox):
                dialog = step.render()
                dialog.show()
                self.grab_widget(dialog, suffix='confirmation')
        return steps

    def test_replace_field_contents( self ):
        action = list_action.ReplaceFieldContents()
        proxy = QueryModelProxy(Session().query(Person))
        person_model_context = ObjectsModelContext(
            app_admin.get_related_admin(Person), proxy, QtCore.QLocale()
        )
        steps = action.model_run(person_model_context, 'first_name')
        for step in steps:
            if isinstance(step, ChangeObject):
                field_value = step.get_object()
                field_value.value = 'known'

    def test_open_form_view( self ):
        # sort and filter the original model
        item_view = self.view.item_view
        list_model = item_view.model()
        list_model.sort(1, Qt.SortOrder.DescendingOrder)
        list_model.onTimeout()
        self.process()
        list_model.headerData(0, Qt.Orientation.Vertical, ObjectRole)
        list_model.data(list_model.index(0, 0), Qt.ItemDataRole.DisplayRole)
        list_model.onTimeout()
        self.process()
        self.view.item_view.setCurrentIndex(list_model.index(0, 0))
        for step_name, step in self.gui_run(open_form_view_name, self.gui_context,None, model_context_name=self.model_context_name):
            if step_name == action_steps.OpenFormView.__name__:
                form = action_steps.OpenFormView.render(self.gui_context, step)
                form_value = form.model.value()
        self.assertTrue(isinstance(form_value, list))

    @staticmethod
    def track_crud_steps(action, model_context):
        created, updated = [], []
        steps = []
        for step in action.model_run(model_context, None):
            steps.append(type(step))
            if isinstance(step, action_steps.CreateObjects):
                created.extend(initial_naming_context.resolve(step.created) if step.created else [])
            elif isinstance(step, action_steps.UpdateObjects):
                updated.extend(initial_naming_context.resolve(step.updated) if step.updated else [])
        return steps, created, updated

    def test_remove_selection(self):
        list(self.gui_run(
            remove_selection_name, self.gui_context,
            None, model_context_name=self.model_context_name
        ))

    def test_move_rank_up_down(self):
        metadata = MetaData()
        Entity = declarative_base(cls = EntityBase,
                                  metadata = metadata,
                                  metaclass = EntityMetaMock,
                                  class_registry = dict(),
                                  constructor = None,
                                  name = 'Entity' )
        metadata.bind = 'sqlite://'
        session = Session()

        class A(Entity):

            rank = schema.Column(types.Integer, nullable=False)
            type = schema.Column(types.Unicode, nullable=False)

            __entity_args__ = {
                'ranked_by': (rank, type)
            }

            class Admin(EntityAdmin):
                pass

        metadata.create_all()

        proxy = QueryModelProxy(session.query(Person))
        person_model_context = ObjectsModelContext(
            app_admin.get_related_admin(Person), proxy, QtCore.QLocale()
        )

        # The actions should not be present in the related toolbar actions of the entity if its not rank-based.
        related_toolbar_actions = [action.route[-1] for action in person_model_context.admin.get_related_toolbar_actions('onetomany')]
        self.assertNotIn(list_action.move_rank_up.name, related_toolbar_actions)
        self.assertNotIn(list_action.move_rank_down.name, related_toolbar_actions)
        # If the action is run on a non rank-based entity anyways, an assertion should block it.
        for action in (list_action.move_rank_up, list_action.move_rank_down):
            with self.assertRaises(AssertionError) as exc:
                list(action.model_run(person_model_context, None))
            self.assertEqual(str(exc.exception), action.Message.entity_not_rank_based.value.format(person_model_context.admin.entity))

        # The action should be present on a rank-based entity:
        admin = app_admin.get_related_admin(A)
        related_toolbar_actions = [action.route[-1] for action in admin.get_related_toolbar_actions('onetomany')]
        self.assertIn(list_action.move_rank_up.name, related_toolbar_actions)
        self.assertIn(list_action.move_rank_down.name, related_toolbar_actions)

        # The action should raise an exception if no single line is selected:
        ax1 = A(type='x', rank=1)
        ax2 = A(type='x', rank=2)
        ax3 = A(type='x', rank=3)
        ay1 = A(type='y', rank=1)
        session.flush()
        model_context = ObjectsModelContext(
            admin, admin.get_proxy([ax1, ax2, ay1, ax3]), None
        )
        model_context.collection_count = 4
        for action in (list_action.move_rank_up, list_action.move_rank_down):
            with self.assertRaises(UserException) as exc:
                list(action.model_run(model_context, None))
            self.assertEqual(exc.exception.text, action.Message.no_single_selection.value)
        model_context.selected_rows = [(0,1)]
        model_context.selection_count = 2
        for action in (list_action.move_rank_up, list_action.move_rank_down):
            with self.assertRaises(UserException) as exc:
                list(action.model_run(model_context, None))
            self.assertEqual(exc.exception.text, action.Message.no_single_selection.value)

        # A single selected line should work:
        model_context.selected_rows = [(0,0)]
        model_context.selection_count = 1
        # Move down with at least two rank-compatible objects with a lower rank and verify
        # the one directly lower is taken:
        list(list_action.move_rank_down.model_run(model_context, None))
        self.assertEqual(ax1.rank, 2)
        self.assertEqual(ax2.rank, 1)
        self.assertEqual(ax3.rank, 3)
        # Move down again:
        list(list_action.move_rank_down.model_run(model_context, None))
        self.assertEqual(ax1.rank, 3)
        self.assertEqual(ax2.rank, 1)
        self.assertEqual(ax3.rank, 2)
        # Now test switching back up:
        list(list_action.move_rank_up.model_run(model_context, None))
        self.assertEqual(ax1.rank, 2)
        self.assertEqual(ax2.rank, 1)
        self.assertEqual(ax3.rank, 3)
        list(list_action.move_rank_up.model_run(model_context, None))
        self.assertEqual(ax1.rank, 1)
        self.assertEqual(ax2.rank, 2)
        self.assertEqual(ax3.rank, 3)
        # The action should not switch ranks if no compatible objects are defined, e.g.:
        # * Trying to move up with already highest rank
        list(list_action.move_rank_up.model_run(model_context, None))
        self.assertEqual(ax1.rank, 1)
        self.assertEqual(ax2.rank, 2)
        self.assertEqual(ax3.rank, 3)
        model_context.selected_rows = [(3,3)]
        # * Trying to move down with already lowest rank
        list(list_action.move_rank_down.model_run(model_context, None))
        self.assertEqual(ax1.rank, 1)
        self.assertEqual(ax2.rank, 2)
        self.assertEqual(ax3.rank, 3)

        metadata.drop_all()
        metadata.clear()

    def test_set_filters(self):
        set_filters_step = yield SetFilters()
        state = self.get_state(set_filters_step, self.gui_context)
        self.assertTrue(len(state.modes))
        mode_names = set(m.name for m in state.modes)
        self.assertIn('first_name', mode_names)
        self.assertNotIn('note', mode_names)
        self.gui_run(set_filters_name, self.gui_context, set_filters_step[1], model_context_name=self.model_context_name)
        #steps = self.gui_run(set_filters, self.gui_context)
        #for step in steps:
            #if isinstance(step, action_steps.ChangeField):
                #steps.send(('first_name', 'test'))

    def test_group_box_filter(self):
        state = self.get_state(group_box_filter_name, self.gui_context)
        self.assertTrue(len(state['modes']))
        self.gui_run(group_box_filter_name, self.gui_context, state['modes'][0]['value'], model_context_name=self.model_context_name)

    def test_combo_box_filter(self):
        state = self.get_state(combo_box_filter_name, self.gui_context)
        self.assertTrue(len(state['modes']))
        widget = self.view.render_action(
            list_filter.ComboBoxFilter.render_hint, combo_box_filter_name,
            self.view, None
        )
        AbstractActionWidget.set_combobox_state(widget, state)
        self.assertTrue(widget.count())
        self.gui_run(combo_box_filter_name, self.gui_context, state['modes'][0]['value'], model_context_name=self.model_context_name)
        self.grab_widget(widget)


close_form_name = unit_test_context.bind(('close_form',), form_action.CloseForm())
to_previous_form_name = unit_test_context.bind(('to_previous_form',), form_action.ToPreviousForm())
to_next_form_name = unit_test_context.bind(('to_next_form',), form_action.ToNextForm())
to_first_form_name = unit_test_context.bind(('to_first_form',), form_action.ToFirstForm())
to_last_form_name = unit_test_context.bind(('to_last_form',), form_action.ToLastForm())

class FormActionsCase(
    RunningProcessCase,
    ExampleModelMixinCase, GrabMixinCase, QueryQStandardItemModelMixinCase):
    """Test the standard list actions.
    """

    images_path = test_view.static_images_path

    @classmethod
    def setUpClass(cls):
        super(FormActionsCase, cls).setUpClass()
        cls.gui_run(setup_sample_model_name, ('constant', 'null'), mode=True)
        cls.gui_run(load_sample_data_name, ('constant', 'null'), mode=True)

    def setUp( self ):
        super(FormActionsCase, self).setUp()
        self.model_context_name = ('test_form_actions_model_context_{0}'.format(next(context_counter)),)
        self.gui_run(setup_query_proxy_name, mode=self.model_context_name)
        person_admin = app_admin.get_related_admin(Person)
        self.admin_route = person_admin.get_admin_route()
        self.setup_item_model(self.admin_route, person_admin.get_name())
        self.form_view = FormView()
        self.form_view.setup(
            'Test form', self.admin_route, tuple(), self.item_model,
            Form([])._to_dict(), {}, 0
        )
        self.gui_context_name = self.form_view.gui_context_name

    def tearDown(self):
        self.tear_down_item_model()
        super().tearDown()

    def test_previous_next( self ):
        list(self.gui_run(to_previous_form_name, self.gui_context_name, model_context_name=self.model_context_name))
        list(self.gui_run(to_next_form_name, self.gui_context_name, model_context_name=self.model_context_name))
        list(self.gui_run(to_first_form_name, self.gui_context_name, model_context_name=self.model_context_name))
        list(self.gui_run(to_last_form_name, self.gui_context_name, model_context_name=self.model_context_name))

    def test_close_form( self ):
        list(self.gui_run(close_form_name, self.gui_context_name, model_context_name=self.model_context_name))


backup_action_name = unit_test_context.bind(('backup',), application_action.Backup())
restore_action_name = unit_test_context.bind(('restore',), application_action.Restore())
change_logging_action_name = unit_test_context.bind(('change_logging',), ChangeLogging())
segmentation_fault_action_name = unit_test_context.bind(('segmentation_fault',), application_action.SegmentationFault())
refresh_action_name = unit_test_context.bind(('refresh',), application_action.Refresh())
        
class ApplicationActionsCase(
    RunningProcessCase, GrabMixinCase, ExampleModelMixinCase
    ):
    """Test application actions.
    """

    images_path = test_view.static_images_path
    model_context_name = ('constant', 'null')

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.gui_run(setup_sample_model_name, ('constant', 'null'), mode=True)
        cls.gui_run(load_sample_data_name, ('constant', 'null'), mode=True)

    def setUp(self):
        super( ApplicationActionsCase, self ).setUp()
        self.context = MockModelContext(session=Session())
        self.context.admin = app_admin
        self.gui_context = ('cpp_gui_context', 'root_backend')

    def test_refresh(self):
        self.gui_run(dirty_session_action_name, ('constant', 'null'), mode=True)
        #
        # refresh the session through the action
        #
        generator = self.gui_run(refresh_action_name, self.gui_context, None)
        for step in generator:
            if isinstance(step, tuple) and step[0] == 'UpdateObjects':
                updates = step[1]['updated']
        self.assertTrue(len(updates))

    def test_select_profile(self):
        profile_case = test_core.ProfileCase('setUp')
        profile_case.setUp()
        profile_store = profile_case.test_profile_store()
        action = application_action.SelectProfileMixin()
        generator = action.select_profile(profile_store, app_admin)
        for step in generator:
            if isinstance(step, action_steps.SelectItem):
                generator.send(step.items[1].value)
                profile_selected = True
        self.assertTrue(profile_selected)

    def test_backup_and_restore( self ):
        replies = {action_steps.SaveFile: 'unittest-backup.db'}
        generator = self.gui_run(backup_action_name, self.gui_context, None, replies)
        file_saved = False
        for step in generator:
            if isinstance(step, tuple) and step[0] == 'SaveFile':
                file_saved = True
        self.assertTrue(file_saved)
        replies = {action_steps.SelectFile: ['unittest-backup.db']}
        generator = self.gui_run(restore_action_name, self.gui_context, None, replies)
        file_selected = False
        for step in generator:
            if isinstance(step, tuple) and step[0] == 'SelectFile':
                file_selected = True
        self.assertTrue(file_selected)

    def test_change_logging( self ):
        change_logging_action = ChangeLogging()
        for step in change_logging_action.model_run(self.context, None):
            if isinstance( step, action_steps.ChangeObject ):
                step.get_object().level = logging.INFO

    def test_segmentation_fault( self ):
        list(self.gui_run(segmentation_fault_action_name, self.gui_context, None))


class FieldActionCase(TestMetaData, ExampleModelMixinCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        movie_admin = app_admin.get_related_admin(Movie)
        cls.setup_sample_model()
        list(LoadSampleData().model_run(None, None))
        cls.movie = cls.session.query(Movie).offset(1).first()
        movie_list_model_context = ObjectsModelContext(
            movie_admin, movie_admin.get_proxy([cls.movie]), None
        )
        # a model context for the director attribute
        director_attributes = list(movie_admin.get_static_field_attributes(
            ['director']
        ))[0]
        cls.director_context = UpdateMixin.field_action_model_context(
            movie_list_model_context, cls.movie, director_attributes
        )
        # a model context for the script attribute
        script_attributes = list(movie_admin.get_static_field_attributes(
            ['script']
        ))[0]
        cls.script_context = UpdateMixin.field_action_model_context(
            movie_list_model_context, cls.movie, script_attributes
        )
        # a model context for the tags attribute
        tags_attributes = list(movie_admin.get_static_field_attributes(
            ['tags']
        ))[0]
        cls.tags_context = UpdateMixin.field_action_model_context(
            movie_list_model_context, cls.movie, tags_attributes
        )

    def test_select_object(self):
        select_object = SelectObject()
        object_selected = False
        person = self.session.query(Person).first()
        self.assertTrue(person)
        self.assertNotEqual(self.movie, person)
        generator = select_object.model_run(self.director_context, mode=None)
        for step in generator:
            if isinstance(step, action_steps.SelectObjects):
                generator.send(person)
                object_selected = True
        self.assertTrue(object_selected)
        self.assertEqual(self.movie.director, person)

    def test_upload_and_detach_file(self):
        upload_file = UploadFile()
        file_uploaded = False
        generator = upload_file.model_run(self.script_context, mode=None)
        for step in generator:
            if isinstance(step, action_steps.SelectFile):
                generator.send([__file__])
                file_uploaded = True
        self.assertTrue(file_uploaded)
        self.assertTrue(self.movie.script)
        detach_file = DetachFile()
        generator = detach_file.model_run(self.script_context, mode=None)
        detach_confirmed = False
        for step in generator:
            if isinstance(step, action_steps.MessageBox):
                generator.send(QtWidgets.QMessageBox.StandardButton.Yes)
                detach_confirmed = True
        self.assertTrue(detach_confirmed)
        self.assertEqual(self.movie.script, None)

    def test_add_existing_object(self):
        tag = self.session.query(Tag).first()
        self.assertTrue(tag)
        state = add_existing_object.get_state(self.tags_context)
        self.assertTrue(state.visible)
        self.assertTrue(state.enabled)
        initial_row_count = len(self.movie.tags)
        generator = add_existing_object.model_run(self.tags_context, mode=None)
        for step in generator:
            if isinstance(step, action_steps.SelectObjects):
                generator.send([tag])
        new_row_count = len(self.movie.tags)
        self.assertEqual(new_row_count, initial_row_count+1)


class ListFilterCase(TestMetaData):

    def setUp( self ):
        super( ListFilterCase, self ).setUp()
        self.app_admin = ApplicationAdmin()

    def test_filter_strategies(self):

        class B(self.Entity):

            class Admin(EntityAdmin):
                list_display = ['one2many_col']
                field_attributes = {
                    'one2many_col':{'filter_strategy': list_filter.One2ManyFilter},
                }

        class A(self.Entity):

            text_col = schema.Column(types.Unicode(10), nullable=False)
            text_col_nullable = schema.Column(types.Unicode(10))
            bool_col = schema.Column(types.Boolean, nullable=False)
            bool_col_nullable = schema.Column(types.Boolean)
            date_col = schema.Column(types.Date, nullable=False)
            date_col_nullable = schema.Column(types.Date)
            time_col = schema.Column(types.Time, nullable=False)
            time_col_nullable = schema.Column(types.Time)
            int_col = schema.Column(types.Integer, nullable=False)
            int_col_nullable = schema.Column(types.Integer)
            months_col = schema.Column(types.Integer, nullable=False)
            months_col_nullable = schema.Column(types.Integer)
            enum_col = schema.Column(camelot.types.Enumeration([('Test', 'Test')]), nullable=False)
            enum_col_nullable = schema.Column(camelot.types.Enumeration([('Test', 'Test')]))

            b_id = schema.Column(types.Integer(), schema.ForeignKey(B.id), nullable=False)
            many2one_col = orm.relationship(B)

            class Admin(EntityAdmin):
                field_attributes = {
                    'months_col':{'delegate': delegates.MonthsDelegate},
                    'months_col_nullable':{'delegate': delegates.MonthsDelegate},
                }
        B.one2many_col = orm.relationship(A)

        self.create_all()
        # Create entity instance to be able to test Many2One and One2Many filter strategies.
        b1 = B()
        b2 = B()
        b3 = B()
        self.session.flush()
        a_defaults = dict(
            text_col='', bool_col=False, date_col=datetime.date.today(), time_col=datetime.time(21, 5, 0),
            int_col=1000, months_col=12, enum_col='Test'
        )
        a1 = A(**a_defaults, many2one_col=b1)
        a2 = A(**a_defaults, many2one_col=b2)
        a3 = A(**a_defaults, many2one_col=b3)
        self.session.flush()

        # Verify strategies accept both the 'raw' operands, as well as their textual representation (used when searching).
        for cols, strategy_cls, search_text, *values in (
            ([A.text_col,   A.text_col_nullable],   list_filter.StringFilter,   'test',       'test'),
            ([A.bool_col,   A.bool_col_nullable],   list_filter.BoolFilter,     'True',        True),
            ([A.date_col,   A.date_col_nullable],   list_filter.DateFilter,     '01-01-2020',  datetime.date(2020,1,1), datetime.date(2022,1,1)),
            ([A.int_col,    A.int_col_nullable],    list_filter.IntFilter,      '1000',        1000, 5000),
            ([A.months_col, A.months_col_nullable], list_filter.MonthsFilter,   '12',          12, 24),
            ([A.enum_col,   A.enum_col_nullable],   list_filter.ChoicesFilter,  'Test',       'Test'),
            ([A.many2one_col],                      list_filter.Many2OneFilter, '1',           b1.id),
            ([A.many2one_col],                      list_filter.Many2OneFilter, '1',           b1.id, b2.id),
            ([A.many2one_col],                      list_filter.Many2OneFilter, '1',           b1.id, b2.id, b3.id),
            ([A.many2one_col],                      list_filter.Many2OneFilter, '1',           b1),
            ([A.many2one_col],                      list_filter.Many2OneFilter, '1',           b1, b2),
            ([A.many2one_col],                      list_filter.Many2OneFilter, '1',           b1, b2, b3),
            ([B.one2many_col],                      list_filter.One2ManyFilter, '1',           a1),
            ([B.one2many_col],                      list_filter.One2ManyFilter, '1',           a1, a2),
            ([B.one2many_col],                      list_filter.One2ManyFilter, '1',           a1, a2, a3),
            ):
            for col in cols:
                admin = self.app_admin.get_related_admin(col.class_)
                query = admin.get_query()
                # Verify expected filter strategy is set:
                fa = admin.get_field_attributes(col.key)
                self.assertIsInstance( fa['filter_strategy'], strategy_cls)

                # Check assertion on invalid attribute:
                for invalid_attribute in [None, '', 'text_col']:
                    with self.assertRaises(AssertionError) as exc:
                        strategy_cls(invalid_attribute)
                if strategy_cls == list_filter.Many2OneFilter:
                    self.assertEqual(str(exc.exception), strategy_cls.AssertionMessage.invalid_many2one_relationship_attribute.value)
                elif strategy_cls == list_filter.One2ManyFilter:
                    self.assertEqual(str(exc.exception), strategy_cls.AssertionMessage.invalid_relationship_attribute.value)
                else:
                    self.assertEqual(str(exc.exception), strategy_cls.AssertionMessage.no_queryable_attribute.value)
                    # Check assertion on no attributes provided:s
                    with self.assertRaises(AssertionError) as exc:
                        strategy_cls()
                    self.assertEqual(str(exc.exception), strategy_cls.AssertionMessage.no_attributes.value)

                if strategy_cls != list_filter.One2ManyFilter:
                    filter_strategy = strategy_cls(col, **fa)
                    operators = filter_strategy.get_operators()
                    # Verify that the operators that check on emptiness are only present for nullable attributes.
                    if not fa['nullable']:
                        self.assertNotIn(list_filter.Operator.is_empty, operators)
                        self.assertNotIn(list_filter.Operator.is_not_empty, operators)
                else:
                    filter_strategy = strategy_cls(col)
                    operators = filter_strategy.get_operators()

                # Verify that for each operator of the filter strategy its clause is constructed properly:
                for operator in operators:
                    operands = values[0:operator.arity.maximum-1] if operator.arity.maximum is not None else values
                    filter_strategy.get_clause(query, operator, *operands)

                # Verify assertion on operands arity mismatch
                with self.assertRaises(AssertionError) as exc:
                    filter_strategy.get_clause(query, list_filter.Operator.eq)
                self.assertEqual(str(exc.exception), strategy_cls.AssertionMessage.nr_operands_arity_mismatch.value.format(0, 1, 1))

                # Verify that for each operator of the filter strategy its search clause is constructed properly:
                search_clause = filter_strategy.get_search_clause(query, search_text)
                # Verify that the search clause equals a general filter clause with the strategy's search operator and the converted operand:
                search_operator = filter_strategy.get_search_operator()
                operands = values[0:search_operator.arity.maximum-1] if search_operator.arity.maximum is not None else values
                filter_clause = filter_strategy.get_clause(query, search_operator, operands[0])
                if str(search_clause) != str(filter_clause):
                    filter_clause = filter_strategy.get_clause(query, search_operator, operands[0])
                self.assertEqual(str(search_clause), str(filter_clause))

        # Check assertion on python type mismatch:
        with self.assertRaises(AssertionError) as exc:
            list_filter.StringFilter(A.int_col)
        self.assertEqual(str(exc.exception), strategy_cls.AssertionMessage.python_type_mismatch.value)
        # The choices filter should allow all python types:
        list_filter.ChoicesFilter(A.int_col)
        list_filter.ChoicesFilter(A.text_col)
        # But in case of multiple attribute, should assert if their python type differs:
        with self.assertRaises(AssertionError) as exc:
            list_filter.ChoicesFilter(A.int_col, A.text_col)
        self.assertEqual(str(exc.exception), strategy_cls.AssertionMessage.python_type_mismatch.value)
