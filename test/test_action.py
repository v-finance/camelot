import datetime
import gc
import io
import logging
import os
import unittest
import openpyxl

import camelot.types

from camelot.admin.admin_route import AdminRoute
from camelot.core.exception import UserException
from camelot.core.item_model import ListModelProxy, ObjectRole
from camelot.admin.action import Action, ActionStep, State
from camelot.admin.action import (
    list_action, application_action, form_action, list_filter,
    ApplicationActionGuiContext, Mode
)
from camelot.admin.action.application import Application
from camelot.admin.action import export_mapping
from camelot.admin.action.base import GuiContext
from camelot.admin.action.logging import ChangeLogging
from camelot.admin.action.list_action import SetFilters
from camelot.admin.application_admin import ApplicationAdmin
from camelot.admin.entity_admin import EntityAdmin
from camelot.admin.validator.entity_validator import EntityValidator
from camelot.bin.meta import NewProjectOptions
from camelot.core.qt import QtGui, QtWidgets, Qt
from camelot.core.exception import CancelRequest
from camelot.core.orm import EntityBase, EntityMeta, Session
from camelot.core.utils import ugettext_lazy as _
from camelot.model import party
from camelot.model.party import Person
from camelot.test import GrabMixinCase, RunningThreadCase
from camelot.test.action import MockListActionGuiContext, MockModelContext
from camelot.view import action_steps, import_utils, utils
from camelot.view.action_runner import hide_progress_dialog
from camelot.view.action_steps import PrintHtml, SelectItem
from camelot.view.action_steps.change_object import ChangeObject, ChangeField
from camelot.view.action_steps.profile import EditProfiles
from camelot.view.controls import actionsbox, delegates, tableview
from camelot.view.controls.action_widget import ActionPushButton
from camelot.view.controls.tableview import TableView
from camelot.view.import_utils import (ColumnMapping, ColumnMappingAdmin, MatchNames)
from camelot.view.qml_view import get_qml_root_backend
from camelot_example.importer import ImportCovers
from camelot_example.model import Movie

from sqlalchemy import MetaData, orm, schema, types
from sqlalchemy.ext.declarative import declarative_base

from . import app_admin, test_core, test_view
from .test_item_model import QueryQStandardItemModelMixinCase
from .test_orm import TestMetaData
from .test_model import ExampleModelMixinCase

test_images = [os.path.join( os.path.dirname(__file__), '..', 'camelot_example', 'media', 'covers', 'circus.png') ]

LOGGER = logging.getLogger(__name__)

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


class ActionBaseCase(RunningThreadCase, SerializableMixinCase):

    def setUp(self):
        super().setUp()
        self.admin_route = app_admin.get_admin_route()
        self.gui_context = ApplicationActionGuiContext()
        self.gui_context.admin_route = self.admin_route

    def test_action_step(self):
        step = ActionStep()
        step.gui_run(self.gui_context)

    def test_action(self):

        class CustomAction( Action ):
            verbose_name = 'Custom Action'
            shortcut = QtGui.QKeySequence.StandardKey.New
            modes = [
                Mode('mode_1', _('First mode')),
                Mode('mode_2', _('Second mode')),
            ]

        action = CustomAction()
        list(self.gui_run(action, self.gui_context))
        state = self.get_state(action, self.gui_context)
        self.assertTrue(state.verbose_name)
        # serialize the state of an action
        deserialized_state = self._write_read(state)
        self.assertEqual(deserialized_state.verbose_name, state.verbose_name)
        self.assertEqual(len(deserialized_state.modes), len(state.modes))


class ActionWidgetsCase(unittest.TestCase, GrabMixinCase):
    """Test widgets related to actions.
    """

    images_path = test_view.static_images_path

    def setUp(self):
        get_qml_root_backend().setVisible(True, False)
        self.action = ImportCovers()
        self.admin_route = app_admin.get_admin_route()
        self.gui_context = ApplicationActionGuiContext()
        self.gui_context.admin_route = app_admin.get_admin_route()
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
            widget.set_state( state )
            self.grab_widget( widget, suffix='%s_%s'%( suffix,
                                                       state_name ) )

    def test_action_push_botton( self ):
        widget = ActionPushButton( self.action,
                                   self.gui_context,
                                   self.parent )
        self.grab_widget_states( widget, 'application' )

    def test_hide_progress_dialog( self ):
        dialog = self.gui_context.get_progress_dialog()
        dialog.show()
        with hide_progress_dialog(self.gui_context):
            self.assertTrue( dialog.isHidden() )
        self.assertFalse( dialog.isHidden() )

