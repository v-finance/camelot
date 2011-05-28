#  ============================================================================
#
#  Copyright (C) 2007-2011 Conceptive Engineering bvba. All rights reserved.
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

"""Module for managing imports"""

import csv
import codecs

from PyQt4 import QtGui
from PyQt4 import QtCore

from camelot.core.utils import xls2list
from camelot.core.utils import ugettext as _
from camelot.core.utils import ugettext_lazy

from camelot.view.art import Pixmap, ColorScheme
from camelot.view.model_thread import post
from camelot.view.wizard.pages.select import SelectFilePage
from camelot.view.wizard.pages.progress_page import ProgressPage
from camelot.view.controls.editors.one2manyeditor import One2ManyEditor
from camelot.view.proxy.collection_proxy import CollectionProxy

import logging
logger = logging.getLogger('camelot.view.wizard.importwizard')

class RowData(object):
    """Class representing the data in a single row of the imported file as an
    object with attributes column_1, column_2, ..., each representing the data
    in a single column of that row.

    since the imported file might contain less columns than expected, the
    RowData object returns None for not existing attributes"""

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
    """Returns data from csv file as a list of RowData objects"""

    def __init__(self, filename):
        self.filename = filename
        self._data = None

    def __call__(self):
        if self._data==None:
            self._data = []
            import chardet

            detected = chardet.detect(open(self.filename).read())['encoding']
            enc = detected or 'utf-8'

            items = UnicodeReader(open(self.filename), encoding=enc)

            self._data = [
                RowData(i, row_data)
                for i, row_data in enumerate(items)
            ]

        return self._data


class XlsCollectionGetter(object):
    """Returns the data from excel file as a list of RowData objects"""

    def __init__(self, filename, encoding='utf-8'):
        self.filename = filename
        self.encoding = encoding
        self._data = None

    def __call__(self):
        if self._data == None:
            rows = xls2list(self.filename)[1:] # we skip the first row :)

            self._data = [
                RowData(i, row_data)
                for i, row_data in enumerate(rows)
            ]

        return self._data


