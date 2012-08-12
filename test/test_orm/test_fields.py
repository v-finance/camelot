"""
test the different syntaxes to define fields
"""
import unittest

from camelot.core.sql import metadata
from camelot.core.orm import EntityBase, EntityMeta, Field, Session, has_field

from sqlalchemy.types import String

class TestFields( unittest.TestCase ):

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
        self.metadata.create_all()
        process_deferred_properties( self.class_registry )
        
    def tearDown(self):
        self.metadata.drop_all()
        self.metadata.clear()

    def test_attr_syntax(self):
        
        class Person(self.Entity):
            firstname = Field(String(30))
            surname = Field(String(30))

        self.create_all()

        self.session.begin()
        
        homer = Person(firstname="Homer", surname="Simpson")
        bart = Person(firstname="Bart", surname="Simpson")

        self.session.commit()
        self.session.expunge_all()

        p = Person.get_by(firstname="Homer")

        assert p.surname == 'Simpson'

    def test_has_field(self):
        
        class Person(self.Entity):
            has_field('firstname', String(30))
            has_field('surname', String(30))

        self.create_all()

        self.session.begin()
        
        homer = Person(firstname="Homer", surname="Simpson")
        bart = Person(firstname="Bart", surname="Simpson")

        self.session.commit()
        self.session.expunge_all()

        p = Person.get_by(firstname="Homer")

        assert p.surname == 'Simpson'
