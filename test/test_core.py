import unittest
from camelot.test import ModelThreadTestCase

class CoreCase(ModelThreadTestCase):
    """test functions from camelot.core
    """
    pass
        
class ConfCase(unittest.TestCase):
    """Test the global configuration"""
    
    def test_import_settings(self):
        from camelot.core.conf import settings
        self.assertRaises( AttributeError, lambda:settings.FOO )
        self.assertTrue( settings.CAMELOT_MEDIA_ROOT.endswith( 'media' ) )
