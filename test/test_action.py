import datetime
import logging
import os
import unittest

import openpyxl

from sqlalchemy import orm

import six

from camelot.core.item_model import ListModelProxy, ObjectRole
from camelot.admin.application_admin import ApplicationAdmin
from camelot.admin.action import Action, GuiContext, ActionStep, State, Mode
from camelot.admin.action import (list_action, application_action,
                                  document_action, form_action,
                                  list_filter, ApplicationActionGuiContext)
from camelot.admin.action.application import Application
from camelot.core.item_model import ListModelProxy, ObjectRole
from camelot.core.qt import QtGui, QtWidgets, QtCore, Qt
from camelot.core.exception import CancelRequest, UserException
from camelot.core.utils import ugettext_lazy as _
from camelot.core.orm import Session

from camelot.model import party
from camelot.model.party import Person

from camelot.test import GrabMixinCase, RunningThreadCase
from camelot.test.action import MockModelContext
from camelot.view.action_steps.orm import AbstractCrudSignal
from camelot.view.action_runner import ActionRunner
from camelot.view import action_steps, import_utils
from camelot.view.proxy.collection_proxy import CollectionProxy
from camelot.view.controls import tableview, actionsbox, progress_dialog
from camelot.view import utils
from camelot.view.import_utils import (
    RowData, ColumnMapping, MatchNames, ColumnMappingAdmin
)

from camelot_example.model import Movie

from . import test_view
from . import test_model
from .test_item_model import QueryQStandardItemModelMixinCase
from .test_model import ExampleModelCase, ExampleModelMixinCase

test_images = [os.path.join( os.path.dirname(__file__), '..', 'camelot_example', 'media', 'covers', 'circus.png') ]

LOGGER = logging.getLogger(__name__)


class ActionBaseCase(RunningThreadCase):

    def setUp(self):
        super(ActionBaseCase, self).setUp()
        self.gui_context = GuiContext()
        self.gui_context.admin = ApplicationAdmin()

    def test_action_step( self ):
        step = ActionStep()
        step.gui_run( self.gui_context )

    def test_action( self ):

        class CustomAction( Action ):
            shortcut = QtGui.QKeySequence.New

        action = CustomAction()
        action.gui_run( self.gui_context )
        self.assertTrue( action.get_name() )
        self.assertTrue( action.get_shortcut() )

class ActionWidgetsCase(unittest.TestCase, GrabMixinCase):
    """Test widgets related to actions.
    """

    images_path = test_view.static_images_path

    def setUp(self):
        from camelot_example.importer import ImportCovers
        self.app_admin = ApplicationAdmin()
        self.action = ImportCovers()
        self.application_gui_context = ApplicationActionGuiContext()
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
                                   self.application_gui_context,
                                   self.parent )
        self.grab_widget_states( widget, 'application' )

    def test_hide_progress_dialog( self ):
        from camelot.view.action_runner import hide_progress_dialog
        dialog = progress_dialog.ProgressDialog("test")
        dialog.show()
        self.application_gui_context.progress_dialog = dialog
        with hide_progress_dialog( self.application_gui_context ):
            self.assertTrue( dialog.isHidden() )
        self.assertFalse( dialog.isHidden() )

class ActionStepsCase(RunningThreadCase, GrabMixinCase, ExampleModelMixinCase):
    """Test the various steps that can be executed during an
    action.
    """

    images_path = test_view.static_images_path

    @classmethod
    def setUpClass(cls):
        super(ActionStepsCase, cls).setUpClass()
        cls.setup_sample_model()

    def setUp(self):
        ExampleModelCase.setUp(self)
        from camelot_example.model import Movie
        from camelot.admin.application_admin import ApplicationAdmin
        self.load_example_data()
        self.app_admin = ApplicationAdmin()
        self.context = MockModelContext()
        self.context.obj = Movie.query.first()
        self.gui_context = GuiContext()

# begin test application action
    def test_example_application_action( self ):
        from camelot_example.importer import ImportCovers
        from camelot_example.model import Movie
        # count the number of movies before the import
        movies = Movie.query.count()
        # create an import action
        action = ImportCovers()
        generator = action.model_run( None )
        select_file = six.advance_iterator( generator )
        self.assertFalse( select_file.single )
        # pretend the user selected a file
        generator.send(test_images)
        # continue the action till the end
        list( generator )
        # a movie should be inserted
        self.assertEqual( movies + 1, Movie.query.count() )
