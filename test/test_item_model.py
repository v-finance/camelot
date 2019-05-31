import unittest

from camelot.view.item_model.cache import ValueCache

class ValueCacheCase(unittest.TestCase):

    def test_changed_columns(self):
        cache = ValueCache(10)
        self.assertEqual(len(cache), 0)
        
        a = object()
        changed = cache.add_data(4, a, {1: 1, 2: 2, 3: 3})
        self.assertEqual(len(cache), 1)
        self.assertEqual(len(changed), 3)
        self.assertEqual(changed, {1, 2, 3})
        data = cache.get_data(4)
        self.assertEqual(len(data), 3)

        b = object()
        changed = cache.add_data(5, b, {1: 1, 2: 2, 3: 3, 4:4})
        self.assertEqual(len(cache), 2)
        self.assertEqual(len(changed), 4)
        data = cache.get_data(5)
        self.assertEqual(len(data), 4)

        changed = cache.add_data(4, a,  {1: 1, 2: 3, 3: 4})
        self.assertEqual(len(cache), 2)
        self.assertEqual(len(changed), 2)
        self.assertEqual(changed, {2, 3})
        data = cache.get_data(4)
        self.assertEqual(len(data), 3)

        changed = cache.add_data(4, a,  {4: 4,})
        self.assertEqual(len(cache), 2)
        self.assertEqual(len(changed), 1)
        self.assertEqual(changed, {4,})
        data = cache.get_data(4)
        self.assertEqual(len(data), 4)

    def test_limited_length(self):
        cache = ValueCache(10)
        self.assertEqual(len(cache), 0)
        for i in range(10):
            o = object()
            cache.add_data(i, o, {1: 1, 2: 2, 3: 3})
        self.assertEqual(len(cache), 10)
        cache.add_data(12, object(), {1: 1, 2: 3, 3: 4})
        self.assertEqual(len(cache), 10)