class ActionStepsCase(RunningThreadCase, GrabMixinCase, ExampleModelMixinCase, SerializableMixinCase):
    """Test the various steps that can be executed during an
    action.
    """

    images_path = test_view.static_images_path

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
        super(ActionStepsCase, self).setUp()
        get_qml_root_backend().setVisible(True, False)
        self.admin_route = app_admin.get_admin_route()
        self.gui_context = ApplicationActionGuiContext()
        self.gui_context.admin_route = self.admin_route

    def test_change_object( self ):
        admin = app_admin.get_related_admin(NewProjectOptions)
        options = NewProjectOptions()
        options.name = 'Videostore'
        options.module = 'videostore'
        options.domain = 'example.com'
        change_object = ChangeObject(options, admin)
        dialog = change_object.render(self.gui_context)
        self.grab_widget( dialog )

    def test_select_file( self ):
        action_steps.SelectFile('Image Files (*.png *.jpg);;All Files (*)')

    def test_select_item( self ):

        # begin select item
        class SendDocumentAction( Action ):

            def model_run( self, model_context, mode ):
                methods = [ ('email', 'By E-mail'),
                            ('fax',   'By Fax'),
                            ('post',  'By postal mail') ]
                method = yield SelectItem( methods, value='email' )
                # handle sending of the document
                LOGGER.info('selected {}'.format(method))

        # end select item

        action = SendDocumentAction()
        for step in self.gui_run(action, self.gui_context):
            if isinstance(step, ActionStep):
                dialog = step.render()
                self.grab_widget(dialog)
        self.assertTrue(dialog)

    def test_edit_profile(self):
        step = yield EditProfiles([], '')
        dialog = EditProfiles.render(self.gui_context, step)
        dialog.show()
        self.grab_widget(dialog)

    def test_open_file( self ):
        stream = io.BytesIO(b'1, 2, 3, 4')
        open_stream = action_steps.OpenStream( stream, suffix='.csv' )
        self.assertTrue( str( open_stream ) )
        action_steps.OpenString(b'1, 2, 3, 4')
        context = { 'columns':['width', 'height'],
                    'table':[[1,2],[3,4]] }
        action_steps.OpenJinjaTemplate( 'list.html', context )
        action_steps.WordJinjaTemplate( 'list.html', context )

    def test_update_progress( self ):
        update_progress = action_steps.UpdateProgress(
            20, 100, _('Importing data')
        )
        self.assertTrue( str( update_progress ) )
        update_progress = self._write_read(update_progress)
        # give the gui context a progress dialog, so it can be updated
        progress_dialog = self.gui_context.get_progress_dialog()
        update_progress.gui_run(self.gui_context, update_progress._to_bytes())
        # now press the cancel button
        progress_dialog.cancel()
        with self.assertRaises( CancelRequest ):
            update_progress.gui_run(self.gui_context, update_progress._to_bytes())

    def test_message_box( self ):
        step = action_steps.MessageBox('Hello World')
        serialized_step = step._to_dict()
        dialog = step.render(serialized_step)
        dialog.show()
        self.grab_widget(dialog)

    #def test_main_menu(self):
        #main_menu = action_steps.MainMenu(app_admin.get_main_menu())
        #main_menu = self._write_read(main_menu)
        #main_menu.gui_run(self.gui_context)