class RowDataAdminDecorator(object):
    """Decorator that transforms the Admin of the class to be imported to an
    Admin of the RowData objects to be used when previewing and validating the
    data to be imported.

    based on the field attributes of the original mode, it will turn the
    background color pink if the data is invalid for being imported.
    """

    def __init__(self, object_admin):
        """:param object_admin: the object_admin object that will be
        decorated"""
        self._object_admin = object_admin
        self._new_field_attributes = {}
        self._columns = None

    def __getattr__(self, attr):
        return getattr(self._object_admin, attr)

    def create_validator(self, model):
        """Creates a validator that validates the data to be imported, the
        validator will check if the background of the cell is pink, and if it
        is it will mark that object as invalid.
        """
        from camelot.admin.validator.object_validator import ObjectValidator

        class NewObjectValidator(ObjectValidator):

            def objectValidity(self, obj):
                columns = self.admin.get_columns()
                dynamic_attributes = self.admin.get_dynamic_field_attributes(
                    obj,
                    [c[0] for c in columns]
                )
                for attrs in dynamic_attributes:
                    if attrs['background_color'] == ColorScheme.pink_1:
                        logger.debug('we have an invalid field')
                        return ['invalid field']
                return []

        return NewObjectValidator(self, model)

    def get_fields(self):
        return self.get_columns()

    def flush(self, obj):
        """When flush is called, don't do anything, since we'll only save the
        object when importing them for real"""
        pass
    
    def delete(self, obj):
        pass

    def get_field_attributes(self, field_name):
        return self._new_field_attributes[field_name]

    def get_static_field_attributes(self, field_names):
        for _field_name in field_names:
            yield {'editable':True}

    def get_dynamic_field_attributes(self, obj, field_names):
        for field_name in field_names:
            attributes = self.get_field_attributes(field_name)
            string_value = attributes['getter'](obj)
            valid = True
            value = None
            if 'from_string' in attributes:
                try:
                    value = attributes['from_string'](string_value)
                except Exception:
                    valid = False
                # 0 is valid
                if value != 0 and not value and not attributes['nullable']:
                    valid = False
            if valid:
                yield {'background_color':None}
            else:
                yield {'background_color':ColorScheme.pink_1}

    def new_field_attributes(self, i, original_field_attributes, original_field):
        from camelot.view.controls import delegates

        def create_getter(i):
            return lambda o:getattr(o, 'column_%i'%i)

        attributes = dict(original_field_attributes)
        attributes['delegate'] = delegates.PlainTextDelegate
        attributes['python_type'] = str
        attributes['original_field'] = original_field
        attributes['getter'] = create_getter(i)

        # remove some attributes that might disturb the import wizard
        for attribute in ['background_color', 'tooltip']:
            attributes[attribute] = None

        self._new_field_attributes['column_%i' %i] = attributes

        return attributes

    def get_columns(self):
        if self._columns:
            return self._columns

        original_columns = self._object_admin.get_columns()
        new_columns = [
            (
                'column_%i' %i,
                self.new_field_attributes(i, attributes, original_field)
            )
            for i, (original_field, attributes) in enumerate(original_columns)
            if attributes.get('editable',  True)
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
        validator.validity_changed_signal.connect(self.update_complete)
        model.layoutChanged.connect(self.validate_all_rows)
        post(validator.validate_all_rows)
        self.collection_getter = collection_getter

        icon = 'tango/32x32/mimetypes/x-office-spreadsheet.png'
        self.setPixmap(QtGui.QWizard.LogoPixmap, Pixmap(icon).getQPixmap())

        self.previewtable = One2ManyEditor(
            admin = model.get_admin(),
            parent = self,
            create_inline = True,
            vertical_header_clickable = False,
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

    @QtCore.pyqtSlot()
    def validate_all_rows(self):
        validator = self.model.get_validator()
        post(validator.validate_all_rows, self._all_rows_validated)

    def _all_rows_validated(self, *args):
        self.update_complete(0)

    @QtCore.pyqtSlot(int)
    def update_complete(self, row=0):
        self._complete = (self.model.get_validator().number_of_invalid_rows()==0)
        self.completeChanged.emit()
        if self._complete:
            self._note.set_value(None)
        else:
            self._note.set_value(_(
                'Please correct the data above before proceeding with the '
                'import.<br/>Incorrect cells have a pink background.'
            ))

    def initializePage(self):
        """Gets all info needed from SelectFilePage and feeds table"""
        filename = self.field('datasource').toString()
        self._complete = False
        self.completeChanged.emit()
        self.model.set_collection_getter(self.collection_getter(filename))
        self.previewtable.set_value(self.model)
        self.validate_all_rows()

    def validatePage(self):
        answer = QtGui.QMessageBox.question(
            self,
            _('Proceed with import'),
            _('Importing data cannot be undone,\n'
              'are you sure you want to continue'),
            QtGui.QMessageBox.Cancel,
            QtGui.QMessageBox.Ok,
        )
        if answer == QtGui.QMessageBox.Ok:
            return True
        return False

    def isComplete(self):
        return self._complete


class FinalPage(ProgressPage):
    """FinalPage is the final page in the import process"""

    title = ugettext_lazy('Import Progress')
    sub_title = ugettext_lazy('Please wait while data is being imported.')

    def __init__(self, parent=None, model=None, admin=None):
        """
        :model: the source model from which to import data
        :admin: the admin class of the target data
        """
        super(FinalPage, self).__init__(parent)
        self.model = model
        self.admin = admin
        icon = 'tango/32x32/mimetypes/x-office-spreadsheet.png'
        self.setPixmap(QtGui.QWizard.LogoPixmap, Pixmap(icon).getQPixmap())
        self.setButtonText(QtGui.QWizard.FinishButton, _('Close'))
        self.progressbar = QtGui.QProgressBar()

    def run(self):
        collection = self.model.get_collection()
        self.update_maximum_signal.emit( len(collection) )
        for i,row in enumerate(collection):
            new_entity_instance = self.admin.entity()
            for field_name, attributes in self.model.get_admin().get_columns():
                try:
                    from_string = attributes['from_string']
                except KeyError:
                    logger.warn( 'field %s has no from_string field attribute, dont know how to import it properly'%attributes['original_field'] )
                    from_string = lambda _a:None
                setattr(
                    new_entity_instance,
                    attributes['original_field'],
                    from_string(getattr(row, field_name))
                )
            self.admin.add(new_entity_instance)
            self.admin.flush(new_entity_instance)
            self.update_progress_signal.emit(
                i, _('Row %i of %i imported') % (i+1, len(collection))
            )


class DataPreviewCollectionProxy(CollectionProxy):
    header_icon = None


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
    rowdata_admin_decorator = RowDataAdminDecorator

    def __init__(self, parent=None, admin=None):
        """:param admin: camelot model admin of the destination data"""
        super(ImportWizard, self).__init__(parent)
        assert admin
        #
        # Set the size of the wizard to 2/3rd of the screen, since we want to
        # get some work done here, the user needs to verify and possibly
        # correct its data
        #
        desktop = QtCore.QCoreApplication.instance().desktop()
        self.setMinimumSize(desktop.width()*2/3, desktop.height()*2/3)

        row_data_admin = self.rowdata_admin_decorator(admin)
        model = DataPreviewCollectionProxy(
            row_data_admin,
            lambda:[],
            row_data_admin.get_columns
        )
        self.setWindowTitle(self.window_title)
        self.add_pages(model, admin)
        self.setOption(QtGui.QWizard.NoCancelButton)

    def add_pages(self, model, admin):
        """
        Add all pages to the import wizard, reimplement this method to add
        custom pages to the wizard.  This method is called in the __init__
        method, to add all pages to the wizard.

        :param model: the CollectionProxy that will be used to display the to
        be imported data
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



