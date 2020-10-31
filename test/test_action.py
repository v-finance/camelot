import datetime
import json
import io
import logging
import os
import unittest

import openpyxl

import six

from camelot.core.item_model import ListModelProxy, ObjectRole
from camelot.admin.application_admin import ApplicationAdmin
from camelot.admin.action import Action, ActionStep, State
from camelot.admin.action import (list_action, application_action,
                                  document_action, form_action,
                                  list_filter, ApplicationActionGuiContext)
from camelot.admin.action.application import Application
from camelot.core.qt import QtGui, QtWidgets, Qt
from camelot.core.exception import CancelRequest
from camelot.core.utils import ugettext_lazy as _
from camelot.core.orm import Session

from camelot.model import party
from camelot.model.party import Person

from camelot.test import GrabMixinCase, RunningThreadCase
from camelot.test.action import MockModelContext
from camelot.view import action_steps, import_utils
from camelot.view.controls import tableview, actionsbox
from camelot.view import utils
from camelot.view.import_utils import (
    ColumnMapping, MatchNames, ColumnMappingAdmin
)
from camelot.view.workspace import DesktopWorkspace
from camelot_example.model import Movie

from . import test_view
from .test_item_model import QueryQStandardItemModelMixinCase
from .test_model import ExampleModelMixinCase

test_images = [os.path.join( os.path.dirname(__file__), '..', 'camelot_example', 'media', 'covers', 'circus.png') ]

LOGGER = logging.getLogger(__name__)


class ActionBaseCase(RunningThreadCase):

    def setUp(self):
        super().setUp()
        self.gui_context = ApplicationActionGuiContext()
        self.gui_context.admin = ApplicationAdmin()

    def test_action_step(self):
        step = ActionStep()
        step.gui_run(self.gui_context)

    def test_action(self):

        class CustomAction( Action ):
            verbose_name = 'Custom Action'
            shortcut = QtGui.QKeySequence.New

        action = CustomAction()
        list(self.gui_run(action, self.gui_context))
        state = self.get_state(action, self.gui_context)
        self.assertTrue(state.verbose_name)


class ActionWidgetsCase(unittest.TestCase, GrabMixinCase):
    """Test widgets related to actions.
    """

    images_path = test_view.static_images_path

    def setUp(self):
        from camelot_example.importer import ImportCovers
        self.app_admin = ApplicationAdmin()
        self.action = ImportCovers()
        self.workspace = DesktopWorkspace(self.app_admin, None)
        self.gui_context = self.workspace.gui_context
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
        from camelot.view.controls.action_widget import ActionPushButton
        widget = ActionPushButton( self.action,
                                   self.gui_context,
                                   self.parent )
        self.grab_widget_states( widget, 'application' )

    def test_hide_progress_dialog( self ):
        from camelot.view.action_runner import hide_progress_dialog
        dialog = self.gui_context.get_progress_dialog()
        dialog.show()
        with hide_progress_dialog(self.gui_context):
            self.assertTrue( dialog.isHidden() )
        self.assertFalse( dialog.isHidden() )