class ListActionsCase(
    RunningThreadCase,
    GrabMixinCase, ExampleModelMixinCase, QueryQStandardItemModelMixinCase):
    """Test the standard list actions.
    """

    images_path = test_view.static_images_path

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.thread.post(cls.setup_sample_model)
        cls.thread.post(cls.load_example_data)
        cls.group_box_filter = list_filter.GroupBoxFilter(
            'last_name', exclusive=True
        )
        cls.combo_box_filter = list_filter.ComboBoxFilter('last_name')
        cls.process()
        gc.disable()

    @classmethod
    def tearDownClass(cls):
        cls.thread.post(cls.tear_down_sample_model)
        cls.process()
        super().tearDownClass()
        gc.enable()

    def setUp( self ):
        super(ListActionsCase, self).setUp()
        self.thread.post(self.session.close)
        self.process()
        self.admin = app_admin.get_related_admin(Person)
        self.thread.post(self.setup_proxy)
        self.process()
        self.admin_route = self.admin.get_admin_route()
        self.setup_item_model(self.admin_route, self.admin.get_name())
        self.movie_admin = app_admin.get_related_admin(Movie)
        # make sure the model has rows and header data
        self._load_data(self.item_model)
        table_view = tableview.TableView(ApplicationActionGuiContext(), self.admin_route)
        table_view.set_admin()
        table_view.table.setModel(self.item_model)
        # select the first row
        table_view.table.setCurrentIndex(self.item_model.index(0, 0))
        self.gui_context = table_view.gui_context
        self.gui_context.admin_route = self.admin_route
        self.model_context = self.gui_context.create_model_context()
        # create a model context
        self.example_folder = os.path.join( os.path.dirname(__file__), '..', 'camelot_example' )

    def tearDown( self ):
        Session().expunge_all()

    def test_gui_context( self ):
        self.assertTrue( isinstance( self.gui_context.copy(),
                                     list_action.ListActionGuiContext ) )
        model_context = self.gui_context.create_model_context()
        self.assertTrue( isinstance( model_context,
                                     list_action.ListActionModelContext ) )
        list( model_context.get_collection() )
        list( model_context.get_selection() )
        model_context.get_object()

    def test_change_row_actions( self ):

        gui_context = MockListActionGuiContext()
        to_first = list_action.ToFirstRow()
        to_previous = list_action.ToPreviousRow()
        to_next = list_action.ToNextRow()
        to_last = list_action.ToLastRow()

        # the state does not change when the current row changes,
        # to make the actions usable in the main window toolbar
        to_last.gui_run( gui_context )
        #self.assertFalse( get_state( to_last ).enabled )
        #self.assertFalse( get_state( to_next ).enabled )
        to_previous.gui_run( gui_context )
        #self.assertTrue( get_state( to_last ).enabled )
        #self.assertTrue( get_state( to_next ).enabled )
        to_first.gui_run( gui_context )
        #self.assertFalse( get_state( to_first ).enabled )
        #self.assertFalse( get_state( to_previous ).enabled )
        to_next.gui_run( gui_context )
        #self.assertTrue( get_state( to_first ).enabled )
        #self.assertTrue( get_state( to_previous ).enabled )

    def test_print_preview(self):
        action = list_action.PrintPreview()
        for step in self.gui_run(action, self.gui_context):
            if isinstance(step, action_steps.PrintPreview):
                dialog = step.render(self.gui_context)
                dialog.show()
                self.grab_widget(dialog)
        self.assertTrue(dialog)

    def test_export_spreadsheet( self ):
        action = list_action.ExportSpreadsheet()
        for step in self.gui_run(action, self.gui_context):
            if isinstance(step, tuple) and step[0] == 'OpenFile':
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
                generator.send('mapping 1')

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
        with self.assertRaises(Exception) as ec:
            self.test_import_from_file('import_example.xls')
        self.assertIn('xls is not a supported', str(ec.exception))

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
        action = list_action.ImportFromFile()
        generator = self.gui_run(action, self.gui_context)
        for step in generator:
            if isinstance(step, tuple) and step[0] == 'SelectFile':
                generator.send([os.path.join(self.example_folder, filename)])
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

    def test_replace_field_contents( self ):
        action = list_action.ReplaceFieldContents()
        steps = action.model_run(self.gui_context.create_model_context(), None)
        for step in steps:
            if isinstance(step, ChangeField):
                dialog = step.render()
                field_editor = dialog.findChild(QtWidgets.QWidget, 'field_choice')
                field_editor.set_value('first_name')
                dialog.show()
                self.grab_widget( dialog )
                steps.send(('first_name', 'known'))

    def test_open_form_view( self ):
        # sort and filter the original model
        item_view = self.gui_context.item_view
        list_model = item_view.model()
        list_model.sort(1, Qt.SortOrder.DescendingOrder)
        list_model.timeout_slot()
        self.process()
        list_model.headerData(0, Qt.Orientation.Vertical, ObjectRole)
        list_model.data(list_model.index(0, 0), Qt.ItemDataRole.DisplayRole)
        list_model.timeout_slot()
        self.process()
        self.gui_context.item_view.setCurrentIndex(list_model.index(0, 0))
        model_context = self.gui_context.create_model_context()
        open_form_view_action = list_action.OpenFormView()
        for step in open_form_view_action.model_run(model_context, None):
            form = step.render(self.gui_context)
            form_value = form.model.get_value()
        self.assertTrue(isinstance(form_value, ListModelProxy))

    @staticmethod
    def track_crud_steps(action, model_context):
        created = updated = None
        steps = []
        for step in action.model_run(model_context, None):
            steps.append(type(step))
            if isinstance(step, action_steps.CreateObjects):
                created = step.objects_created if created is None else created.extend(step.objects_created)
            elif isinstance(step, action_steps.UpdateObjects):
                updated = step.objects_updated if updated is None else updated.extend(step.objects_updated)
        return steps, created, updated

    def test_duplicate_selection( self ):
        initial_row_count = self._row_count(self.item_model)
        action = list_action.DuplicateSelection()
        action.gui_run(self.gui_context)
        self.process()
        new_row_count = self._row_count(self.item_model)
        self.assertEqual(new_row_count, initial_row_count+1)
        person = Person(first_name='test', last_name='person')
        self.session.flush()
        model_context = MockModelContext(self.session)
        model_context.admin = self.admin
        model_context.proxy = self.admin.get_proxy([])

        # The action should only be applicable for a single selection.
        # So verify a UserException is raised when selecting multiple ...
        model_context.selection = [None, None]
        model_context.selection_count = 2
        with self.assertRaises(UserException) as exc:
            list(action.model_run(model_context, None))
        self.assertEqual(exc.exception.text, action.Message.no_single_selection.value) 
        # ...and selecting None has no side-effects.
        model_context.selection = []
        model_context.selection_count = 0
        steps, created, updated = self.track_crud_steps(action, model_context)
        self.assertIsNone(created)
        self.assertIsNone(updated)
        self.assertNotIn(action_steps.FlushSession, steps)

        # Verify the valid duplication of a single selection.
        model_context.selection = [person]
        model_context.selection_count = 1
        steps, created, updated = self.track_crud_steps(action, model_context)
        self.assertEqual(len(created), 1)
        self.assertEqual(len(updated), 0)
        self.assertIn(action_steps.FlushSession, steps)
        copied_obj = created[0]
        self.assertEqual(copied_obj.first_name, person.first_name)
        self.assertEqual(copied_obj.last_name, person.last_name)

        # Verify in the case wherein the duplicated instance is invalid, its is not flushed yet and opened within its form.
        # Set custom validator that always fails to make sure duplicated instance is found to be invalid/
        validator = self.admin.validator
        class CustomValidator(EntityValidator):

            def validate_object(self, p):
                return ['some validation error']

        self.admin.validator = CustomValidator
        model_context.selection = [person]
        steps, created, updated = self.track_crud_steps(action, model_context)
        self.assertEqual(len(created), 1)
        self.assertIsNone(updated)
        self.assertIn(action_steps.OpenFormView, steps)
        self.assertNotIn(action_steps.FlushSession, steps)
        copied_obj = created[0]
        self.assertEqual(copied_obj.first_name, person.first_name)
        self.assertEqual(copied_obj.last_name, person.last_name)
        # Reinstated original validator to prevent intermingling with other test (cases).
        self.admin.validator = validator

    def test_delete_selection(self):
        selected_object = self.model_context.get_object()
        self.assertTrue(selected_object in self.session)
        delete_selection_action = list_action.DeleteSelection()
        delete_selection_action.gui_run( self.gui_context )
        self.process()
        self.assertFalse(selected_object in self.session)

    def test_switch_rank(self):

        metadata = MetaData()
        Entity = declarative_base(cls = EntityBase,
                                  metadata = metadata,
                                  metaclass = EntityMeta,
                                  class_registry = dict(),
                                  constructor = None,
                                  name = 'Entity' )
        metadata.bind = 'sqlite://'
        session = Session()

        class A(Entity):

            rank = schema.Column(types.Integer, nullable=False)
            type = schema.Column(types.Unicode, nullable=False)

            __facade_args__ = {
                'ranked_by': (rank, type)
            }

            class Admin(EntityAdmin):
                pass

        metadata.create_all()
        selected_object = self.model_context.get_object()
        self.assertTrue(selected_object in self.session)
        switch_rank_action = list_action.SwitchRank()

        # The action should not be present in the related toolbar actions of the entity if its not rank-based.
        related_toolbar_actions = [action.route[-1] for action in self.model_context.admin.get_related_toolbar_actions('onetomany')]
        self.assertNotIn(list_action.SwitchRank.name, related_toolbar_actions)
        # If the action is run on a non rank-based entity anyways, an assertion should block it.
        with self.assertRaises(AssertionError) as exc:
            list(switch_rank_action.model_run(self.model_context, None))
        self.assertEqual(str(exc.exception), list_action.SwitchRank.Message.entity_not_rank_based.value.format(self.model_context.admin.entity))

        # The action should be present on a rank-based entity:
        admin = app_admin.get_related_admin(A)
        related_toolbar_actions = [action.route[-1] for action in admin.get_related_toolbar_actions('onetomany')]
        self.assertIn(list_action.SwitchRank.name, related_toolbar_actions)

        # The action should raise an exception if no 2 lines are selected:
        ax1 = A(type='x', rank=1)
        ax2 = A(type='x', rank=2)
        ay1 = A(type='y', rank=1)
        session.flush()
        model_context = list_action.ListActionModelContext()
        model_context.proxy = admin.get_proxy([ax1, ax2, ay1])
        model_context.admin = admin
        with self.assertRaises(UserException) as exc:
            list(switch_rank_action.model_run(model_context, None))
        self.assertEqual(exc.exception.text, list_action.SwitchRank.Message.select_2_lines.value)

        # 2 lines selected within the same rank dimension should work:
        model_context.selected_rows = [(0,1)]
        model_context.selection_count = 2
        list(switch_rank_action.model_run(model_context, None))
        self.assertEqual(ax1.rank, 2)
        self.assertEqual(ax2.rank, 1)

        # The action should not allow changing the rank between incompatible objects (that do not share the same rank dimension).
        model_context.selected_rows = [(0,0), (2,2)]
        model_context.selection_count = 2
        with self.assertRaises(UserException) as exc:
            list(switch_rank_action.model_run(model_context, None))
        self.assertEqual(exc.exception.text, list_action.SwitchRank.Message.incompatible_rank_dimension.value)

        metadata.drop_all()
        metadata.clear()

    def test_add_existing_object(self):
        initial_row_count = self._row_count(self.item_model)
        action = list_action.AddExistingObject()
        steps = self.gui_run(action, self.gui_context)
        for step in steps:
            # SelectObjects is a serializable action
            if isinstance(step, tuple) and step[0] == action_steps.SelectObjects.__name__:
                steps.send([Person(first_name='Unknown', last_name='Unknown')])
        new_row_count = self._row_count(self.item_model)
        self.assertEqual(new_row_count, initial_row_count+1)

    def test_add_new_object(self):
        add_new_object_action = list_action.AddNewObject()
        add_new_object_action.gui_run( self.gui_context )

    def test_remove_selection(self):
        remove_selection_action = list_action.RemoveSelection()
        list( remove_selection_action.model_run( self.gui_context.create_model_context(), None ) )

    def test_set_filters(self):
        set_filters_step = yield SetFilters()
        state = self.get_state(set_filters_step, self.gui_context)
        self.assertTrue(len(state.modes))
        mode_names = set(m.name for m in state.modes)
        self.assertIn('first_name', mode_names)
        self.assertNotIn('note', mode_names)
        SetFilters.gui_run(self.gui_context, set_filters_step[1])
        #steps = self.gui_run(set_filters, self.gui_context)
        #for step in steps:
            #if isinstance(step, action_steps.ChangeField):
                #steps.send(('first_name', 'test'))

    def test_group_box_filter(self):
        state = self.get_state(self.group_box_filter, self.gui_context)
        self.assertTrue(len(state.modes))
        widget = self.gui_context.view.render_action(self.group_box_filter, None)
        widget.set_state(state)
        self.assertTrue(len(widget.get_value()))
        widget.run_action()
        self.grab_widget(widget)

    def test_combo_box_filter(self):
        state = self.get_state(self.combo_box_filter, self.gui_context)
        self.assertTrue(len(state.modes))
        widget = self.gui_context.view.render_action(self.combo_box_filter, None)
        widget.set_state(state)
        self.assertTrue(len(widget.get_value()))
        widget.run_action()
        self.grab_widget(widget)

    def test_filter_list(self):
        action_box = actionsbox.ActionsBox(None)
        for action in [self.group_box_filter,
                       self.combo_box_filter]:
            action_widget = self.gui_context.view.render_action(action, None)
            action_box.layout().addWidget(action_widget)
        self.grab_widget(action_box)
        return action_box

    def test_filter_list_in_table_view(self):
        gui_context = GuiContext()
        gui_context.action_routes = {}
        person_admin = Person.Admin(app_admin, Person)
        table_view = TableView(gui_context, person_admin.get_admin_route())
        filters = [self.group_box_filter,
                   self.combo_box_filter]
        filter_routes = []
        filter_states = []
        for action in filters:
            action_route = AdminRoute._register_list_action_route(person_admin.get_admin_route(), action)
            filter_routes.append(action_route)
            action_state = State()._to_dict() # use default state
            filter_states.append((action_route, action_state))
        table_view.set_admin()
        table_view.set_filters(filter_routes, filter_states)

    def test_orm( self ):

        class UpdatePerson( Action ):

            verbose_name = _('Update person')

            def model_run( self, model_context, mode ):
                for person in model_context.get_selection():
                    soc_number = person.social_security_number
                    if soc_number:
                        # assume the social sec number contains the birth date
                        person.birth_date = datetime.date( int(soc_number[0:4]),
                                                           int(soc_number[4:6]),
                                                           int(soc_number[6:8])
                                                           )
                    # delete the email of the person
                    for contact_mechanism in person.contact_mechanisms:
                        model_context.session.delete( contact_mechanism )
                        yield action_steps.DeleteObjects((contact_mechanism,))
                    # add a new email
                    m = ('email', '%s.%s@example.com'%( person.first_name,
                                                        person.last_name ) )
                    cm = party.ContactMechanism( mechanism = m )
                    pcm = party.PartyContactMechanism( party = person,
                                                       contact_mechanism = cm )
                    
                    # immediately update the GUI
                    yield action_steps.CreateObjects((cm,))
                    yield action_steps.CreateObjects((pcm,))
                    yield action_steps.UpdateObjects((person,))
                # flush the session on finish
                model_context.session.flush()

        # end manual update

        action_step = None
        update_person = UpdatePerson()
        for step in self.gui_run(update_person, self.gui_context):
            if isinstance(step, ActionStep):
                action_step = step
                action_step.gui_run(self.gui_context)
        self.assertTrue(action_step)

        # begin auto update

        class UpdatePerson( Action ):

            verbose_name = _('Update person')

            def model_run( self, model_context, mode ):
                for person in model_context.get_selection():
                    soc_number = person.social_security_number
                    if soc_number:
                        # assume the social sec number contains the birth date
                        person.birth_date = datetime.date( int(soc_number[0:4]),
                                                           int(soc_number[4:6]),
                                                           int(soc_number[6:8])
                                                           )
                    # delete the email of the person
                    for contact_mechanism in person.contact_mechanisms:
                        model_context.session.delete( contact_mechanism )
                    # add a new email
                    m = ('email', '%s.%s@example.com'%( person.first_name,
                                                        person.last_name ) )
                    cm = party.ContactMechanism( mechanism = m )
                    party.PartyContactMechanism( party = person,
                                                contact_mechanism = cm )
                # flush the session on finish and update the GUI
                yield action_steps.FlushSession( model_context.session )

        # end auto update

        action_step = None
        update_person = UpdatePerson()
        for step in self.gui_run(update_person, self.gui_context):
            if isinstance(step, ActionStep):
                action_step = step
                action_step.gui_run(self.gui_context)
        self.assertTrue(action_step)

    def test_print_html( self ):

        # begin html print
        class PersonSummary(Action):

            verbose_name = _('Summary')

            def model_run(self, model_context, mode):
                person = model_context.get_object()
                yield PrintHtml("<h1>This will become the personal report of {}!</h1>".format(person))
        # end html print

        action = PersonSummary()
        steps = list(self.gui_run(action, self.gui_context))
        dialog = steps[0].render(self.gui_context)
        dialog.show()
        self.grab_widget(dialog)

