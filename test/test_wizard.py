from camelot.test import ModelThreadTestCase

from test_view import static_images_path
        
class MergeDocumentWizardTest(ModelThreadTestCase):
    
    images_path = static_images_path
    
    def test_wizard_widget(self):
        from camelot.view.wizard.merge_document import MergeDocumentWizard
        wizard = MergeDocumentWizard(None, lambda:[])
        wizard.show()
        self.grab_widget( wizard )