# end test application action

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
        from camelot.view.action_steps import SelectFile
        select_file = SelectFile( 'Image Files (*.png *.jpg);;All Files (*)' )

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

        # end select item

        action = SendDocumentAction()
        for step in action.model_run( self.context ):
            dialog = step.render()
            self.grab_widget( dialog )

    def test_text_document( self ):
        # begin text document
        class EditDocumentAction( Action ):

            def model_run( self, model_context ):
                document = QtGui.QTextDocument()
                document.setHtml( '<h3>Hello World</h3>')
                yield action_steps.EditTextDocument( document )
        # end text document

        action = EditDocumentAction()
        for step in action.model_run( self.context ):
            dialog = step.render()
            self.grab_widget( dialog )

    def test_print_html( self ):

        # begin html print
        class MovieSummary( Action ):

            verbose_name = _('Summary')

            def model_run(self, model_context):
                from camelot.view.action_steps import PrintHtml
                movie = model_context.get_object()
                yield PrintHtml( "<h1>This will become the movie report of %s!</h1>" % movie.title )
        # end html print

        action = MovieSummary()
        steps = list( action.model_run( self.context ) )
        dialog = steps[0].render( self.gui_context )
        dialog.show()
        self.grab_widget( dialog )

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

    def test_orm( self ):
        # prepare the model context
        contact = party.ContactMechanism( mechanism = ('email', 'info@test.be') )
        person = party.Person( first_name = u'Living',
                               last_name = u'Stone',
                               social_security_number = u'2003030212345' )
        party.PartyContactMechanism( party = person,
                                     contact_mechanism = contact )
        self.context.obj = person
        self.context.session.flush()

        # begin manual update

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

        update_person = UpdatePerson()
        for step in update_person.model_run( self.context ):
            step.gui_run( self.gui_context )

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

        update_person = UpdatePerson()
        for step in update_person.model_run( self.context ):
            step.gui_run( self.gui_context )

    def test_update_progress( self ):
        from camelot.view.controls.progress_dialog import ProgressDialog
        update_progress = action_steps.UpdateProgress( 20, 100, _('Importing data') )
        self.assertTrue( six.text_type( update_progress ) )
        # give the gui context a progress dialog, so it can be updated
        self.gui_context.progress_dialog = ProgressDialog('Progress')
        update_progress.gui_run( self.gui_context )
        # now press the cancel button
        self.gui_context.progress_dialog.cancel()
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
        super(ListActionsCase, cls).setUpClass()
        ##cls.setup_sample_model()
        cls.thread.post(cls.setup_sample_model)
        cls.thread.post(cls.load_example_data)
        cls.group_box_filter = list_filter.GroupBoxFilter(
            'last_name', exclusive=True
        )
        cls.combo_box_filter = list_filter.ComboBoxFilter('last_name')
        cls.editor_filter = list_filter.EditorFilter('last_name')
        cls.process()

    def setUp( self ):
        super(ListActionsCase, self).setUp()
        self.thread.post(self.session.close)
        self.process()
        ##self.load_example_data()
        self.app_admin = ApplicationAdmin()
        self.admin = self.app_admin.get_related_admin(Person)
        self.setup_item_model(self.admin)
        self.movie_admin = self.app_admin.get_related_admin(Movie)
        
        ##item_model = CollectionProxy(self.movie_admin)
        ##list(item_model.add_columns(self.movie_admin.list_display))
        ##item_model.set_value(self.movie_admin.get_proxy(self.session.query(Movie)))
        # make sure the model has rows and header data
        self._load_data(self.item_model)
        ##item_model.rowCount()
        ##item_model.timeout_slot()
        ##item_model.headerData(0, Qt.Vertical, ObjectRole)
        ##item_model.timeout_slot()
        table_view = tableview.AdminTableWidget(self.admin)
        table_view.setModel(self.item_model)
        # make sure there is data at (0,0), so it can be selected
        ##item_model.data(item_model.index(0,0), Qt.DisplayRole)
        ##item_model.timeout_slot()
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

    def test_sqlalchemy_command( self ):
        model_context = self.context
        from camelot.model.batch_job import BatchJobType
        # create a batch job to test with
        bt = BatchJobType( name = 'audit' )
        model_context.session.add( bt )
        bt.flush()
        # begin issue a query through the model_context
        model_context.session.query( BatchJobType ).update( values = {'name':'accounting audit'},
                                                            synchronize_session = 'evaluate' )
        # end issue a query through the model_context
        #
        # the batch job should have changed
        self.assertEqual( bt.name, 'accounting audit' )

    def test_change_row_actions( self ):
        from camelot.test.action import MockListActionGuiContext

        gui_context = MockListActionGuiContext()
        get_state = lambda action:action.get_state( gui_context.create_model_context() )
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
        replace = list_action.ReplaceFieldContents()
        generator = replace.model_run( self.context )
        for step in generator:
            if isinstance( step, action_steps.ChangeField ):
                dialog = step.render()
                field_editor = dialog.findChild(QtWidgets.QWidget, 'field_choice')
                field_editor.set_value( 'rating' )
                dialog.show()
                self.grab_widget( dialog )
                generator.send( ('rating', 3) )

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

    @classmethod
    def get_state(cls, action, gui_context):
        """
        Get the state of an action in the model thread and return
        the result.
        """
        model_context = gui_context.create_model_context()

        class StateRegister(QtCore.QObject):

            def __init__(self):
                super(StateRegister, self).__init__()
                self.state = None

            @QtCore.qt_slot(object)
            def set_state(self, state):
                self.state = state

        state_register = StateRegister()
        cls.thread.post(
            action.get_state, state_register.set_state, args=(model_context,)
        )
        cls.process()
        return state_register.state

    @classmethod
    def gui_run(cls, action, gui_context):
        """
        Simulates the gui_run of an action, but instead of blocking,
        yields progress each time a message is received from the model.
        """

        class IteratingActionRunner(ActionRunner):

            def __init__(self, generator_function, gui_context):
                super(IteratingActionRunner, self).__init__(
                    generator_function, gui_context
                )
                self.return_queue = []
                self.exception_queue = []
                cls.process()

            @QtCore.qt_slot( object )
            def generator(self, generator):
                LOGGER.debug('got generator')
                self._generator = generator

            @QtCore.qt_slot( object )
            def exception(self, exception_info):
                LOGGER.debug('got exception {}'.format(exception_info))
                self.exception_queue.append(exception_info)

            @QtCore.qt_slot( object )
            def __next__(self, yielded):
                LOGGER.debug('got step {}'.format(yielded))
                self.return_queue.append(yielded)

            def run(self):
                super(IteratingActionRunner, self).generator(self._generator)
                cls.process()
                step = self.return_queue.pop()
                while isinstance(step, ActionStep):
                    if isinstance(step, AbstractCrudSignal):
                        LOGGER.debug('crud step, update view')
                        step.gui_run(gui_context)
                    LOGGER.debug('yield step {}'.format(step))
                    gui_result = yield step
                    LOGGER.debug('post result {}'.format(gui_result))
                    cls.thread.post(
                        self._iterate_until_blocking,
                        self.__next__,
                        self.exception,
                        args = (self._generator.send, gui_result,)
                    )
                    cls.process()
                    if len(self.exception_queue):
                        raise Exception(self.exception_queue.pop().text)
                    step = self.return_queue.pop()
                LOGGER.debug("iteration finished")
                yield None

        runner = IteratingActionRunner(action.model_run, gui_context)
        yield from runner.run()

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
        set_filters = list_action.SetFilters()
        generator = set_filters.model_run(self.context)
        for step in generator:
            if isinstance(step, action_steps.ChangeField):
                generator.send(('name', 'test'))

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

