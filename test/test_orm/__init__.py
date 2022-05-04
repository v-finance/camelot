import unittest

from sqlalchemy import MetaData
from sqlalchemy.ext.declarative import declarative_base

from camelot.core.orm import EntityBase, EntityMeta, Session

class EntityMetaMock(EntityMeta):
    """
    Specialized EntityMeta mock used for testing that overwrites the default assignment of
    the __entity_args__ entity name argument in a way that allows test cases to define multiple Entities
    with the same name.
    """

    def _default_entity_name(cls, classname, dict_):
        entity_name = super()._default_entity_name(cls, classname, dict_)
        return '{}_{}'.format(entity_name, id(entity_name))

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
