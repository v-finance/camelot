from . import TestMetaData

from camelot.core.orm import Field, OneToOne, ManyToOne

from sqlalchemy.types import String, Unicode, Integer

class TestOneToOne( TestMetaData ):

    def test_simple( self ):
        
        class A( self.Entity ):
            name = Field(String(60))
            b = OneToOne('B')

        class B( self.Entity ):
            name = Field(String(60))
            a = ManyToOne('A')

        self.create_all()
        with self.session.begin():
            b1 = B(name='b1', a=A(name='a1'))

        self.session.expire_all()

        b = B.query.one()
        a = b.a

        assert b == a.b


