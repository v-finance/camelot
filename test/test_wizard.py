from camelot.test import ModelThreadTestCase
from camelot.view.wizard import importwizard

from test_view import static_images_path

class ImportWizardTest(ModelThreadTestCase):
    
    images_path = static_images_path
    
    def test_select_file_page(self):
        page = importwizard.SelectFilePage()
        self.grab_widget( page )
        
    def test_csv_wizard(self):
        from camelot.model.authentication import Person
        from camelot.admin.application_admin import ApplicationAdmin
        app_admin = ApplicationAdmin()
        person_admin = Person.Admin(app_admin, Person)
        wizard = importwizard.ImportWizard( admin=person_admin )
        # show appears to be needed to get a proper size of the widget
        wizard.show()
        self.grab_widget( wizard )         