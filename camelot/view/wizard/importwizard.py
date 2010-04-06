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

import csv
import codecs

from PyQt4 import QtGui
from PyQt4 import QtCore
from PyQt4.QtCore import Qt
from PyQt4.QtGui import QColor

from camelot.core.utils import ugettext as _

from camelot.view.art import Pixmap
from camelot.view.model_thread import post
from camelot.view.wizard.pages.select import SelectFilePage
from camelot.view.controls.editors.one2manyeditor import One2ManyEditor

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger('camelot.view.wizard.importwizard')


class RowData(object):
    """Class representing the data in a single row of the imported file as an
    object with attributes column_1, column_2, ..., each representing the data
    in a single column of that row.
    
    since the imported file might contain less columns than expected, the RowData
    object returns None for not existing attributes
    """

    def __init__(self, row_number, row_data):
        """:param row_data: a list containing the data
        [column_1_data, column_2_data, ...] for a single row
        """
        self.id = row_number + 1
        for i, data in enumerate(row_data):
            self.__setattr__('column_%i' % i, data)

    def __getattr__(self, attr_name):
        return None

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
    data to be imported.
    
    based on the field attributes of the original mode, it will turn the background color pink
    if the data is invalid for being imported.
    """
    
    invalid_color = QColor('Pink')

    def __init__(self, object_admin):
        """:param object_admin: the object_admin object that will be
        decorated"""
        self._object_admin = object_admin
        self._columns = None

    def __getattr__(self, attr):
        return getattr(self._object_admin, attr)

    def create_validator(self, model):
        """Creates a validator that validates the data to be imported, the validator will
        check if the background of the cell is pink, and if it is it will mark that object
        as invalid.
        """
        from camelot.admin.validator.object_validator import ObjectValidator
        
        class NewObjectValidator(ObjectValidator):
            
            def objectValidity(self, entity_instance):
                for _field_name, attributes in self.admin.get_columns():
                    background_color_getter = attributes.get('background_color', None)
                    if background_color_getter:
                        background_color = background_color_getter(entity_instance)
                        if background_color==self.admin.invalid_color:
                            return ['invalid field']
                return []
            
        return NewObjectValidator(self, model)
    
    def get_fields(self):
        return self.get_columns()
    
    def flush(self, obj):
        pass
    
    def get_columns(self):
        if self._columns:
            return self._columns
        
        original_columns = self._object_admin.get_columns()

        def new_field_attributes(i, original_field_attributes, original_field):
            from camelot.view.controls import delegates
            attributes = dict(original_field_attributes)
            attributes['delegate'] = delegates.PlainTextDelegate
            attributes['python_type'] = str
            attributes['original_field'] = original_field
            
            # remove some attributes that might disturb the import wizard
            for attribute in ['background_color', 'tooltip']:
                attributes[attribute] = None

            if 'from_string' in attributes:

                def get_background_color(o):
                    """If the string is not convertible with from_string, or
                    the result is None when a value is required, set the
                    background to pink"""
                    value = getattr(o, 'column_%i'%i)
                    if not value and (attributes['nullable']==False):
                        return self.invalid_color
                    try:
                        value = attributes['from_string'](value)
                        return None
                    except:
                        return self.invalid_color

                attributes['background_color'] = get_background_color

            return attributes

        new_columns = [
            (
                'column_%i' %i,
                new_field_attributes(i, attributes, original_field)
            )
            for i, (original_field, attributes) in enumerate(original_columns)
            if attributes['editable']
        ]

        self._columns = new_columns
        
        return new_columns


class DataPreviewPage(QtGui.QWizardPage):
    """DataPreviewPage is the previewing page for the import wizard"""

    def __init__(self, parent=None, model=None, collection_getter=None):
        from camelot.view.controls.editors import NoteEditor
        super(DataPreviewPage, self).__init__(parent)
        assert model
        assert collection_getter
        self.setTitle(_('Data Preview'))
        self.setSubTitle(_('Please review the data below.'))
        self._complete = False
        self.model = model
        validator = self.model.get_validator()
        self.connect( validator, validator.validity_changed_signal, self.update_complete)
        self.connect( model, QtCore.SIGNAL('layoutChanged()'), self.validate_all_rows )
        post(validator.validate_all_rows)
        self.collection_getter = collection_getter

        icon = 'tango/32x32/mimetypes/x-office-spreadsheet.png'
        self.setPixmap(QtGui.QWizard.LogoPixmap, Pixmap(icon).getQPixmap())

        self.previewtable = One2ManyEditor(
            admin = model.get_admin(),
            parent=self,
            create_inline=True
        )
        self._note = NoteEditor()
        self._note.set_value(None)
        
        ly = QtGui.QVBoxLayout()
        ly.addWidget(self.previewtable)
        ly.addWidget(self._note)
        self.setLayout(ly)

        self.setCommitPage(True)
        self.setButtonText(QtGui.QWizard.CommitButton, _('Import'))
        self.update_complete()
        
    def validate_all_rows(self):
        validator = self.model.get_validator()
        post(validator.validate_all_rows, self.update_complete)
        
    def update_complete(self, *args):
        self._complete = (self.model.get_validator().number_of_invalid_rows()==0)
        self.emit(QtCore.SIGNAL('completeChanged()'))
        if self._complete:
            self._note.set_value(None)
        else:
            self._note.set_value(_('Please correct the data above before proceeding with the import.<br/>Incorrect cells have a pink background.'))
        
    def initializePage(self):
        """Gets all info needed from SelectFilePage and feeds table"""
        filename = self.field('datasource').toString()
        self._complete = False
        self.emit(QtCore.SIGNAL('completeChanged()'))
        self.model.set_collection_getter(self.collection_getter(filename))
        self.previewtable.set_value(self.model)
        self.validate_all_rows()
        
    def validatePage(self):
        answer = QtGui.QMessageBox.question(self, 
                                           _('Proceed with import'), 
                                           _('Importing data cannot be undone,\nare you sure you want to continue'),
                                           QtGui.QMessageBox.Cancel,
                                           QtGui.QMessageBox.Ok,
                                           )
        if answer==QtGui.QMessageBox.Ok:
            return True
        return False

    def isComplete(self):
        return self._complete


class FinalPage(QtGui.QWizardPage):
    """FinalPage is the final page in the import process"""

    change_maximum_signal = QtCore.SIGNAL('change_maximum')
    change_value_signal = QtCore.SIGNAL('change_value')
    
    def __init__(self, parent=None, model=None, admin=None):
        """
        :model: the source model from which to import data
        :admin: the admin class of the target data
        """
        super(FinalPage, self).__init__(parent)
        self.setTitle(_('Import Progress'))
        self.model = model
        self.admin = admin
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
            for field_name, attributes in self.model.get_admin().get_columns():
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
        """:param admin: camelot model admin of the destination data"""
        from camelot.view.proxy.collection_proxy import CollectionProxy
        super(ImportWizard, self).__init__(parent)
        assert admin

        row_data_admin = RowDataAdminDecorator(admin)
        model = CollectionProxy(
            row_data_admin,
            lambda:[],
            row_data_admin.get_columns
        )
        self.setWindowTitle(_(self.window_title))
        self.add_pages(model, admin)
        self.setOption(QtGui.QWizard.NoCancelButton)

    def add_pages(self, model, admin):
        """
        Add all pages to the import wizard, reimplement this method to add
        custom pages to the wizard.  This method is called in the __init__method, to add
        all pages to the wizard.
        
        :param model: the CollectionProxy that will be used to display the to be imported data
        :param admin: the admin of the destination data
        """
        self.addPage(SelectFilePage(parent=self))
        self.addPage(
            DataPreviewPage(
                parent=self,
                model=model,
                collection_getter=self.collection_getter
            )
        )
        self.addPage(FinalPage(parent=self, model=model, admin=admin))        
