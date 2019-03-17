import unittest

from camelot.container.collection_container import CollectionContainer

class CollectionContainerCase(unittest.TestCase):
    
    def test_compare(self):
        original = [1, 2, 3]
        contained = CollectionContainer(original)
        self.assertTrue(original==original)
        self.assertTrue(contained==contained)
        self.assertTrue(contained==original)
        self.assertTrue(contained!=None)
        self.assertTrue(contained!=[4, 5, 6])
        self.assertFalse(contained!=original)