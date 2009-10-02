from camelot.test import ModelThreadTestCase

class I18NTest(ModelThreadTestCase):
  
  def testUGetText(self):
    from snippet.i18n.specify_translation_string import message
    self.assertTrue(message)
