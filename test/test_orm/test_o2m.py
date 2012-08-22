"""
test one to many relationships
"""

import logging

from . import TestMetaData

from camelot.core.orm import Field, OneToMany, ManyToOne, using_options

from sqlalchemy.types import String, Unicode
from sqlalchemy import and_

class TestOneToMany( TestMetaData ):
    
    def test_simple( self ):

        class A( self.Entity ):
            name = Field(String(60))
            bs = OneToMany('B')

        class B( self.Entity ):
            name = Field(String(60))
            a = ManyToOne('A')

        self.create_all()
        
        with self.session.begin():
            a1 = A(name='a1')
            b1 = B(name='b1', a=a1)

            # does it work before a commit? (does the backref work?)
            assert b1 in a1.bs

        self.session.expunge_all()

        b = B.query.one()
        a = b.a

        assert b in a.bs

    def test_selfref(self):
        
        class Person( self.Entity ):
            name = Field(String(30))

            father = ManyToOne('Person', inverse='children')
            children = OneToMany('Person', inverse='father')

        self.create_all()

        with self.session.begin():
            grampa = Person(name="Abe")
            homer = Person(name="Homer")
            bart = Person(name="Bart")
            lisa = Person(name="Lisa")
    
            grampa.children.append(homer)
            homer.children.append(bart)
            lisa.father = homer

        self.session.expunge_all()

        p = Person.get_by(name="Homer")

        assert p in p.father.children
        assert p.father is Person.get_by(name="Abe")
        assert p is Person.get_by(name="Lisa").father

    def test_multiple_selfref(self):
        # define a self-referential table with several relations

        class TreeNode( self.Entity ):
            using_options(order_by='name')
            name = Field(String(50), required=True)

            parent = ManyToOne('TreeNode')
            children = OneToMany('TreeNode', inverse='parent')
            root = ManyToOne('TreeNode')

        self.create_all()

        root = TreeNode(name='rootnode')
        root.children.append(TreeNode(name='node1', root=root))
        node2 = TreeNode(name='node2', root=root)
        node2.children.append(TreeNode(name='subnode1', root=root))
        node2.children.append(TreeNode(name='subnode2', root=root))
        root.children.append(node2)
        root.children.append(TreeNode(name='node3', root=root))

        session.commit()
        session.clear()

        root = TreeNode.get_by(name='rootnode')
        sub2 = TreeNode.get_by(name='subnode2')
        assert sub2 in root.children[1].children
        assert sub2.root == root

    def test_viewonly(self):
        
        class User( self.Entity ):
            name = Field(String(50))
            boston_addresses = OneToMany('Address', primaryjoin=lambda:
                and_(Address.user_id == User.id, Address.city == u'Boston'),
                viewonly=True
            )
            addresses = OneToMany('Address')

        class Address( self.Entity ):
            user = ManyToOne('User')
            street = Field(Unicode(255))
            city = Field(Unicode(255))

        self.create_all()

        with self.session.begin():
            user = User(name="u1",
                        addresses=[Address(street=u"Queen Astrid Avenue, 32",
                                           city=u"Brussels"),
                                   Address(street=u"Cambridge Street, 5",
                                           city=u"Boston")])

        self.session.expunge_all()

        user = User.get(1)
        assert len(user.addresses) == 2
        assert len(user.boston_addresses) == 1
        assert "Cambridge" in user.boston_addresses[0].street

    def test_filter_func(self):
        
        class User( self.Entity ):
            name = Field(String(50))
            boston_addresses = OneToMany('Address', filter=lambda c:
                                         c.city == u'Boston')
            addresses = OneToMany('Address')

        class Address( self.Entity ):
            user = ManyToOne('User')
            street = Field(Unicode(255))
            city = Field(Unicode(255))

        self.create_all()

        user = User(name="u1",
                    addresses=[Address(street=u"Queen Astrid Avenue, 32",
                                       city=u"Brussels"),
                               Address(street=u"Cambridge Street, 5",
                                       city=u"Boston")])

        session.commit()
        session.clear()

        user = User.get(1)
        assert len(user.addresses) == 2
        assert len(user.boston_addresses) == 1
        assert "Cambridge" in user.boston_addresses[0].street

    def test_inverse_has_non_pk_target(self):
        
        class A( self.Entity ):
            name = Field(String(60), unique=True)
            bs = OneToMany('B')

        class B( self.Entity ):
            name = Field(String(60))
            a = ManyToOne('A', target_column='name')

        self.create_all()

        a1 = A(name='a1')
        b1 = B(name='b1', a=a1)

        # does it work before a commit? (does the backref work?)
        assert b1 in a1.bs

        session.commit()
        session.clear()

        b = B.query.one()
        a = b.a

        assert b.a.name == 'a1'
        assert b in a.bs

    def test_has_many_syntax(self):
        
        class Person( self.Entity ):
            has_field('name', String(30))
            has_many('pets', of_kind='Animal')

        class Animal( self.Entity ):
            has_field('name', String(30))
            belongs_to('owner', of_kind='Person')

        self.create_all()

        santa = Person(name="Santa Claus")
        rudolph = Animal(name="Rudolph", owner=santa)

        session.commit()
        session.clear()

        santa = Person.get_by(name="Santa Claus")

        assert Animal.get_by(name="Rudolph") in santa.pets
