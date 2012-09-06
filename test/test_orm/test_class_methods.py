"""
    simple test case
"""

from . import TestMetaData

from camelot.core.orm import Field

from sqlalchemy.types import String, Unicode, Integer

class TestOldMethods( TestMetaData ):

    def test_get( self ):
        
        class A( self.Entity ):
            name = Field(String(32))

        self.create_all()

        with self.session.begin():
            a1 = A(name="a1")

        self.session.expire_all()

        assert A.get(1).name == "a1"

