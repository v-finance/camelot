import tempfile
import unittest
import os

class BinCase(unittest.TestCase):
    """test functions from camelot.bin
    """
            
    def test_create_new_project(self):
        from camelot.bin.meta import CreateNewProject, templates, NewProjectOptions
        new_project_action = CreateNewProject()
        options = NewProjectOptions()
        options.source = 'new_project' 
        new_project_action.start_project( options )
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
        
