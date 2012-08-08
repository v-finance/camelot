import unittest
from camelot.test import ModelThreadTestCase

memento_id_counter = 0

class MementoCase( ModelThreadTestCase ):
    """test functions from camelot.core.memento
    """
    
    def setUp( self ):
        super( MementoCase, self ).setUp()
        from camelot.core.memento import SqlMemento
        global memento_id_counter
        self.memento = SqlMemento()
        memento_id_counter += 1
        self.id_counter = memento_id_counter
        self.model = 'TestMemento'
        
    def test_update( self ):
        self.memento.register_update( self.model,
                                      [self.id_counter],
                                      {'name':'foo'} )
        changes = list( self.memento.get_changes( self.model,
                                                  [self.id_counter],
                                                  {'name':'bar'} ) )
        self.assertEqual( len(changes), 1 )

    def test_delete( self ):
        self.memento.register_delete( self.model,
                                      [self.id_counter],
                                      {'name':'foo'} )
        changes = list( self.memento.get_changes( self.model,
                                                  [self.id_counter],
                                                  {'name':'foo'} ) )
        self.assertEqual( len(changes), 1 )

    def test_create( self ):
        self.memento.register_create( self.model,
                                      [self.id_counter] )
        changes = list( self.memento.get_changes( self.model,
                                                  [self.id_counter],
                                                  {'name':'foo'} ) )
        self.assertEqual( len(changes), 1 )
        
class ConfCase(unittest.TestCase):
    """Test the global configuration"""
    
    def test_import_settings(self):
        from camelot.core.conf import settings
        self.assertRaises( AttributeError, lambda:settings.FOO )
        self.assertTrue( settings.CAMELOT_MEDIA_ROOT.endswith( 'media' ) )