class FormActionsCase(
    unittest.TestCase,
    ExampleModelMixinCase, GrabMixinCase, QueryQStandardItemModelMixinCase):
    """Test the standard list actions.
    """

    images_path = test_view.static_images_path

    @classmethod
    def setUpClass(cls):
        super(FormActionsCase, cls).setUpClass()
        cls.setup_sample_model()

    def setUp( self ):
        super(FormActionsCase, self).setUp()
        self.app_admin = ApplicationAdmin()
        self.load_example_data()
        self.setup_item_model(self.app_admin.get_related_admin(Person))
        self.model_context = MockModelContext()
        self.model_context.obj = Person.query.first()
        self.model_context.admin = self.app_admin.get_related_admin( Person )
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
        previous_action.gui_run( self.gui_context )
        next_action = form_action.ToNextForm()
        next_action.gui_run( self.gui_context )
        first_action = form_action.ToFirstForm()
        first_action.gui_run( self.gui_context )
        last_action = form_action.ToLastForm()
        last_action.gui_run( self.gui_context )

    def test_show_history( self ):
        show_history_action = form_action.ShowHistory()
        list( show_history_action.model_run( self.model_context ) )

    def test_close_form( self ):
        close_form_action = form_action.CloseForm()
        list( close_form_action.model_run( self.model_context ) )

