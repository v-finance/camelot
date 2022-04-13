import unittest

from sqlalchemy import MetaData
from sqlalchemy.ext.declarative import declarative_base

from camelot.core.orm import EntityBase, EntityMeta, Session

class EntityMetaMock(EntityMeta):
    """
    Specialized EntityMeta mock used for testing that enables rebinding of entity naming contexts.
    This allows test cases to define multiple Entities with the same name on the same table.
    """
    rebind = True

class TestMetaData( unittest.TestCase ):
    """Test case that provides setUp and tearDown
    of metadata separated from camelot default
    metadata.  
    
    This can be used to setup and test various
    model configurations that dont interfer with 
    eachother.
    """
    
    def setUp(self):
        self.metadata = MetaData()
        self.class_registry = dict()
        self.Entity = declarative_base( cls = EntityBase, 
                                        metadata = self.metadata,
                                        metaclass = EntityMetaMock,
                                        class_registry = self.class_registry,
                                        constructor = None,
                                        name = 'Entity' )
        self.metadata.bind = 'sqlite://'
        self.session = Session()

    def create_all(self):
        self.metadata.create_all()
        
    def tearDown(self):
        self.metadata.drop_all()
        self.metadata.clear()
