import os

from PyQt4 import QtGui

from camelot.test import ModelThreadTestCase

from test_view import static_images_path

class ActionWidgetsCase(ModelThreadTestCase):
    """Test widgets related to actions.
    """

    images_path = static_images_path

    def setUp(self):
        from camelot.admin.action import ApplicationActionGuiContext
        from camelot.admin.application_admin import ApplicationAdmin
        from camelot_example.importer import ImportCovers
        ModelThreadTestCase.setUp(self)
        self.app_admin = ApplicationAdmin()
        self.action = ImportCovers()
        self.application_gui_context = ApplicationActionGuiContext()
        self.parent = QtGui.QWidget()
        self.states = [ 'enabled', 'disabled', 'forbidden',
                        'hidden', 'notification' ]
        
    def grab_widget_states( self, widget, suffix ):
        for state in self.states:
            widget.set_state( state )
            self.grab_widget( widget, suffix='%s_%s'%( suffix,
                                                       state ) )
        
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
        
class ActionStepsCase(ModelThreadTestCase):
    """Test the various steps that can be executed during an
    action.
    """

    images_path = static_images_path
    
    def setUp(self):
        from camelot.admin.application_admin import ApplicationAdmin
        ModelThreadTestCase.setUp(self)
        self.app_admin = ApplicationAdmin()

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
        from camelot.view.action_steps import SelectOpenFile
        select_file = SelectOpenFile( 'Image Files (*.png *.jpg);;All Files (*)' )
        dialog = select_file.render()
        self.grab_widget( dialog )
