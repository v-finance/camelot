#  ============================================================================
#
#  Copyright (C) 2007-2008 Conceptive Engineering bvba. All rights reserved.
#  www.conceptive.be / project-camelot@conceptive.be
#
#  This file is part of the Camelot Library.
#
#  This file may be used under the terms of the GNU General Public
#  License version 2.0 as published by the Free Software Foundation
#  and appearing in the file LICENSE.GPL included in the packaging of
#  this file.  Please review the following information to ensure GNU
#  General Public Licensing requirements will be met:
#  http://www.trolltech.com/products/qt/opensource.html
#
#  If you are unsure which license is appropriate for your use, please
#  review the following information:
#  http://www.trolltech.com/products/qt/licensing.html or contact
#  project-camelot@conceptive.be.
#
#  This file is provided AS IS with NO WARRANTY OF ANY KIND, INCLUDING THE
#  WARRANTY OF DESIGN, MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE.
#
#  For use of this library in commercial applications, please contact
#  project-camelot@conceptive.be
#
#  ============================================================================

"""utilities for importwizard module"""

import csv
import codecs
import chardet
from PyQt4.QtCore import Qt
from PyQt4 import QtCore, QtGui
from PyQt4.QtCore import QModelIndex, QVariant, QStringList


# see http://docs.python.org/library/csv.html
class UTF8Recoder:
    """Iterator that reads an encoded stream
and reencodes the input to UTF-8."""

    def __init__(self, f, encoding):
        self.reader = codecs.getreader(encoding)(f)

    def __iter__(self):
        return self

    def next(self):
        return self.reader.next().encode('utf-8')


# see http://docs.python.org/library/csv.html
class UnicodeReader:
    """A CSV reader which will iterate over lines in the CSV file
"f", which is encoded in the given encoding."""

    def __init__(self, f, dialect=csv.excel, encoding='utf-8', **kwds):
        f = UTF8Recoder(f, encoding)
        self.reader = csv.reader(f, dialect=dialect, **kwds)

    def next(self):
        row = self.reader.next()
        return [unicode(s, 'utf-8') for s in row]

    def __iter__(self):
        return self


def import_csv_data(source):
    """Uses chardet to try to detect the encoding of a source"""
    detected = chardet.detect(open(source).read())['encoding']
    enc = detected or 'utf-8'
    try: result = UnicodeReader(open(source), encoding=enc)
    except: return list()
    return list(result)


def columns_iter(model, row):
    """iterates over the columns of a Qt model's row"""
    for col in range(model.columnCount()):
        idx = model.index(row, col, QModelIndex())
        qvar = model.data(idx)
        yield (col+1, qvar.toString())


def labeled_columns_iter(model, row, labels):
    """labeled version of column_iter"""
    assert len(labels) == model.columnCount()
    for label, col in zip(labels, range(model.columnCount())):
        idx = model.index(row, col, QModelIndex())
        qvar = model.data(idx)
        yield (label, qvar.toString())


def rows_iter(model, startrow=0):
    """iterates over the rows of a Qt model"""
    for row in range(startrow, model.rowCount()):
        cols = ((col, val) for col, val in columns_iter(model, row))
        yield dict(cols)


def labeled_rows_iter(model, labels, startrow=0):
    """labeled version of rows_iter"""
    for row in range(startrow, model.rowCount()):
        cols = ((label, val) \
                for label, val in \
                    labeled_columns_iter(model, row, labels))
        yield dict(cols)
