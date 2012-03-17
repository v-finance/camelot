#  ============================================================================
#
#  Copyright (C) 2007-2012 Conceptive Engineering bvba. All rights reserved.
#  www.conceptive.be / project-camelot@conceptive.be
#
#  This file is part of the Camelot Library.
#
#  This file may be used under the terms of the GNU General Public
#  License version 2.0 as published by the Free Software Foundation
#  and appearing in the file license.txt included in the packaging of
#  this file.  Please review this information to ensure GNU
#  General Public Licensing requirements will be met.
#
#  If you are unsure which license is appropriate for your use, please
#  visit www.python-camelot.com or contact project-camelot@conceptive.be
#
#  This file is provided AS IS with NO WARRANTY OF ANY KIND, INCLUDING THE
#  WARRANTY OF DESIGN, MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE.
#
#  For use of this library in commercial applications, please contact
#  project-camelot@conceptive.be
#
#  ============================================================================

"""test module for the 'camelot/view/field_attributes.py' module"""

import unittest
from datetime import datetime
from camelot.core import constants
from camelot.view.utils import (ParsingError,
                                bool_from_string,
                                date_from_string,
                                time_from_string,
                                datetime_from_string,
                                int_from_string,
                                float_from_string)


class FromStringTestCase(unittest.TestCase):

    def test_bool_from_string(self):
        self.assertRaises(ParsingError, bool_from_string, None)
        self.assertRaises(ParsingError, bool_from_string, 'soup')
        self.assertEqual(False, bool_from_string('false'))
        self.assertEqual(False, bool_from_string('False'))
        self.assertEqual(True, bool_from_string('true'))
        self.assertEqual(True, bool_from_string('True'))

    def test_date_from_string(self):
        self.assertRaises(ParsingError, date_from_string, None)
        
        fmt = constants.strftime_date_format
        d_1 = datetime.strptime('19-11-2009', fmt).date()
        d_2 = date_from_string('19-11-2009', fmt)
        
        self.assertEqual(d_1, d_2)
        self.assertRaises(ParsingError, date_from_string, '2009', fmt)
        self.assertRaises(ParsingError, date_from_string, '11-19-2009', fmt)
        self.assertRaises(ParsingError, date_from_string, '11-19-09', fmt)
        self.assertRaises(ParsingError, date_from_string, '11/09/2009', fmt)

    def test_time_from_string(self):
        self.assertRaises(ParsingError, time_from_string, None)

        fmt = constants.strftime_time_format
        t_1 = datetime.strptime('11:48', fmt).time()
        t_2 = time_from_string('11:48', fmt)

        self.assertEqual(t_1, t_2)
        self.assertRaises(ParsingError, time_from_string, 'am', fmt)
        self.assertRaises(ParsingError, time_from_string, '11:48 am', fmt)
        self.assertRaises(ParsingError, date_from_string, '11:48 AM', fmt)
    
    def test_datetime_from_string(self):
        self.assertRaises(ParsingError, datetime_from_string, None)

        fmt = constants.strftime_datetime_format
        dt_1 = datetime.strptime('19-11-2009 11:48', fmt)
        dt_2 = datetime_from_string('19-11-2009 11:48', fmt)

        self.assertEqual(dt_1, dt_2)
        self.assertRaises(ParsingError,
                          datetime_from_string,
                          '19-11-2009, 11:48',
                          fmt)
        self.assertRaises(ParsingError,
                          datetime_from_string,
                          '11:48',
                          fmt)
        self.assertRaises(ParsingError,
                          datetime_from_string,
                          '19-11-2009',
                          fmt)

    def test_int_from_string(self):
        self.assertRaises(ParsingError, int_from_string, None)
        self.assertRaises(ParsingError, int_from_string, 'sausage')
        self.assertEqual(102, int_from_string('102'))
        self.assertEqual(0, int_from_string(''))
        self.assertRaises(ParsingError, int_from_string, '105.4')

    def test_float_from_string(self):
        self.assertRaises(ParsingError, float_from_string, None)
        self.assertRaises(ParsingError, float_from_string, 'casserole')
        self.assertEqual(0.0, float_from_string(''))
        self.assertEqual(0.1, float_from_string('0.1'))
        self.assertEqual(5105.5, float_from_string('5105.5'))


if __name__ == '__main__':
    unittest.main()



