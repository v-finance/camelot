"""
test the different syntaxes to define fields
"""
from . import TestMetaData

from camelot.core.orm import Field, has_field

from sqlalchemy.types import String

class TestFields( TestMetaData ):

    def test_attr_syntax(self):
        
        class Person(self.Entity):
            firstname = Field(String(30))
            surname = Field(String(30))

        self.create_all()

        self.session.begin()
        
        Person(firstname="Homer", surname="Simpson")
        Person(firstname="Bart", surname="Simpson")

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
        
        Person(firstname="Homer", surname="Simpson")
        Person(firstname="Bart", surname="Simpson")

        self.session.commit()
        self.session.expunge_all()

        p = Person.get_by(firstname="Homer")

        assert p.surname == 'Simpson'
