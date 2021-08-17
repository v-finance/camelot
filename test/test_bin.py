import os
import tempfile
import unittest

from camelot.bin.meta import CreateNewProject, templates
from camelot.view.action_steps import ChangeObject


class BinCase(unittest.TestCase):
    """test functions from camelot.bin
    """
            
    def test_create_new_project(self):
        new_project_action = CreateNewProject()
        for step in new_project_action.model_run( None ):
            if isinstance(step, ChangeObject):
                options = step.get_object()
                options.source = tempfile.mkdtemp('new_project')
        #
        # validate the generated files
        #
        for filename, _template in templates:
            code = open( os.path.join( options.source, 
                                       filename.replace('{{options.module}}', options.module) ) ).read()
            if filename.endswith('.py'):
                compile( code, 
                         filename,
                         'exec' )
        
