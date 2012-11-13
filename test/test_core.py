import unittest

from camelot.core.memento import memento_change, memento_types
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
        
    def test_lifecycle( self ):
        
        memento_changes = [
            memento_change( self.model, 
                            [self.id_counter], 
                            None, 'create' ),            
            memento_change( self.model, 
                            [self.id_counter], 
                            {'name':'foo'}, 'before_update' ),
            memento_change( self.model, 
                            [self.id_counter], 
                            {'name':'bar'}, 'before_delete' ),            
            ]
        
        self.memento.register_changes( memento_changes )
        changes = list( self.memento.get_changes( self.model,
                                                  [self.id_counter],
                                                  {} ) )
        self.assertEqual( len(changes), 3 )
        
    def test_no_error( self ):
        memento_changes = [
            memento_change( None, 
                            [self.id_counter], 
                            None, None ),                     
            ]
        self.memento.register_changes( memento_changes )
        
    def test_custom_memento_type( self ):
        memento_types.append( (100, 'custom') )
        memento_changes = [
            memento_change( self.model, 
                            [self.id_counter], 
                            {}, 'custom' ),                     
            ]
        self.memento.register_changes( memento_changes )
        changes = list( self.memento.get_changes( self.model,
                                                  [self.id_counter],
                                                  {} ) )
        self.assertEqual( len(changes), 1 )
                        
class ConfCase(unittest.TestCase):
    """Test the global configuration"""
    
    def test_import_settings(self):
        from camelot.core.conf import settings
        self.assertRaises( AttributeError, lambda:settings.FOO )
        self.assertTrue( settings.CAMELOT_MEDIA_ROOT.endswith( 'media' ) )
        
class AutoReloadCase( ModelThreadTestCase ):
    """Test the auto reload functions"""
    
    def test_source_changed( self ):
        pass
        #from camelot.core.auto_reload import auto_reload
        #auto_reload.source_changed( None )
