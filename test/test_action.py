import os

from PyQt4 import QtGui

from camelot.admin.action import Action
from camelot.admin.action import list_action
from camelot.core.utils import ugettext_lazy as _
from camelot.test import ModelThreadTestCase
from camelot.test.action import MockModelContext

from test_view import static_images_path

class ActionWidgetsCase( ModelThreadTestCase ):
    """Test widgets related to actions.
    """

    images_path = static_images_path

    def setUp(self):
        from camelot.admin.action import ApplicationActionGuiContext, State
        from camelot.admin.application_admin import ApplicationAdmin
        from camelot_example.importer import ImportCovers
        ModelThreadTestCase.setUp(self)
        self.app_admin = ApplicationAdmin()
        self.action = ImportCovers()
        self.application_gui_context = ApplicationActionGuiContext()
        self.parent = QtGui.QWidget()
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
        
    def test_action_label( self ):
        from camelot.view.controls.action_widget import ActionLabel
        widget = ActionLabel( self.action,
                              self.application_gui_context,
                              self.parent )
        self.grab_widget_states( widget, 'application' )

    def test_action_push_botton( self ):
        from camelot.view.controls.action_widget import ActionPushButton
        widget = ActionPushButton( self.action,
                                   self.application_gui_context,
                                   self.parent )
        self.grab_widget_states( widget, 'application' )
        
class ActionStepsCase( ModelThreadTestCase ):
    """Test the various steps that can be executed during an
    action.
    """

    images_path = static_images_path
    
    def setUp(self):
        from camelot_example.model import Movie
        from camelot.admin.application_admin import ApplicationAdmin
        ModelThreadTestCase.setUp(self)
        self.app_admin = ApplicationAdmin()
        self.context = MockModelContext()
        self.context.obj = Movie.query.first()

# begin test application action
    def test_example_application_action( self ):
        from camelot_example.importer import ImportCovers
        from camelot_example.model import Movie
        # count the number of movies before the import
        movies = Movie.query.count()
        # create an import action
        action = ImportCovers()
        generator = action.model_run( None )
        select_file = generator.next()
        self.assertFalse( select_file.single )
        # pretend the user selected a file
        generator.send( [os.path.join( os.path.dirname(__file__), '..', 'camelot_example', 'media', 'covers', 'circus.jpg') ] )
        # continue the action till the end
        list( generator )
        # a movie should be inserted
        self.assertEqual( movies + 1, Movie.query.count() )
# end test application action

    def test_change_object( self ):
        from camelot.bin.meta import NewProjectOptions
        from camelot.view.action_steps.change_object import ChangeObjectDialog
        admin = NewProjectOptions.Admin( self.app_admin, NewProjectOptions )
        options = NewProjectOptions()
        options.name = 'Videostore'
        options.module = 'videostore'
        options.domain = 'example.com'
        dialog = ChangeObjectDialog( options, admin )
        self.grab_widget( dialog )
        
    def test_select_file( self ):
        from camelot.view.action_steps import SelectFile
        select_file = SelectFile( 'Image Files (*.png *.jpg);;All Files (*)' )
        dialog = select_file.render()
        self.grab_widget( dialog )
        
    def test_print_preview( self ):
        
        # begin webkit print
        class WebkitPrint( Action ):
            
            def model_run( self, model_context ):
                from PyQt4.QtWebKit import QWebView
                from camelot.view.action_steps import PrintPreview
                
                movie = model_context.get_object()
                
                document = QWebView()
                document.setHtml( '<h2>%s</h2>' % movie.title )
                
                yield PrintPreview( document )
        # end webkit print
                
        action = WebkitPrint()
        steps = list( action.model_run( self.context ) )
        dialog = steps[0].render()
        dialog.show()
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
        dialog = steps[0].render()
        dialog.show()
        self.grab_widget( dialog )

class ListActionsCase( ModelThreadTestCase ):
    """Test the standard list actions.
    """

    images_path = static_images_path

    def setUp( self ):
        from camelot_example.model import Movie
        from camelot.admin.application_admin import ApplicationAdmin
        ModelThreadTestCase.setUp(self)
        self.app_admin = ApplicationAdmin()
        self.context = MockModelContext()
        self.context.obj = Movie.query.first()
        self.context.admin = self.app_admin.get_related_admin( Movie )
        
    def test_change_row_actions( self ):
        from camelot.test.action import MockListActionGuiContext
        
        gui_context = MockListActionGuiContext()
        get_state = lambda action:action.get_state( gui_context.create_model_context() )
        to_first = list_action.ToFirstRow()
        to_previous = list_action.ToPreviousRow()
        to_next = list_action.ToNextRow()
        to_last = list_action.ToLastRow()
        
        to_last.gui_run( gui_context )
        self.assertFalse( get_state( to_last ).enabled )
        self.assertFalse( get_state( to_next ).enabled )
        to_previous.gui_run( gui_context )
        self.assertTrue( get_state( to_last ).enabled )
        self.assertTrue( get_state( to_next ).enabled )
        to_first.gui_run( gui_context )
        self.assertFalse( get_state( to_first ).enabled )
        self.assertFalse( get_state( to_previous ).enabled )
        to_next.gui_run( gui_context )
        self.assertTrue( get_state( to_first ).enabled )
        self.assertTrue( get_state( to_previous ).enabled )
        
    def test_print_preview( self ):
        print_preview = list_action.PrintPreview()
        for step in print_preview.model_run( self.context ):
            dialog = step.render()
            dialog.show()
            self.grab_widget( dialog )
