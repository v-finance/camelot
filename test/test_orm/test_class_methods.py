"""
    simple test case
"""

from camelot.core.orm import Session
from camelot.core.qt import QtCore
from sqlalchemy import schema
from sqlalchemy.types import String

from . import TestMetaData


class TestClassMethods( TestMetaData ):

    def test_get( self ):
        
        class A( self.Entity ):
            name = schema.Column(String(32))

        self.create_all()

        with self.session.begin():
            A(name="a1")

        self.session.expire_all()
        self.assertEqual(  A.get(1).name, "a1" )
        
    def test_query( self ):
        #
        # The query attribute of a class should return a query bound to
        # the session belonging to the current thread
        #
        
        class A( self.Entity ):
            name = schema.Column(String(32))
            
        self.create_all()
        
        with self.session.begin():
            A(name="a1")
            
        self.assertEqual( A.query.count(), 1 )
        
        session_1 = A.query.session
        self.assertEqual( session_1, Session() )
        
        class QueryThread( QtCore.QThread ):
            
            def run( self ):
                self.query_session_2 = A.query.session
                self.orm_session_2 = Session()
        
        thread = QueryThread()
        thread.start()
        thread.wait()
        
        self.assertNotEqual( session_1, thread.orm_session_2 )
        self.assertNotEqual( session_1, thread.query_session_2 )
