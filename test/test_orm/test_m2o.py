"""
test many to one relationships
"""

import logging

from . import TestMetaData

from camelot.core.orm import ( Field, OneToMany, ManyToOne, using_options,
                               has_field, has_many, belongs_to )

from sqlalchemy.types import String, Unicode, Integer
from sqlalchemy import and_

class TestManyToOne( TestMetaData ):

    def test_simple(self):
        
        class A( self.Entity ):
            name = Field(String(60))

        class B( self.Entity ):
            name = Field(String(60))
            a = ManyToOne('A')

        self.create_all()

        with self.session.begin():
            b1 = B( name='b1', a = A( name = 'a1' ) )

        self.session.expunge_all()

        b = B.query.one()

        assert b.a.name == 'a1'

    def test_with_key_pk(self):
        
        class A( self.Entity ):
            test = Field(Integer, primary_key=True, key='testx')

        class B( self.Entity ):
            a = ManyToOne('A')

        self.create_all()

        with self.session.begin():
            b1 = B(a=A(testx=1))

        self.session.expunge_all()

        b = B.query.one()

        assert b.a.testx == 1

    def test_wh_key_in_m2o_col_kwargs(self):
        class A( self.Entity ):
            name = Field(String(128), default="foo")

        class B( self.Entity ):
            # specify a different key for the column so that
            #  it doesn't override the property when the column
            #  gets created.
            a = ManyToOne('A', colname='a',
                          column_kwargs=dict(key='a_id'))

        self.create_all()

        assert 'id' in A.table.primary_key.columns
        assert 'a_id' in B.table.columns

        with self.session.begin():
            a = A()
            self.session.flush()
            b = B(a=a)
            
        self.session.expunge_all()

        assert B.query.first().a == A.query.first()

    def test_specified_field(self):
        
        class Person( self.Entity ):
            name = Field(String(30))

        class Animal( self.Entity ):
            name = Field(String(30))
            owner_id = Field(Integer, colname='owner')
            owner = ManyToOne('Person', field=owner_id)

        self.create_all()

        assert 'owner' in Animal.table.c
        assert 'owner_id' not in Animal.table.c


        with self.session.begin():
            homer = Person(name="Homer")
            slh = Animal(name="Santa's Little Helper", owner=homer)

        self.session.expunge_all()

        homer = Person.get_by(name="Homer")
        animals = Animal.query.all()
        assert animals[0].owner is homer

    def test_one_pk(self):
        
        class A( self.Entity ):
            name = Field(String(40), primary_key=True)

        class B( self.Entity ):
            a = ManyToOne('A', primary_key=True)

        class C( self.Entity ):
            b = ManyToOne('B', primary_key=True)

        self.create_all()

        assert 'name' in A.table.primary_key.columns
        assert 'a_name' in B.table.primary_key.columns
        assert 'b_a_name' in C.table.primary_key.columns

    def test_m2o_is_only_pk(self):
        
        class A( self.Entity ):
            pass

        class B( self.Entity ):
            a = ManyToOne('A', primary_key=True)

        self.create_all()

        assert 'id' in A.table.primary_key.columns
        assert 'a_id' in B.table.primary_key.columns
        assert 'id' not in B.table.primary_key.columns

    def test_multi_pk_in_target(self):
        
        class A( self.Entity ):
            key1 = Field(Integer, primary_key=True)
            key2 = Field(String(40), primary_key=True)

        class B( self.Entity ):
            num = Field(Integer, primary_key=True)
            a = ManyToOne('A', primary_key=True)

        class C( self.Entity ):
            num = Field(Integer, primary_key=True)
            b = ManyToOne('B', primary_key=True)

        self.create_all()

        assert 'key1' in A.table.primary_key.columns
        assert 'key2' in A.table.primary_key.columns

        assert 'num' in B.table.primary_key.columns
        assert 'a_key1' in B.table.primary_key.columns
        assert 'a_key2' in B.table.primary_key.columns

        assert 'num' in C.table.primary_key.columns
        assert 'b_num' in C.table.primary_key.columns
        assert 'b_a_key1' in C.table.primary_key.columns
        assert 'b_a_key2' in C.table.primary_key.columns

    def test_cycle_but_use_alter(self):
        
        class A( self.Entity ):
            c = ManyToOne('C', use_alter=True)

        class B( self.Entity ):
            a = ManyToOne('A', primary_key=True)

        class C( self.Entity ):
            b = ManyToOne('B', primary_key=True)

        self.create_all()

        assert 'a_id' in B.table.primary_key.columns
        assert 'b_a_id' in C.table.primary_key.columns
        assert 'id' in A.table.primary_key.columns
        assert 'c_b_a_id' in A.table.columns

    def test_multi(self):
        
        class A( self.Entity ):
            name = Field(String(32))

        class B( self.Entity ):
            name = Field(String(15))

            a_rel1 = ManyToOne('A')
            a_rel2 = ManyToOne('A')

        self.create_all()

        with self.session.begin():
            a1 = A(name="a1")
            a2 = A(name="a2")
            b1 = B(name="b1", a_rel1=a1, a_rel2=a2)
            b2 = B(name="b2", a_rel1=a1, a_rel2=a1)

        self.session.expunge_all()

        a1 = A.get_by(name="a1")
        a2 = A.get_by(name="a2")
        b1 = B.get_by(name="b1")
        b2 = B.get_by(name="b2")

        assert a1 == b2.a_rel1
        assert a2 == b1.a_rel2

    def test_non_pk_target(self):
        class A( self.Entity ):
            name = Field(String(60), unique=True)

        class B( self.Entity ):
            name = Field(String(60))
            a = ManyToOne('A', target_column=['id', 'name'])
# currently fails
#            c = ManyToOne('C', target_column=['id', 'name'])

#        class C(Entity):
#            name = Field(String(60), unique=True)

        self.create_all()

        with self.session.begin():
            b1 = B(name='b1', a=A(name='a1'))

        self.session.expunge_all()

        b = B.query.one()

        assert b.a.name == 'a1'

    def test_belongs_to_syntax(self):
        
        class Person( self.Entity ):
            has_field('name', String(30))

        class Animal( self.Entity ):
            has_field('name', String(30))
            belongs_to('owner', of_kind='Person')

        self.create_all()

        with self.session.begin():
            santa = Person(name="Santa Claus")
            rudolph = Animal(name="Rudolph", owner=santa)

        self.session.expunge_all()

        assert "Claus" in Animal.get_by(name="Rudolph").owner.name
