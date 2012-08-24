import unittest

from camelot.core.orm import EntityBase, EntityMeta, Session

class TestMetaData( unittest.TestCase ):
    """Test case that provides setUp and tearDown
    of metadata separated from the camelot default
    metadata.  
    
    This can be used to setup and test various
    model configurations that dont interfer with 
    eachother.
    """
    
    def setUp(self):
        from sqlalchemy import MetaData
        from sqlalchemy.ext.declarative import declarative_base
        self.metadata = MetaData()
        self.class_registry = dict()
        self.Entity = declarative_base( cls = EntityBase, 
                                        metadata = self.metadata,
                                        metaclass = EntityMeta,
                                        class_registry = self.class_registry,
                                        constructor = None,
                                        name = 'Entity' )
        self.metadata.bind = 'sqlite://'
        self.session = Session()

    def create_all(self):
        from camelot.core.orm import process_deferred_properties
        process_deferred_properties( self.class_registry )
        self.metadata.create_all()
        
    def tearDown(self):
        self.metadata.drop_all()
        self.metadata.clear()