import unittest


class I18NTest(unittest.TestCase):

    def test_ugettext(self):
        from .snippet.i18n.specify_translation_string import message
        self.assertTrue(message)
      
    def test_ugettext_lazy(self):
        from .snippet.i18n.specify_lazy_translation_string import message
        self.assertTrue(message)
        
