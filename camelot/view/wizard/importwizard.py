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

"""Module for managing imports"""

import logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger('camelot.view.wizard.importwizard')

import csv
import codecs

from PyQt4.QtCore import Qt
from PyQt4 import QtCore, QtGui
from PyQt4.QtGui import QColor

from camelot.view.controls.editors.one2manyeditor import One2ManyEditor
from camelot.core.utils import ugettext as _
from camelot.view.art import Pixmap


class SelectFilePage(QtGui.QWizardPage):
    """SelectFilePage is the file selection page of the import wizard"""

    def __init__(self, parent=None):
        super(SelectFilePage, self).__init__(parent)
        self.setTitle(_('Import data from a file'))
        self.setSubTitle(_(
            "To import data, click 'Browse' to "
            "select a file then click 'Import'."
        ))

        icon = 'tango/32x32/mimetypes/x-office-spreadsheet.png'
        self.setPixmap(QtGui.QWizard.LogoPixmap, Pixmap(icon).getQPixmap())

        label = QtGui.QLabel(_('Select file:'))
        self.filelineedit = QtGui.QLineEdit()
        label.setBuddy(self.filelineedit)
        browsebutton = QtGui.QPushButton(_('Browse...'))

        # file path is a mandatory field
        self.registerField('datasource*', self.filelineedit)

        layout = QtGui.QVBoxLayout()
        layout.addWidget(label)
        hlayout = QtGui.QHBoxLayout()
        hlayout.addWidget(self.filelineedit)
        hlayout.addWidget(browsebutton)
        layout.addLayout(hlayout)
        self.setLayout(layout)

        self.connect(
            browsebutton,
            QtCore.SIGNAL('clicked()'),
            lambda: self.setpath()
        )

    def setpath(self):
        caption = _('Import Wizard - Set File Path')
        dir = self.field('datasource').toString()
        path = QtGui.QFileDialog.getOpenFileName(self, caption, dir)
        if path:
            self.filelineedit.setText(QtCore.QDir.toNativeSeparators(path))


class RowData(object):
    """Class representing the data in a single row of the imported file as an
    object with attributes column_1, column_2, ..., each representing the data
    in a single column of that row"""

    def __init__(self, row_number, row_data):
        """:param row_data: a list containing the data
        [column_1_data, column_2_data, ...] for a single row
        """
        self.id = row_number + 1
        for i, data in enumerate(row_data):
            self.__setattr__('column_%i' % i, data)


# see http://docs.python.org/library/csv.html
class UTF8Recoder:
    """Iterator that reads an encoded stream and reencodes the input to
    UTF-8."""

    def __init__(self, f, encoding):
        self.reader = codecs.getreader(encoding)(f)

    def __iter__(self):
        return self

    def next(self):
        return self.reader.next().encode('utf-8')


# see http://docs.python.org/library/csv.html
class UnicodeReader:
    """A CSV reader which will iterate over lines in the CSV file "f", which is
    encoded in the given encoding."""

    def __init__(self, f, dialect=csv.excel, encoding='utf-8', **kwds):
        f = UTF8Recoder(f, encoding)
        self.reader = csv.reader(f, dialect=dialect, **kwds)

    def next(self):
        row = self.reader.next()
        return [unicode(s, 'utf-8') for s in row]

    def __iter__(self):
        return self


class CsvCollectionGetter(object):
    """class that when called returns the data in filename as a list of RowData
    objects"""

    def __init__(self, filename):
        self.filename = filename
        self._data = None

    def __call__(self):
        if self._data==None:
            self._data = []
            import chardet
            
            enc = (
                chardet.detect(open(self.filename).read())['encoding']
                or 'utf-8'
            )
            items = UnicodeReader(open(self.filename), encoding=enc)

            self._data = [
                RowData(i, row_data)
                for i, row_data in enumerate(items)
            ]

        return self._data


class RowDataAdminDecorator(object):
    """Decorator that transforms the Admin of the class to be imported to an
    Admin of the RowData objects to be used when previewing and validating the
    data to be imported"""

    def __init__(self, object_admin):
        """:param object_admin: the object_admin object that will be
        decorated"""
        self._object_admin = object_admin

    def __getattr__(self, attr):
        return getattr(self._object_admin, attr)

    def get_columns(self):
        original_columns = self._object_admin.get_columns()

        def new_field_attributes(i, original_field_attributes, original_field):
            from camelot.view.controls import delegates
            attributes = dict(original_field_attributes)
            attributes['delegate'] = delegates.PlainTextDelegate
            attributes['python_type'] = str
            attributes['original_field'] = original_field

            if 'from_string' in attributes:

                def get_background_color(o):
                    """If the string is not convertible with from_string, or
                    the result is None when a value is required, set the
                    background to pink"""
                    value = getattr(o, 'column_%i'%i)
                    if not value and (attributes['nullable']==False):
                        return QColor('Pink')
                    try:
                        value = attributes['from_string'](value)
                        return None
                    except:
                        return QColor('Pink')

                attributes['background_color'] = get_background_color

            return attributes

        new_columns = [
            (
                'column_%i' %i,
                new_field_attributes(i, attributes, original_field)
            )
            for i, (original_field, attributes) in enumerate(original_columns)
        ]

        return new_columns