class FormActionsCase(
    RunningThreadCase,
    ExampleModelMixinCase, GrabMixinCase, QueryQStandardItemModelMixinCase):
    """Test the standard list actions.
    """

    images_path = test_view.static_images_path

    @classmethod
    def setUpClass(cls):
        super(FormActionsCase, cls).setUpClass()
        cls.thread.post(cls.setup_sample_model)
        cls.thread.post(cls.load_example_data)
        cls.process()

    @classmethod
    def tearDownClass(cls):
        cls.thread.post(cls.tear_down_sample_model)
        cls.process()
        super().tearDownClass()

    def setUp( self ):
        super(FormActionsCase, self).setUp()
        self.thread.post(self.setup_proxy)
        self.process()
        person_admin = app_admin.get_related_admin(Person)
        self.admin_route = person_admin.get_admin_route()
        self.setup_item_model(self.admin_route, person_admin.get_name())
        self.gui_context = form_action.FormActionGuiContext()
        self.gui_context._model = self.item_model
        self.gui_context.widget_mapper = QtWidgets.QDataWidgetMapper()
        self.gui_context.widget_mapper.setModel(self.item_model)
        self.gui_context.admin_route = self.admin_route
        self.gui_context.admin = person_admin

    def tearDown(self):
        super().tearDown()

    def test_gui_context( self ):
        self.assertTrue( isinstance( self.gui_context.copy(),
                                     form_action.FormActionGuiContext ) )
        self.assertTrue( isinstance( self.gui_context.create_model_context(),
                                     form_action.FormActionModelContext ) )

    def test_previous_next( self ):
        previous_action = form_action.ToPreviousForm()
        list(self.gui_run(previous_action, self.gui_context))
        next_action = form_action.ToNextForm()
        list(self.gui_run(next_action, self.gui_context))
        first_action = form_action.ToFirstForm()
        list(self.gui_run(first_action, self.gui_context))
        last_action = form_action.ToLastForm()
        list(self.gui_run(last_action, self.gui_context))

    def test_show_history( self ):
        show_history_action = form_action.ShowHistory()
        list(self.gui_run(show_history_action, self.gui_context))

    def test_close_form( self ):
        close_form_action = form_action.CloseForm()
        list(self.gui_run(close_form_action, self.gui_context))

