from camelot.admin.action.application_action import ApplicationAction
from camelot.core.utils import ugettext_lazy as _

class ImportCovers( ApplicationAction ):
    verbose_name = _('Import cover images')
    
# begin select files
    def model_run( self, model_context ):
        from camelot.view.action_steps import SelectOpenFile
        
        select_image_files = SelectOpenFile( 'Image Files (*.png *.jpg);;All Files (*)' )
        select_image_files.single = False
        file_names = yield select_image_files
# end select files
        print file_names