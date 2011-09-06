from camelot.test import ModelThreadTestCase

from test_view import static_images_path

class ActionStepsCase(ModelThreadTestCase):
    """Test the various steps that can be executed during an
    action.
    """

    images_path = static_images_path
    
    def setUp(self):
        from camelot.admin.application_admin import ApplicationAdmin
        ModelThreadTestCase.setUp(self)
        self.app_admin = ApplicationAdmin()
        
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
