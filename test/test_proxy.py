import datetime
import logging
import unittest

from camelot.admin.action.field_action import ClearObject, SelectObject
from camelot.admin.object_admin import ObjectAdmin
from camelot.core.item_model import (
    AbstractModelFilter, ListModelProxy, QueryModelProxy
)
from camelot.model.party import Party, Person
from camelot.view.controls import delegates

LOGGER = logging.getLogger(__name__)

from .test_model import ExampleModelMixinCase, LoadSampleData

class B(object):

    def __init__(self, value):
        self.value = value

    def __str__(self):
        return '{}'.format(self.value)

    class Admin(ObjectAdmin):
        list_display = ['value']


class C(B):
    pass

class A(object):

    def __init__(self, x):
        self.w = B(x)
        self.x = x
        self.y = 0
        self.z = [C(0), C(0)]
        self.created = datetime.datetime.now()

    class Admin(ObjectAdmin):
        list_display = ['x', 'y', 'z', 'created', 'w']
        field_attributes = {
            'w': {'editable': True,
                  'delegate': delegates.Many2OneDelegate,
                  'target': B,
                  'actions':[SelectObject(), ClearObject()],
                  },
            'x': {'editable': True,
                  'static':'static',
                  'prefix':lambda o:'pre',
                  'tooltip': 'Hint',
                  'background_color': 'red',
                  'delegate': delegates.IntegerDelegate,
                  },
            'y': {'editable': lambda o: o.x < 10,
                  'delegate': delegates.IntegerDelegate,
                  'nullable': False,
                  },
            'z': {'editable': True,
                  'delegate': delegates.One2ManyDelegate,
                  'target': C,
                  },
            'created': {
                'delegate': delegates.DateTimeDelegate
            }
        }

        def get_verbose_identifier(self, obj):
            return 'A : {0}'.format(obj.x)

        def get_completions(self, obj, field_name, prefix):
            if field_name == 'w':
                return [
                    B('{0}_{1.x}_1'.format(prefix, obj)),
                    B('{0}_{1.x}_2'.format(prefix, obj)),
                    B('{0}_{1.x}_3'.format(prefix, obj)),
                    ]


class ListModelProxyCase(unittest.TestCase):

    def setUp(self):
        super(ListModelProxyCase, self).setUp()
        self.list_model = [A(1), A(2), A(3), A(0)]
        self.proxy = ListModelProxy(self.list_model)
        self.attribute_name = 'x'

        class XLessThanFilter(AbstractModelFilter):
        
            def filter(self, it, value):
                for obj in it:
                    if obj.x < value:
                        yield obj
        
        self.list_model_filter = XLessThanFilter()

    def create_object(self):
        return A(7)
    
    def delete_object(self, obj):
        pass

    def append_object_to_collection(self, obj):
        self.list_model.append(obj)

    def test_index_new_object(self):
        initial_length = len(self.proxy)
        self.assertTrue(initial_length)
        # a new object is created, and the proxy is unaware
        obj = self.create_object()
        self.assertEqual(len(self.proxy), initial_length)
        # append the new object to the collection without going
        # through the proxy
        self.append_object_to_collection(obj)
        # the proxy is still unaware
        self.assertEqual(len(self.proxy), initial_length)
        # try to find the new object through the proxy
        try:
            i = self.proxy.index(obj)
        except ValueError:
            # if the proxy is a queryproxy, the object will not be found
            i = None
        # if the object was found, so the length of the proxy has changed
        if i is not None:
            self.assertEqual(len(self.proxy), initial_length+1)

    def test_length(self):
        self.assertTrue(len(self.proxy))

    def test_slice(self):
        rows = len(self.proxy)
        self.assertTrue(list(self.proxy[0:1]))
        self.assertTrue(list(self.proxy[rows - 1:rows]))

    def test_append(self):
        # append a new object twice
        size = len(self.proxy)
        obj = self.create_object()
        self.proxy.append(obj)
        self.proxy.append(obj)
        self.assertEqual(len(self.proxy), size+1)
        # append an existing object
        first_obj = list(self.proxy[0:1])[0]
        self.proxy.append(first_obj)
        self.assertEqual(len(self.proxy), size+1)

    def test_remove(self):
        # remove an existing object
        size = len(self.proxy)
        first_obj, second_obj, third_obj = list(self.proxy[0:3])
        self.proxy.remove(second_obj)
        self.delete_object(second_obj)
        self.assertEqual(len(self.proxy), size-1)
        new_first_obj, new_second_obj = list(self.proxy[0:2])
        self.assertEqual(first_obj, new_first_obj)
        self.assertEqual(third_obj, new_second_obj)
        # remove a new twice
        obj = self.create_object()
        self.proxy.append(obj)
        self.proxy.remove(obj)
        self.assertEqual(len(self.proxy), size-1)

    def test_remove_outside_proxy(self):
        # Test proxy handling the reindexing of objects that are removed from the list model outside the proxy interface.
        size = len(self.proxy)
        first_obj, second_obj, third_obj, fourth_obj = self.list_model
        
        # Remove an object from the list model directly and verify it is removed from the proxy's _objects, but still present in the _indexed_objects.
        self.list_model.remove(second_obj)
        self.assertEqual(len(self.proxy), size)
        self.assertEqual(len(self.proxy._objects), size-1)
        self.assertNotIn(second_obj, self.proxy._objects)
        self.assertIn(second_obj, self.proxy._indexed_objects)
        
        # Then create a new object and append it to the proxy, which has the result of the new object having an _objects' index
        # that is still present in the proxy's _indexed_objects, refering to the old removed object.
        # In the extending of its indexed objects, the proxy should detect those cases, and assign the new object a new index at the end:        
        new_obj = self.create_object()
        self.proxy.append(new_obj)
        self.assertEqual(len(self.proxy), size+1)
        self.assertEqual(len(self.proxy._objects), size)
        self.assertNotIn(second_obj, self.proxy._objects)
        self.assertIn(second_obj, self.proxy._indexed_objects)
        self.assertIn(new_obj, self.proxy._objects)
        self.assertIn(new_obj, self.proxy._indexed_objects)
        self.assertEqual(self.proxy.index(new_obj), size)
        
        # Remove another object from the list model
        self.list_model.remove(fourth_obj)
        self.assertEqual(len(self.proxy), size+1)
        self.assertEqual(len(self.proxy._objects), size-1)
        self.assertNotIn(fourth_obj, self.proxy._objects)
        self.assertIn(fourth_obj, self.proxy._indexed_objects)
        
        # Then create a new object and append it to list model directly, outside the proxy.
        new_obj_2 = self.create_object()
        self.list_model.append(new_obj_2)
        self.assertEqual(len(self.proxy), size+1)
        self.assertEqual(len(self.proxy._objects), size)
        self.assertNotIn(fourth_obj, self.proxy._objects)
        self.assertIn(fourth_obj, self.proxy._indexed_objects)
        self.assertIn(new_obj_2, self.proxy._objects)
        self.assertNotIn(new_obj_2, self.proxy._indexed_objects)

        # This time the proxy should detect the removed object's index still being present in the _indexed_objects when we index the new object
        # on the proxy and again gets assigned a new index at the end:        
        i = self.proxy.index(new_obj_2)
        self.assertEqual(len(self.proxy), size+2)
        self.assertEqual(len(self.proxy._objects), size)
        self.assertNotIn(fourth_obj, self.proxy._objects)
        self.assertIn(fourth_obj, self.proxy._indexed_objects)
        self.assertIn(new_obj_2, self.proxy._objects)
        self.assertIn(new_obj_2, self.proxy._indexed_objects)
        self.assertEqual(i, size+1)
        
    def test_copy_after_sort(self):
        self.proxy.sort(self.attribute_name)
        length = len(self.proxy)
        new_proxy = self.proxy.copy()
        self.assertEqual(len(new_proxy), length)
        for o1, o2 in zip(self.proxy[0:length], new_proxy[0:length]):
            self.assertEqual(o1, o2)

    def test_copy_before_index(self):
        # take a copy before the indexing has been done, to make
        # sure the internal state is initialized correct
        new_proxy = self.proxy.copy()
        self.assertEqual(len(new_proxy), len(self.proxy))

    def test_filter(self):
        self.assertEqual(len(self.proxy), 4)
        self.proxy.filter(self.list_model_filter, 3)
        self.assertEqual(len(self.proxy), 3)