class ActionStepsCase(RunningThreadCase, GrabMixinCase, ExampleModelMixinCase):
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
        self.app_admin = ApplicationAdmin()
        self.workspace = DesktopWorkspace(self.app_admin, None)
        self.gui_context = self.workspace.gui_context

    def test_change_object( self ):
        from camelot.bin.meta import NewProjectOptions
        from camelot.view.action_steps.change_object import ChangeObject
        admin = self.app_admin.get_related_admin(NewProjectOptions)
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
        from camelot.view.action_steps import SelectItem

        # begin select item
        class SendDocumentAction( Action ):

            def model_run( self, model_context ):
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

    def test_text_document( self ):
        # begin text document
        class EditDocumentAction( Action ):

            def model_run( self, model_context ):
                document = QtGui.QTextDocument()
                document.setHtml( '<h3>Hello World</h3>')
                yield action_steps.EditTextDocument( document )
        # end text document

        action = EditDocumentAction()
        for step in self.gui_run(action, self.gui_context):
            if isinstance(step, ActionStep):
                dialog = step.render()
                self.grab_widget(dialog)
        self.assertTrue(dialog)

    def test_edit_profile(self):
        from camelot.view.action_steps.profile import EditProfiles
        step = EditProfiles([], '')
        dialog = step.render(self.gui_context)
        dialog.show()
        self.grab_widget(dialog)

    def test_open_file( self ):
        stream = six.BytesIO(b'1, 2, 3, 4')
        open_stream = action_steps.OpenStream( stream, suffix='.csv' )
        self.assertTrue( six.text_type( open_stream ) )
        action_steps.OpenString( six.b('1, 2, 3, 4') )
        context = { 'columns':['width', 'height'],
                    'table':[[1,2],[3,4]] }
        action_steps.OpenJinjaTemplate( 'list.html', context )
        action_steps.WordJinjaTemplate( 'list.html', context )

    def test_update_progress( self ):
        update_progress = action_steps.UpdateProgress( 20, 100, _('Importing data') )
        self.assertTrue( six.text_type( update_progress ) )
        stream = io.BytesIO()
        update_progress.writeStream(stream)
        stream.seek(0)
        update_progress_state = json.load(stream)
        self.assertTrue(update_progress_state)
        # give the gui context a progress dialog, so it can be updated
        progress_dialog = self.gui_context.get_progress_dialog()
        update_progress.gui_run( self.gui_context )
        # now press the cancel button
        progress_dialog.cancel()
        with self.assertRaises( CancelRequest ):
            update_progress.gui_run( self.gui_context )

    def test_message_box( self ):
        step = action_steps.MessageBox('Hello World')
        dialog = step.render()
        dialog.show()
        self.grab_widget(dialog)

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
        cls.editor_filter = list_filter.EditorFilter('last_name')
        cls.process()

    @classmethod
    def tearDownClass(cls):
        cls.thread.post(cls.tear_down_sample_model)
        cls.process()
        super().tearDownClass()

    def setUp( self ):
        super(ListActionsCase, self).setUp()
        self.thread.post(self.session.close)
        self.process()
        self.app_admin = ApplicationAdmin()
        self.admin = self.app_admin.get_related_admin(Person)
        self.thread.post(self.setup_proxy)
        self.process()
        self.setup_item_model(self.admin)
        self.movie_admin = self.app_admin.get_related_admin(Movie)
        # make sure the model has rows and header data
        self._load_data(self.item_model)
        table_view = tableview.AdminTableWidget(self.admin)
        table_view.setModel(self.item_model)
        # select the first row
        table_view.setCurrentIndex(self.item_model.index(0, 0))
        # create gui context
        self.gui_context = list_action.ListActionGuiContext()
        self.gui_context.admin = self.admin
        self.gui_context.view = table_view
        self.gui_context.item_view = table_view.findChild(QtWidgets.QTableView)
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
        from camelot.test.action import MockListActionGuiContext

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
            if isinstance(step, action_steps.OpenFile):
                filename = step.get_path()
        self.assertTrue(filename)
        # see if the generated file can be parsed
        openpyxl.load_workbook(filename)

    def test_save_restore_export_mapping(self):
        from camelot_example.model import Movie

        settings = self.app_admin.get_settings()
        settings.beginGroup('export_mapping')
        # make sure there are no previous settings
        settings.remove('')

        save_export_mapping = list_action.SaveExportMapping(settings)
        restore_export_mapping = list_action.RestoreExportMapping(settings)

        model_context = MockModelContext()
        admin = self.app_admin.get_related_admin(Movie)
        field_choices = [('field_{0}'.format(i), 'Field {0}'.format(i)) for i in range(10)]
        model_context.admin = import_utils.ColumnSelectionAdmin(
            admin,
            field_choices = field_choices
        )
        model_context.selection = [import_utils.ColumnMapping(0, [], 'field_1'),
                                   import_utils.ColumnMapping(1, [], 'field_2')]

        for step in save_export_mapping.model_run(model_context):
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

        generator = restore_export_mapping.model_run(model_context)
        for step in generator:
            if isinstance(step, action_steps.SelectItem):
                generator.send('mapping 1')

        self.assertEqual(model_context.selection[0].field, 'field_1')

    def test_match_names(self):
        rows = [
            ['first_name', 'last_name'],
            ['Unknown',    'Unknown'],
        ]
        fields = [field for field, _fa in self.gui_context.admin.get_columns()]
        mapping = ColumnMapping(0, rows)
        self.assertNotEqual(mapping.field, 'first_name' )
        
        match_names = MatchNames()
        model_context = MockModelContext()
        model_context.obj = mapping
        model_context.admin = ColumnMappingAdmin(
            self.gui_context.admin,
            field_choices=[(f,f) for f in fields]
        )
        list(match_names.model_run(model_context))
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
            if isinstance(step, action_steps.SelectFile):
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
        steps = self.gui_run(action, self.gui_context)
        for step in steps:
            if isinstance(step, action_steps.ChangeField):
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
        list_model.sort(1, Qt.DescendingOrder)
        list_model.timeout_slot()
        self.process()
        list_model.headerData(0, Qt.Vertical, ObjectRole)
        list_model.data(list_model.index(0, 0), Qt.DisplayRole)
        list_model.timeout_slot()
        self.process()
        self.gui_context.item_view.setCurrentIndex(list_model.index(0, 0))
        model_context = self.gui_context.create_model_context()
        open_form_view_action = list_action.OpenFormView()
        for step in open_form_view_action.model_run(model_context):
            form = step.render(self.gui_context)
            form_value = form.model.get_value()
        self.assertTrue(isinstance(form_value, ListModelProxy))
        
    def test_duplicate_selection( self ):
        initial_row_count = self._row_count(self.item_model)
        action = list_action.DuplicateSelection()
        action.gui_run(self.gui_context)
        self.process()
        new_row_count = self._row_count(self.item_model)
        self.assertEqual(new_row_count, initial_row_count+1)

    def test_delete_selection(self):
        selected_object = self.model_context.get_object()
        self.assertTrue(selected_object in self.session)
        delete_selection_action = list_action.DeleteSelection()
        delete_selection_action.gui_run( self.gui_context )
        self.process()
        self.assertFalse(selected_object in self.session)

    def test_add_existing_object(self):
        initial_row_count = self._row_count(self.item_model)
        action = list_action.AddExistingObject()
        steps = self.gui_run(action, self.gui_context)
        for step in steps:
            if isinstance(step, action_steps.SelectObjects):
                steps.send([Person(first_name='Unknown', last_name='Unknown')])
        new_row_count = self._row_count(self.item_model)
        self.assertEqual(new_row_count, initial_row_count+1)

    def test_add_new_object(self):
        add_new_object_action = list_action.AddNewObject()
        add_new_object_action.gui_run( self.gui_context )

    def test_remove_selection(self):
        remove_selection_action = list_action.RemoveSelection()
        list( remove_selection_action.model_run( self.gui_context.create_model_context() ) )

    def test_set_filters(self):
        action = list_action.SetFilters()
        steps = self.gui_run(action, self.gui_context)
        for step in steps:
            if isinstance(step, action_steps.ChangeField):
                steps.send(('first_name', 'test'))

    def test_group_box_filter(self):
        state = self.get_state(self.group_box_filter, self.gui_context)
        self.assertTrue(len(state.modes))
        widget = self.group_box_filter.render(self.gui_context, None)
        widget.set_state(state)
        self.assertTrue(len(widget.get_value()))
        widget.run_action()
        self.grab_widget(widget)

    def test_combo_box_filter(self):
        state = self.get_state(self.combo_box_filter, self.gui_context)
        self.assertTrue(len(state.modes))
        widget = self.combo_box_filter.render(self.gui_context, None)
        widget.set_state(state)
        self.assertTrue(len(widget.get_value()))
        widget.run_action()
        self.grab_widget(widget)

    def test_editor_filter(self):
        state = self.get_state(self.editor_filter, self.gui_context)
        self.assertTrue(len(state.modes))
        widget = self.editor_filter.render(self.gui_context, None)
        widget.set_state(state)
        self.assertTrue(len(widget.get_value()))
        widget.run_action()
        self.grab_widget(widget)

    def test_filter_list(self):
        action_box = actionsbox.ActionsBox(self.gui_context, None)
        action_box.set_actions([self.group_box_filter,
                                self.combo_box_filter])
        self.grab_widget(action_box)
        return action_box

    def test_filter_list_in_table_view(self):
        from camelot.view.controls.tableview import TableView
        from camelot.model.party import Person
        from camelot.admin.application_admin import ApplicationAdmin
        from camelot.admin.action.base import GuiContext
        gui_context = GuiContext()
        app_admin = ApplicationAdmin()
        person_admin = Person.Admin(app_admin, Person)
        table_view = TableView( gui_context, person_admin )
        table_view.set_filters([self.group_box_filter,
                                self.combo_box_filter])

    def test_orm( self ):

        class UpdatePerson( Action ):

            verbose_name = _('Update person')

            def model_run( self, model_context ):
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

            def model_run( self, model_context ):
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

            def model_run(self, model_context):
                from camelot.view.action_steps import PrintHtml
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
        self.app_admin = ApplicationAdmin()
        self.thread.post(self.setup_proxy)
        self.process()
        self.setup_item_model(self.app_admin.get_related_admin(Person))
        self.gui_context = form_action.FormActionGuiContext()
        self.gui_context._model = self.item_model
        self.gui_context.widget_mapper = QtWidgets.QDataWidgetMapper()
        self.gui_context.widget_mapper.setModel(self.item_model)
        self.gui_context.admin = self.app_admin.get_related_admin( Person )

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
        self.gui_context.admin = ApplicationAdmin()

    def test_application(self):
        app = Application(self.gui_context.admin)
        list(self.gui_run(app, self.gui_context))

    def test_custom_application(self):

        # begin custom application
        class CustomApplication(Application):
        
            def model_run( self, model_context ):
                from camelot.view import action_steps
                yield action_steps.UpdateProgress(text='Starting up')
        # end custom application

        application = CustomApplication(self.gui_context.admin)
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
        from camelot.admin.application_admin import ApplicationAdmin
        from camelot.view.workspace import DesktopWorkspace
        self.app_admin = ApplicationAdmin()
        self.context = MockModelContext(session=self.session)
        self.gui_context = application_action.ApplicationActionGuiContext()
        self.gui_context.admin = self.app_admin
        self.gui_context.workspace = DesktopWorkspace( self.app_admin, None )

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
        from . import test_core
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
            if isinstance(step, action_steps.SaveFile):
                generator.send('unittest-backup.db')
                file_saved = True
        self.assertTrue(file_saved)
        restore_action = application_action.Restore()
        generator = self.gui_run(restore_action, self.gui_context)
        file_selected = False
        for step in generator:
            if isinstance(step, action_steps.SelectFile):
                generator.send(['unittest-backup.db'])
                file_selected = True
        self.assertTrue(file_selected)

    def test_open_table_view(self):
        person_admin = self.app_admin.get_related_admin( Person )
        open_table_view_action = application_action.OpenTableView(person_admin)
        list(self.gui_run(open_table_view_action, self.gui_context))

    def test_open_new_view( self ):
        person_admin = self.app_admin.get_related_admin(Person)
        open_new_view_action = application_action.OpenNewView(person_admin)
        generator = self.gui_run(open_new_view_action, self.gui_context)
        for step in generator:
            if isinstance(step, action_steps.SelectSubclass):
                generator.send(person_admin)

    def test_change_logging( self ):
        change_logging_action = application_action.ChangeLogging()
        for step in change_logging_action.model_run( self.context ):
            if isinstance( step, action_steps.ChangeObject ):
                step.get_object().level = logging.INFO

    def test_segmentation_fault( self ):
        segmentation_fault = application_action.SegmentationFault()
        list(self.gui_run(segmentation_fault, self.gui_context))


class DocumentActionsCase(unittest.TestCase):
    """Test the standard document actions.
    """

    images_path = test_view.static_images_path

    def setUp( self ):
        self.gui_context = document_action.DocumentActionGuiContext()
        self.gui_context.document = QtGui.QTextDocument('Hello world')

    def test_gui_context( self ):
        self.assertTrue( isinstance( self.gui_context.copy(),
                                     document_action.DocumentActionGuiContext ) )
        self.assertTrue( isinstance( self.gui_context.create_model_context(),
                                     document_action.DocumentActionModelContext ) )

    def test_edit_document( self ):
        edit_document_action = document_action.EditDocument()
        model_context = self.gui_context.create_model_context()
        list( edit_document_action.model_run( model_context ) )
