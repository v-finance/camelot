"""
test special properties (eg. column_property, ...)
"""

import logging

from . import TestMetaData

from camelot.core.orm import ( Field, GenericProperty, ColumnProperty, 
                               ManyToOne, OneToMany, has_field, has_property )

from sqlalchemy.types import String, Float, Text
from sqlalchemy import select, func
from sqlalchemy.orm import column_property

class TestSpecialProperties( TestMetaData ):

    def test_lifecycle(self):
        
        class A( self.Entity ):
            name = Field( String( 20 ) )

        assert not isinstance( A.name, Field )

    def test_generic_property(self):
        
        class Tag( self.Entity ):
            score1 = Field(Float)
            score2 = Field(Float)

            score = GenericProperty(
                         lambda c: column_property(
                             (c.score1 * c.score2).label('score')))

        self.create_all()
        with self.session.begin():
            t1 = Tag(score1=5.0, score2=3.0)
            t2 = Tag(score1=10.0, score2=2.0)

        self.session.expunge_all()

        for tag in Tag.query.all():
            assert tag.score == tag.score1 * tag.score2

    def test_column_property(self):
        
        class Tag( self.Entity ):
            score1 = Field(Float)
            score2 = Field(Float)

            score = ColumnProperty(lambda c: c.score1 * c.score2)

        self.create_all()
        with self.session.begin():
            t1 = Tag(score1=5.0, score2=3.0)
            t2 = Tag(score1=10.0, score2=2.0)

        self.session.expunge_all()

        for tag in Tag.query.all():
            assert tag.score == tag.score1 * tag.score2

    def test_column_property_eagerload_and_reuse(self):
        
        class Tag(self.Entity):
            score1 = Field(Float)
            score2 = Field(Float)

            user = ManyToOne('User')

            score = ColumnProperty(lambda c: c.score1 * c.score2)

        class User(self.Entity):
            name = Field(String(16))
            category = ManyToOne('Category')
            tags = OneToMany('Tag', lazy=False)
            score = ColumnProperty(lambda c:
                                   select([func.sum(Tag.score)],
                                          Tag.user_id == c.id).as_scalar())

        class Category(self.Entity):
            name = Field(String(16))
            users = OneToMany('User', lazy=False)

            score = ColumnProperty(lambda c:
                                   select([func.avg(User.score)],
                                          User.category_id == c.id
                                         ).as_scalar())
            
        self.create_all()
            
        with self.session.begin():
            u1 = User(name='joe', tags=[Tag(score1=5.0, score2=3.0),
                                             Tag(score1=55.0, score2=1.0)] )
    
            u2 = User(name='bar', tags=[Tag(score1=5.0, score2=4.0),
                                             Tag(score1=50.0, score2=1.0),
                                             Tag(score1=15.0, score2=2.0)])
    
            c1 = Category(name='dummy', users=[u1, u2] )

        self.session.expunge_all()

        category = Category.query.one()
        assert len( category.users ) == 2 
        for user in category.users:
            assert len( user.tags ) > 0
            assert user.score == sum([tag.score for tag in user.tags])
            for tag in user.tags:
                assert tag.score == tag.score1 * tag.score2
        assert category.score == 85


    def test_has_property(self):
        
        class Tag( self.Entity ):
            has_field('score1', Float)
            has_field('score2', Float)
            has_property('score',
                         lambda c: column_property(
                             (c.score1 * c.score2).label('score')))

        self.create_all()
        with self.session.begin():
            t1 = Tag(score1=5.0, score2=3.0)
            t1 = Tag(score1=10.0, score2=2.0)

        self.session.expunge_all()

        for tag in Tag.query.all():
            assert tag.score == tag.score1 * tag.score2

    def test_deferred(self):
        
        class A( self.Entity ):
            name = Field(String(20))
            stuff = Field(Text, deferred=True)

        self.create_all()
        with self.session.begin():
            A(name='foo')

    def test_setattr(self):
        
        class A( self.Entity ):
            pass

        A.name = Field(String(30))
        
        self.create_all()
        with self.session.begin():    
            a1 = A(name='a1')

        self.session.expunge_all()

        a = A.query.one()

        assert a.name == 'a1'