class DataPreviewPage(QtGui.QWizardPage):
    """DataPreviewPage is the previewing page for the import wizard"""

    def __init__(self, parent=None, model=None, collection_getter=None):
        super(DataPreviewPage, self).__init__(parent)
        assert model
        assert collection_getter
        self.setTitle(_('Data Preview'))
        self.setSubTitle(_('Please review the data below.'))
        self.model = model
        self.collection_getter = collection_getter

        icon = 'tango/32x32/mimetypes/x-office-spreadsheet.png'
        self.setPixmap(QtGui.QWizard.LogoPixmap, Pixmap(icon).getQPixmap())

        self.previewtable = One2ManyEditor(
            admin = model.get_admin(),
            parent=self,
            create_inline=True
        )

        ly = QtGui.QVBoxLayout()
        ly.addWidget(self.previewtable)
        self.setLayout(ly)

        self.setCommitPage(True)
        self.setButtonText(QtGui.QWizard.CommitButton, _('Import'))

    def initializePage(self):
        """Gets all info needed from SelectFilePage and feeds table"""
        filename = self.field('datasource').toString()
        self.model.set_collection_getter(self.collection_getter(filename))
        self.previewtable.set_value(self.model)
        self.emit(QtCore.SIGNAL('completeChanged()'))

    def isComplete(self):
        return True


class FinalPage(QtGui.QWizardPage):
    """FinalPage is the final page in the import process"""

    change_maximum_signal = QtCore.SIGNAL('change_maximum')
    change_value_signal = QtCore.SIGNAL('change_value')
    
    def __init__(self, parent=None, model=None):
        super(FinalPage, self).__init__(parent)
        self.setTitle(_('Import Progress'))
        self.model = model
        self.admin = model.get_admin()
        self.setSubTitle(_('Please wait while data is being imported.'))

        icon = 'tango/32x32/mimetypes/x-office-spreadsheet.png'
        self.setPixmap(QtGui.QWizard.LogoPixmap, Pixmap(icon).getQPixmap())
        self.setButtonText(QtGui.QWizard.FinishButton, _('Close'))
        self.progressbar = QtGui.QProgressBar()

        label = QtGui.QLabel(_(
            'The data will be ready when the progress reaches 100%.'
        ))
        label.setWordWrap(True)

        ly = QtGui.QVBoxLayout()
        ly.addWidget(label)
        ly.addWidget(self.progressbar)
        self.setLayout(ly)
        self.connect(self, self.change_maximum_signal, self.progressbar.setMaximum)
        self.connect(self, self.change_value_signal, self.progressbar.setValue)

    def run_import(self):
        collection = self.model.get_collection_getter()()
        self.emit(self.change_maximum_signal, len(collection))
        for i,row in enumerate(collection):
            new_entity_instance = self.admin.entity()
            for field_name, attributes in self.admin.get_columns():
                setattr(
                    new_entity_instance,
                    attributes['original_field'],
                    attributes['from_string'](getattr(row, field_name))
                )
            self.admin.add(new_entity_instance)
            self.admin.flush(new_entity_instance)
            self.emit(self.change_value_signal, i)

    def import_finished(self):
        self.progressbar.setMaximum(1)
        self.progressbar.setValue(1)
        self.emit(QtCore.SIGNAL('completeChanged()'))

    def isComplete(self):
        return self.progressbar.value() == self.progressbar.maximum()

    def initializePage(self):
        from camelot.view.model_thread import post
        self.progressbar.setMaximum(1)
        self.progressbar.setValue(0)
        self.emit(QtCore.SIGNAL('completeChanged()'))
        post(self.run_import, self.import_finished, self.import_finished)


class ImportWizard(QtGui.QWizard):
    """ImportWizard provides a two-step wizard for importing data as objects
    into Camelot.  To create a custom wizard, subclass this ImportWizard and
    overwrite its class attributes.

    To import a different file format, you probably need a custom
    collection_getter for this file type.
    """

    select_file_page = SelectFilePage
    data_preview_page = DataPreviewPage
    final_page = FinalPage
    collection_getter = CsvCollectionGetter
    window_title = _('Import CSV data')

    def __init__(self, parent=None, admin=None):
        """:param admin: camelot model admin"""
        from camelot.view.proxy.collection_proxy import CollectionProxy
        super(ImportWizard, self).__init__(parent)
        assert admin

        row_data_admin = RowDataAdminDecorator(admin)
        model = CollectionProxy(
            row_data_admin,
            lambda:[],
            row_data_admin.get_columns
        )

        self.addPage(SelectFilePage(parent=self))
        self.addPage(
            DataPreviewPage(
                parent=self,
                model=model,
                collection_getter=self.collection_getter
            )
        )
        self.addPage(FinalPage(parent=self, model=model))
        self.setWindowTitle(_(self.window_title))

        self.setOption(QtGui.QWizard.NoCancelButton)
