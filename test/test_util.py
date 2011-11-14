import unittest
import datetime

class ViewUtilsCase(unittest.TestCase):
    """test the utility functions in camelot.view.utils
    """
    
    def setUp(self):
        from PyQt4 import QtCore
        from camelot.view import utils
        # clear the date and time format cache to prevent different
        # locales to be used
        utils._local_date_format = None
        utils._local_datetime_format = None
        utils._local_time_format = None
        QtCore.QLocale.setDefault( QtCore.QLocale('en_US') )
        
    def test_date_from_string(self):
        from camelot.view.utils import date_from_string
        result = datetime.date(2011,2,22)
        self.assertEqual( date_from_string('02222011'), result )
        self.assertEqual( date_from_string('02-22-2011'), result )
        self.assertEqual( date_from_string('2-22-2011'), result )
        self.assertEqual( date_from_string('2/22/2011'), result )
        result = datetime.date(2011,2,2)
        self.assertEqual( date_from_string('2/2/2011'), result )
        self.assertEqual( date_from_string('2-2-2011'), result )
        
    def test_datetime_from_string(self):
        from camelot.view.utils import datetime_from_string
        result = datetime.datetime(2011,2,22,22,11)
        self.assertEqual( datetime_from_string('02/22/2011 10:11 PM'), result )
        
    def test_time_from_string(self):
        from camelot.view.utils import time_from_string
        result = datetime.time(22,30)
        self.assertEqual( time_from_string('10:30 PM'), result )