class ApplicationCase(RunningThreadCase, GrabMixinCase):

    def setUp(self):
        super( ApplicationCase, self ).setUp()
        self.app_admin = ApplicationAdmin()
        self.context = MockModelContext()
        self.context.admin = self.app_admin

    def test_application(self):
        app = Application(self.app_admin)
        list(app.model_run(self.context))
        
    def test_custom_application(self):

        # begin custom application
        class CustomApplication(Application):
        
            def model_run( self, model_context ):
                from camelot.view import action_steps
                yield action_steps.UpdateProgress(text='Starting up')
        # end custom application
        
        application = CustomApplication(self.app_admin)
        application.gui_run(GuiContext())

class ApplicationActionsCase(
    RunningThreadCase, GrabMixinCase, ExampleModelMixinCase
    ):
    """Test application actions.
    """

    images_path = test_view.static_images_path

    @classmethod
    def setUpClass(cls):
        super(ApplicationActionsCase, cls).setUpClass()
        cls.setup_sample_model()

    def setUp(self):
        super( ApplicationActionsCase, self ).setUp()
        from camelot.admin.application_admin import ApplicationAdmin
        from camelot.core.files.storage import Storage
        from camelot.view.workspace import DesktopWorkspace
        self.app_admin = ApplicationAdmin()
        self.context = MockModelContext(session=self.session)
        self.storage = Storage()
        self.gui_context = application_action.ApplicationActionGuiContext()
        self.gui_context.admin = self.app_admin
        self.gui_context.workspace = DesktopWorkspace( self.app_admin, None )

    def test_refresh( self ):
        from camelot.core.orm import Session
        from camelot.model.party import Person
        refresh_action = application_action.Refresh()
        session = Session()
        session.expunge_all()
        # create objects in various states
        #
        p1 = Person(first_name = u'p1', last_name = u'persistent' )
        p2 = Person(first_name = u'p2', last_name = u'dirty' )
        p3 = Person(first_name = u'p3', last_name = u'deleted' )
        p4 = Person(first_name = u'p4', last_name = u'to be deleted' )
        p5 = Person(first_name = u'p5', last_name = u'detached' )
        p6 = Person(first_name = u'p6', last_name = u'deleted outside session' )
        session.flush()
        p3.delete()
        session.flush()
        p4.delete()
        p2.last_name = u'clean'
        #
        # delete p6 without the session being aware
        #
        person_table = Person.table
        session.execute( person_table.delete().where( person_table.c.party_id == p6.id ) )
        #
        # refresh the session through the action
        #
        list( refresh_action.model_run( self.context ) )
        self.assertEqual( p2.last_name, u'dirty' )

    def test_select_profile(self):
        from . import test_core
        profile_case = test_core.ProfileCase('setUp')
        profile_case.setUp()
        profile_store = profile_case.test_profile_store()
        action = application_action.SelectProfile(profile_store)
        generator = action.model_run(self.context)
        for step in generator:
            if isinstance(step, action_steps.SelectItem):
                generator.send(profile_store.get_last_profile())

    def test_backup_and_restore( self ):
        backup_action = application_action.Backup()
        generator = backup_action.model_run( self.context )
        for step in generator:
            if isinstance( step, action_steps.SelectBackup ):
                dialog = step.render()
                dialog.show()
                self.grab_widget( dialog, suffix = 'backup' )
                generator.send( ('unittest', self.storage) )
        restore_action = application_action.Restore()
        generator = restore_action.model_run( self.context )
        for step in generator:
            if isinstance( step, action_steps.SelectRestore ):
                dialog = step.render()
                dialog.show()
                self.grab_widget( dialog, suffix = 'restore' )
                generator.send( ('unittest', self.storage) )

    def test_change_logging( self ):
        change_logging_action = application_action.ChangeLogging()
        change_logging_action.model_run( self.context )

    def test_open_table_view( self ):
        from camelot.model.party import Person
        person_admin = self.app_admin.get_related_admin( Person )
        open_table_view_action = application_action.OpenTableView( person_admin )
        open_table_view_action.gui_run( self.gui_context )

    def test_open_new_view( self ):
        from camelot.model.party import Person
        person_admin = self.app_admin.get_related_admin( Person )
        open_new_view_action = application_action.OpenNewView( person_admin )
        open_new_view_action.gui_run( self.gui_context )

    def test_change_logging( self ):
        change_logging_action = application_action.ChangeLogging()
        for step in change_logging_action.model_run( self.context ):
            if isinstance( step, action_steps.ChangeObject ):
                step.get_object().level = logging.INFO

    def test_segmentation_fault( self ):
        segmentation_fault = application_action.SegmentationFault()
        list( segmentation_fault.model_run( self.context ) )

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