class ApplicationCase(RunningThreadCase, GrabMixinCase, ExampleModelMixinCase):

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
        self.gui_context = ApplicationActionGuiContext()
        self.admin_route = app_admin.get_admin_route()
        self.gui_context.admin_route = self.admin_route

    def tearDown(self):
        super().tearDown()

    def test_application(self):
        app = Application(app_admin)
        list(self.gui_run(app, self.gui_context))

    def test_custom_application(self):

        # begin custom application
        class CustomApplication(Application):
        
            def model_run( self, model_context, mode ):
                from camelot.view import action_steps
                yield action_steps.UpdateProgress(text='Starting up')
        # end custom application

        application = CustomApplication(app_admin)
        list(self.gui_run(application, self.gui_context))

class ApplicationActionsCase(
    RunningThreadCase, GrabMixinCase, ExampleModelMixinCase
    ):
    """Test application actions.
    """

    images_path = test_view.static_images_path

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
        super( ApplicationActionsCase, self ).setUp()
        self.context = MockModelContext(session=self.session)
        self.context.admin = app_admin
        self.admin_route = app_admin.get_admin_route()
        self.gui_context = application_action.ApplicationActionGuiContext()
        self.gui_context.admin_route = self.admin_route

    def test_refresh(self):
        refresh_action = application_action.Refresh()
        self.thread.post(self.dirty_session)
        self.process()
        #
        # refresh the session through the action
        #
        generator = self.gui_run(refresh_action, self.gui_context)
        for step in generator:
            if isinstance(step, action_steps.UpdateObjects):
                updates = step.get_objects()
        self.assertTrue(len(updates))

    def test_select_profile(self):
        profile_case = test_core.ProfileCase('setUp')
        profile_case.setUp()
        profile_store = profile_case.test_profile_store()
        action = application_action.SelectProfile(profile_store)
        generator = self.gui_run(action, self.gui_context)
        for step in generator:
            if isinstance(step, action_steps.SelectItem):
                generator.send(profile_store.get_last_profile())
                profile_selected = True
        self.assertTrue(profile_selected)

    def test_backup_and_restore( self ):
        backup_action = application_action.Backup()
        generator = self.gui_run(backup_action, self.gui_context)
        file_saved = False
        for step in generator:
            if isinstance(step, tuple) and step[0] == 'SaveFile':
                generator.send('unittest-backup.db')
                file_saved = True
        self.assertTrue(file_saved)
        restore_action = application_action.Restore()
        generator = self.gui_run(restore_action, self.gui_context)
        file_selected = False
        for step in generator:
            if isinstance(step, tuple) and step[0] == 'SelectFile':
                generator.send(['unittest-backup.db'])
                file_selected = True
        self.assertTrue(file_selected)

    def test_open_table_view(self):
        person_admin = app_admin.get_related_admin( Person )
        open_table_view_action = application_action.OpenTableView(person_admin)
        list(self.gui_run(open_table_view_action, self.gui_context))

    def test_open_new_view( self ):
        person_admin = app_admin.get_related_admin(Person)
        open_new_view_action = application_action.OpenNewView(person_admin)
        generator = self.gui_run(open_new_view_action, self.gui_context)
        for step in generator:
            if isinstance(step, action_steps.SelectSubclass):
                generator.send(person_admin)

    def test_change_logging( self ):
        change_logging_action = ChangeLogging()
        for step in change_logging_action.model_run(self.context, None):
            if isinstance( step, action_steps.ChangeObject ):
                step.get_object().level = logging.INFO

    def test_segmentation_fault( self ):
        segmentation_fault = application_action.SegmentationFault()
        list(self.gui_run(segmentation_fault, self.gui_context))

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
        b = B()
        self.session.flush()
        a_defaults = dict(
            text_col='', bool_col=False, date_col=datetime.date.today(), time_col=datetime.time(21, 5, 0),
            int_col=1000, months_col=12, enum_col='Test', many2one_col=b
        )
        A(**a_defaults)
        A(**a_defaults)
        A(**a_defaults)
        self.session.flush()

        for cols, strategy_cls, *values in (
            ([A.text_col,   A.text_col_nullable],   list_filter.StringFilter,   'test'),
            ([A.bool_col,   A.bool_col_nullable],   list_filter.BoolFilter,     'True'),
            ([A.date_col,   A.date_col_nullable],   list_filter.DateFilter,     '2020-01-01', '2022-01-01'),
            ([A.time_col,   A.time_col_nullable],   list_filter.TimeFilter,     '2020-01-01', '2022-01-01'),
            ([A.int_col,    A.int_col_nullable],    list_filter.IntFilter,      '1000',       '5000'),
            ([A.months_col, A.months_col_nullable], list_filter.MonthsFilter,   '12',         '24'),
            ([A.enum_col,   A.enum_col_nullable],   list_filter.ChoicesFilter,  'Test'),
            ([A.many2one_col],                      list_filter.Many2OneFilter, '1'),
            ([A.many2one_col],                      list_filter.Many2OneFilter, '1', '2'),
            ([A.many2one_col],                      list_filter.Many2OneFilter, '1', '2', '3'),
            ([B.one2many_col],                      list_filter.One2ManyFilter, '1'),
            ([B.one2many_col],                      list_filter.One2ManyFilter, '1', '2'),
            ([B.one2many_col],                      list_filter.One2ManyFilter, '1', '2', '3'),
            ):
            for col in cols:
                admin = self.app_admin.get_related_admin(col.class_)
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
                    filter_strategy.get_clause(admin, self.session, operator, *operands)

                # Verify assertion on operands arity mismatch
                with self.assertRaises(AssertionError) as exc:
                    filter_strategy.get_clause(admin, self.session, list_filter.Operator.eq)
                self.assertEqual(str(exc.exception), strategy_cls.AssertionMessage.nr_operands_arity_mismatch.value.format(0, 1, 1))

        # Check assertion on python type mismatch:
        with self.assertRaises(AssertionError) as exc:
            list_filter.StringFilter(A.int_col)
        self.assertEqual(str(exc.exception), strategy_cls.AssertionMessage.python_type_mismatch.value)
        # The choices filter should allow all python types:
        list_filter.ChoicesFilter(A.int_col)
        list_filter.ChoicesFilter(A.text_col)
