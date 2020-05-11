import unittest

from camelot.admin.application_admin import ApplicationAdmin
from camelot.core.qt import QtCore


class I18NTest(unittest.TestCase):

    def test_ugettext(self):
        from .snippet.i18n.specify_translation_string import message
        self.assertTrue(message)
      
    def test_ugettext_lazy(self):
        from .snippet.i18n.specify_lazy_translation_string import message
        self.assertTrue(message)
        
    def test_load_translators( self ):
        app_admin = ApplicationAdmin()
        QtCore.QLocale.setDefault(QtCore.QLocale('nl_BE'))
        self.assertEqual(len( app_admin.get_translator() ), 1)
        QtCore.QLocale.setDefault(QtCore.QLocale('pt_BR'))
        self.assertEqual(len( app_admin.get_translator() ), 2 )
