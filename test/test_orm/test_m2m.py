"""
test many to many relationships
"""

import logging

from . import TestMetaData

from camelot.core.orm import ( Field, ManyToMany, ManyToOne, using_options,
                               has_field, has_many, belongs_to, options,
                               has_and_belongs_to_many )

from sqlalchemy.types import String, Unicode, Integer
from sqlalchemy import orm, and_, schema

class TestManyToMany( TestMetaData ):

    def test_simple( self ):
        
        class A( self.Entity ):
            using_options( shortnames = True )
            name = Field(String(60))
            as_ = ManyToMany('A')
            bs_ = ManyToMany('B')

        class B( self.Entity ):
            using_options( shortnames = True )
            name = Field(String(60))
            as_ = ManyToMany('A')

        self.create_all()

        # check m2m table was generated correctly
        m2m_table = A.bs_.property.secondary
        assert m2m_table.name in self.metadata.tables

        # check column names
        m2m_cols = m2m_table.columns
        assert 'a_id' in m2m_cols
        assert 'b_id' in m2m_cols

        # check selfref m2m table column names were generated correctly
        m2m_cols = A.as_.property.secondary.columns
        assert 'as__id' in m2m_cols
        assert 'inverse_id' in m2m_cols

        # check the relationships work as expected
        with self.session.begin():
            b1 = B(name='b1', as_=[A(name='a1')])

        self.session.expire_all()

        a = A.query.one()
        b = B.query.one()

        assert a in b.as_
        assert b in a.bs_

    def test_table_kwargs(self):
        
        class A(self.Entity):
            bs_ = ManyToMany('B', table_kwargs={'info': {'test': True}})

        class B(self.Entity):
            as_ = ManyToMany('A')

        self.create_all()

        assert A.bs_.property.secondary.info['test'] is True

    def test_table_default_kwargs(self):
        options_defaults['table_options'] = {'info': {'test': True}}

        class A(self.Entity):
            bs_ = ManyToMany('B')

        class B(self.Entity):
            as_ = ManyToMany('A')

        self.create_all()

        options_defaults['table_options'] = {}

        assert A.bs_.property.secondary.info['test'] is True
        assert A.table.info['test'] is True
        assert B.table.info['test'] is True

    def test_custom_global_column_nameformat(self):
        # this needs to be done before declaring the classes
        options.M2MCOL_NAMEFORMAT = options.OLD_M2MCOL_NAMEFORMAT

        class A(self.Entity):
            bs_ = ManyToMany('B')

        class B(self.Entity):
            as_ = ManyToMany('A')

        self.create_all()

        # revert to original format
        options.M2MCOL_NAMEFORMAT = options.NEW_M2MCOL_NAMEFORMAT

        # check m2m table was generated correctly
        m2m_table = A.bs_.property.secondary
        assert m2m_table.name in self.metadata.tables

        # check column names
        m2m_cols = m2m_table.columns
        assert '%s_id' % A.table.name in m2m_cols
        assert '%s_id' % B.table.name in m2m_cols

    def test_alternate_column_formatter(self):
        # this needs to be done before declaring the classes
        options.M2MCOL_NAMEFORMAT = \
            options.ALTERNATE_M2MCOL_NAMEFORMAT

        class A(self.Entity):
            as_ = ManyToMany('A')
            bs_ = ManyToMany('B')

        class B(self.Entity):
            as_ = ManyToMany('A')

        self.create_all()

        # revert to original format
        options.M2MCOL_NAMEFORMAT = options.NEW_M2MCOL_NAMEFORMAT

        # check m2m table column names were generated correctly
        m2m_cols = A.bs_.property.secondary.columns
        assert 'as__id' in m2m_cols
        assert 'bs__id' in m2m_cols

        # check selfref m2m table column names were generated correctly
        m2m_cols = A.as_.property.secondary.columns
        assert 'as__id' in m2m_cols
        assert 'inverse_id' in m2m_cols

    def test_multi_pk_in_target(self):
        class A(self.Entity):
            key1 = Field(Integer, primary_key=True, autoincrement=False)
            key2 = Field(String(40), primary_key=True)

            bs_ = ManyToMany('B')

        class B(self.Entity):
            name = Field(String(60))
            as_ = ManyToMany('A')

        self.create_all()

        with self.session.begin():
            b1 = B(name='b1', as_=[A(key1=10, key2='a1')])

        self.session.expire_all()

        a = A.query.one()
        b = B.query.one()

        assert a in b.as_
        assert b in a.bs_

    def test_multi(self):
        class A(self.Entity):
            name = Field(String(100))

            rel1 = ManyToMany('B')
            rel2 = ManyToMany('B')

        class B(self.Entity):
            name = Field(String(20), primary_key=True)

        self.create_all()

        with self.session.begin():
            b1 = B(name='b1')
            a1 = A(name='a1', rel1=[B(name='b2'), b1],
                              rel2=[B(name='b3'), B(name='b4'), b1])

        self.session.expire_all()

        a1 = A.query.one()
        b1 = B.get_by(name='b1')
        b2 = B.get_by(name='b2')

        assert b1 in a1.rel1
        assert b1 in a1.rel2
        assert b2 in a1.rel1

    def test_selfref(self):
        class Person(self.Entity):
            using_options(shortnames=True)
            name = Field(String(30))

            friends = ManyToMany('Person')

        self.create_all()

        with self.session.begin():
            barney = Person(name="Barney")
            homer = Person(name="Homer", friends=[barney])
            barney.friends.append(homer)

        self.session.expire_all()

        homer = Person.get_by(name="Homer")
        barney = Person.get_by(name="Barney")

        assert homer in barney.friends
        assert barney in homer.friends

        m2m_cols = Person.friends.property.secondary.columns
        assert 'friends_id' in m2m_cols
        assert 'inverse_id' in m2m_cols

    def test_bidirectional_selfref(self):
        class Person(self.Entity):
            using_options(shortnames=True)
            name = Field(String(30))

            friends = ManyToMany('Person')
            is_friend_of = ManyToMany('Person')

        self.create_all()

        with self.session.begin():
            barney = Person(name="Barney")
            homer = Person(name="Homer", friends=[barney])
            barney.friends.append(homer)

        self.session.expire_all()

        homer = Person.get_by(name="Homer")
        barney = Person.get_by(name="Barney")

        assert homer in barney.friends
        assert barney in homer.friends

        m2m_cols = Person.friends.property.secondary.columns
        assert 'friends_id' in m2m_cols
        assert 'is_friend_of_id' in m2m_cols

    def test_has_and_belongs_to_many(self):
        class A(self.Entity):
            has_field('name', String(100))

            has_and_belongs_to_many('bs', of_kind='B')

        class B(self.Entity):
            has_field('name', String(100), primary_key=True)

        self.create_all()

        with self.session.begin():
            b1 = B(name='b1')
            a1 = A(name='a1', bs=[B(name='b2'), b1])
            a2 = A(name='a2', bs=[B(name='b3'), b1])
            a3 = A(name='a3')

        self.session.expire_all()

        a1 = A.get_by(name='a1')
        a2 = A.get_by(name='a2')
        a3 = A.get_by(name='a3')
        b1 = B.get_by(name='b1')
        b2 = B.get_by(name='b2')

        assert b1 in a1.bs
        assert b2 in a1.bs
        assert b1 in a2.bs
        assert not a3.bs

    def test_local_and_remote_colnames(self):
        class A(self.Entity):
            using_options(shortnames=True)
            key1 = Field(Integer, primary_key=True, autoincrement=False)
            key2 = Field(String(40), primary_key=True)

            bs_ = ManyToMany('B', local_colname=['foo', 'bar'],
                                  remote_colname="baz")

        class B(self.Entity):
            using_options(shortnames=True)
            name = Field(String(60))
            as_ = ManyToMany('A', remote_colname=['foo', 'bar'],
                                  local_colname="baz")

        self.create_all()

        with self.session.begin():
            b1 = B(name='b1', as_=[A(key1=10, key2='a1')])

        self.session.expire_all()

        a = A.query.one()
        b = B.query.one()

        assert a in b.as_
        assert b in a.bs_

    def test_manual_table_auto_joins(self):
        from sqlalchemy import Table, Column, ForeignKey, ForeignKeyConstraint

        a_b = schema.Table('a_b', self.metadata,
                           schema.Column('a_key1', None),
                           schema.Column('a_key2', None),
                           schema.Column('b_id', None, schema.ForeignKey('b.id')),
                           schema.ForeignKeyConstraint(['a_key1', 'a_key2'],
                                                       ['a.key1', 'a.key2']))

        class A(self.Entity):
            using_options(shortnames=True)
            key1 = Field(Integer, primary_key=True, autoincrement=False)
            key2 = Field(String(40), primary_key=True)

            bs_ = ManyToMany('B', table=a_b)

        class B(self.Entity):
            using_options(shortnames=True)
            name = Field(String(60))
            as_ = ManyToMany('A', table=a_b)

        self.create_all()

        with self.session.begin():
            b1 = B(name='b1', as_=[A(key1=10, key2='a1')])

        self.session.expire_all()

        a = A.query.one()
        b = B.query.one()

        assert a in b.as_
        assert b in a.bs_

    def test_manual_table_manual_joins(self):
        from sqlalchemy import Table, Column, and_

        a_b = schema.Table('a_b', self.metadata,
                           schema.Column('a_key1', Integer),
                           schema.Column('a_key2', String(40)),
                           schema.Column('b_id', String(60)))

        class A(self.Entity):
            using_options(shortnames=True)
            key1 = Field(Integer, primary_key=True, autoincrement=False)
            key2 = Field(String(40), primary_key=True)

            bs_ = ManyToMany('B', table=a_b,
                             primaryjoin=lambda: and_(A.key1 == a_b.c.a_key1,
                                                      A.key2 == a_b.c.a_key2),
                             secondaryjoin=lambda: B.id == a_b.c.b_id,
                             foreign_keys=[a_b.c.a_key1, a_b.c.a_key2,
                                 a_b.c.b_id])

        class B(self.Entity):
            using_options(shortnames=True)
            name = Field(String(60))

        self.create_all()

        with self.session.begin():
            a1 = A(key1=10, key2='a1', bs_=[B(name='b1')])

        self.session.expire_all()

        a = A.query.one()
        b = B.query.one()

        assert b in a.bs_
