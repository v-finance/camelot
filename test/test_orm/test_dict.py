"""
    test the deep-set functionality
"""

from sqlalchemy.types import Integer, String

from camelot.core.orm import Field, ManyToOne, OneToMany, OneToOne

from . import TestMetaData

class TestDeepSet( TestMetaData ):
    
    def setUp( self ):
        super( TestDeepSet, self ).setUp()

        class Table1( self.Entity ):
            t1id = Field(Integer, primary_key=True)
            name = Field(String(30))
            tbl2s = OneToMany('Table2')
            tbl3 = OneToOne('Table3')
        
        class Table2( self.Entity ):
            t2id = Field(Integer, primary_key=True)
            name = Field(String(30))
            tbl1 = ManyToOne(Table1)
        
        class Table3( self.Entity ):
            t3id = Field(Integer, primary_key=True)
            name = Field(String(30))
            tbl1 = ManyToOne(Table1)  
    
        self.create_all()
        
        self.Table1 = Table1
        self.Table2 = Table2
        self.Table3 = Table3

    def test_set_attr(self):
        with self.session.begin():
            t1 = self.Table1()
            t1.from_dict(dict(name='test1'))
        assert t1.name == 'test1'

    def test_nonset_attr(self):
        with self.session.begin():
            t1 = self.Table1(name='test2')
            t1.from_dict({})
        assert t1.name == 'test2'

    def test_set_rel(self):
        with self.session.begin():
            t1 = self.Table1()
            t1.from_dict(dict(tbl3={'name': 'bob'}))
        assert t1.tbl3.name == 'bob'

    def test_remove_rel(self):
        with self.session.begin():
            t1 = self.Table1()
            t1.tbl3 = self.Table3()
            t1.from_dict(dict(tbl3=None))
        assert t1.tbl3 is None

    def test_update_rel(self):
        with self.session.begin():
            t1 = self.Table1()
            t1.tbl3 = self.Table3(name='fred')
            t1.from_dict(dict(tbl3={'name': 'bob'}))
        assert t1.tbl3.name == 'bob'

    def test_extend_list(self):
        with self.session.begin():
            t1 = self.Table1()
            t1.from_dict(dict(tbl2s=[{'name': 'test3'}]))
        assert len(t1.tbl2s) == 1
        assert t1.tbl2s[0].name == 'test3'

    def test_truncate_list(self):
        with self.session.begin():
            t1 = self.Table1()
            t2 = self.Table2()            
            t1.tbl2s.append(t2)
            t1.from_dict(dict(tbl2s=[]))
        assert len(t1.tbl2s) == 0

    def test_update_list_item(self):
        with self.session.begin():
            t1 = self.Table1()
            t2 = self.Table2()
            t1.tbl2s.append(t2)
            t1.from_dict(dict(tbl2s=[{'t2id': t2.t2id, 'name': 'test4'}]))
        assert len(t1.tbl2s) == 1
        assert t1.tbl2s[0].name == 'test4'

    def test_invalid_update(self):
        with self.session.begin():
            t1 = self.Table1()
            t2 = self.Table2()
            t1.tbl2s.append(t2)
            try:
                t1.from_dict(dict(tbl2s=[{'t2id': t2.t2id+1}]))
                assert False
            except:
                pass

    def test_to(self):
        with self.session.begin():
            t1 = self.Table1(t1id=50, name='test1')
        assert t1.to_dict() == {'t1id': 50, 'name': 'test1'}

    def test_to_deep_m2o(self):
        with self.session.begin():
            t1 = self.Table1(t1id=1, name='test1')
            t2 = self.Table2(t2id=1, name='test2', tbl1=t1)

        self.assertEqual( t2.to_dict(deep={'tbl1': {}}),
                          {'t2id': 1, 'name': 'test2', 'tbl1_t1id': 1,
                           'tbl1': {'name': 'test1'}} )

    def test_to_deep_m2o_none(self):
        with self.session.begin():
            t2 = self.Table2(t2id=1, name='test2')

        assert t2.to_dict(deep={'tbl1': {}}) == \
               {'t2id': 1, 'name': 'test2', 'tbl1_t1id': None, 'tbl1': None}

    def test_to_deep_o2m_empty(self):
        with self.session.begin():
            t1 = self.Table1(t1id=51, name='test2')
        assert t1.to_dict(deep={'tbl2s': {}}) == \
                {'t1id': 51, 'name': 'test2', 'tbl2s': []}

    def test_to_deep_o2m(self):
        with self.session.begin():
            t1 = self.Table1(t1id=52, name='test3')
            t2 = self.Table2(t2id=50, name='test4')
            t1.tbl2s.append(t2)
        assert t1.to_dict(deep={'tbl2s':{}}) == \
                {'t1id': 52,
                 'name': 'test3',
                 'tbl2s': [{'t2id': 50, 'name': 'test4'}]}

    def test_to_deep_o2o(self):
        with self.session.begin():
            t1 = self.Table1(t1id=53, name='test2')
            t1.tbl3 = self.Table3(t3id=50, name='wobble')
        assert t1.to_dict(deep={'tbl3': {}}) == \
                {'t1id': 53,
                 'name': 'test2',
                 'tbl3': {'t3id': 50, 'name': 'wobble'}}

    def test_to_deep_nested(self):
        with self.session.begin():
            t3 = self.Table3(t3id=1, name='test3')
            t1 = self.Table1(t1id=1, name='test1', tbl3=t3)
            t2 = self.Table2(t2id=1, name='test2', tbl1=t1)

        assert t2.to_dict(deep={'tbl1': {'tbl3': {}}}) == \
               {'t2id': 1,
                'name': 'test2',
                'tbl1_t1id': 1,
                'tbl1': {'name': 'test1',
                         'tbl3': {'t3id': 1,
                                  'name': 'test3'}}}

    def test_set_on_aliased_column(self):
        
        class A( self.Entity ):
            name = Field(String(60), colname='strName')

        self.create_all()

        with self.session.begin():
            a = A()
            a.set(name='Aye')

        self.session.expire_all()
        
        assert a.name == 'Aye'
