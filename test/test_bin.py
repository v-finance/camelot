import tempfile
import unittest
import os

class BinCase(unittest.TestCase):
    """test functions from camelot.bin
    """
            
    def test_create_new_project(self):
        from camelot.bin.meta import CreateNewProject, templates
        new_project_action = CreateNewProject('Create New Project')
        options = CreateNewProject.Options()
        options.source = tempfile.mkdtemp()
        new_project_action.model_run( options )
        #
        # validate the generated files
        #
        for filename, _template in templates:
            code = open( os.path.join( options.source, 
                                       options.module,
                                       filename ) ).read()
            compile( code, 
                     filename,
                     'exec' )
        