class QueryModelProxyCase(ListModelProxyCase, ExampleModelMixinCase):

    @classmethod
    def setUpClass(cls):
        super(QueryModelProxyCase, cls).setUpClass()
        cls.setup_sample_model()
        list(LoadSampleData().model_run(None, None))

    @classmethod
    def tearDownClass(cls):
        super(QueryModelProxyCase, cls).tearDownClass()
        cls.tear_down_sample_model()

    def setUp(self):
        super(QueryModelProxyCase, self).setUp()
        self.session.expunge_all()
        self.query = self.session.query(Person)
        self.proxy = QueryModelProxy(self.query)
        self.attribute_name = 'first_name'

    def create_object(self):
        return Person()

    def delete_object(self, obj):
        self.session.delete(obj)
        self.session.flush()

    def test_index_expunged_object(self):
        # a new object is created, and the proxy is aware
        obj = self.create_object()
        self.proxy.append(obj)
        initial_length = len(self.proxy)
        self.assertTrue(initial_length)
        # the new object is expunged, and the proxy is unaware
        self.session.expunge(obj)
        self.assertEqual(len(self.proxy), initial_length)
        # try to find the new object through the proxy
        i = self.proxy.index(obj)
        self.assertTrue(i)
        # inform the proxy about the object being removed
        self.proxy.remove(obj)
        self.assertEqual(len(self.proxy), initial_length-1)

    def test_append_and_flush(self):
        size = len(self.proxy)
        obj = self.create_object()
        self.proxy.append(obj)
        self.assertEqual(len(self.proxy), size+1)
        obj.first_name = 'Foo'
        obj.last_name = 'Fighter'
        self.session.flush()
        self.assertEqual(len(self.proxy), size+1)
        list(self.proxy[0:size+1])[0]

    def test_unique_primary_key(self):
        # A query returns multiple objects with the same primary key
        query = self.session.query(Party)
        proxy = QueryModelProxy(query)
        union_all_query = query.union_all(self.session.query(Party)).order_by(Party.id)
        self.assertEqual(union_all_query.count(), query.count()*2)
        # Validate the second and the first element of the union query
        # refer to the same object
        first_query_element = union_all_query.offset(0).first()
        second_query_element = union_all_query.offset(1).first()
        self.assertEqual(first_query_element, second_query_element)
        # However, the proxy will only report unique primary keys
        union_all_proxy = QueryModelProxy(union_all_query)
        self.assertEqual(len(union_all_proxy), len(proxy))
        first_proxy_element = list(union_all_proxy[0:1])[0]
        second_proxy_element = list(union_all_proxy[1:2])[0]
        self.assertNotEqual(first_proxy_element, second_proxy_element)
        ## And the objects will be at the same index as if there were
        ## no duplicates
        #objects = list(self.proxy[0:len(self.proxy)])
        #union_all_objects = list(union_all_proxy[0:len(union_all_proxy)])
        #for i in range(len(self.proxy)):
            #self.assertEqual(union_all_objects[i], objects[i])

    def test_filter(self):
        pass
    
    def test_remove_outside_proxy(self):
        pass
