import unittest

class HelloWorldCase(unittest.TestCase):

    def test_hello_world(self):
        from .main import HelloWorld
        hello_world = HelloWorld()
        for step in hello_world.model_run(None):
            self.assertTrue(step)

if __name__=='__main__':
    unittest.main()