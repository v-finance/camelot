#  ============================================================================
#
#  Copyright (C) 2007-2016 Conceptive Engineering bvba.
#  www.conceptive.be / info@conceptive.be
#
#  Redistribution and use in source and binary forms, with or without
#  modification, are permitted provided that the following conditions are met:
#      * Redistributions of source code must retain the above copyright
#        notice, this list of conditions and the following disclaimer.
#      * Redistributions in binary form must reproduce the above copyright
#        notice, this list of conditions and the following disclaimer in the
#        documentation and/or other materials provided with the distribution.
#      * Neither the name of Conceptive Engineering nor the
#        names of its contributors may be used to endorse or promote products
#        derived from this software without specific prior written permission.
#  
#  THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
#  ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
#  WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
#  DISCLAIMED. IN NO EVENT SHALL <COPYRIGHT HOLDER> BE LIABLE FOR ANY
#  DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
#  (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
#  LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
#  ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
#  (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
#  SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#
#  ============================================================================

"""Utility classes to import files into Camelot"""

import csv
import datetime
import logging
import os.path
import string


from ..core.qt import QtCore
from camelot.view.controls import delegates
from camelot.admin.admin_route import register_list_actions
from camelot.admin.action.list_action import delete_selection
from camelot.admin.object_admin import ObjectAdmin
from camelot.admin.action import Action, RowNumberAction
from camelot.view.art import ColorScheme
from camelot.core.exception import UserException
from camelot.core.utils import ugettext, ugettext_lazy as _
from camelot.view.utils import local_date_format

from . import action_steps

logger = logging.getLogger('camelot.view.import_utils')

class RowData(object):
    """Class representing the data in a single row of the imported file as an
    object with attributes column_0, column_1, ..., each representing the data
    in a single column of that row.

    since the imported file might contain less columns than expected in
    some rows, the RowData object returns None for not existing attributes
    
    :param row_data: a list containing the data
        [column_0_data, column_1_data, ...] for a single row
    """

    def __init__(self, row_number, row_data):
        self.id = row_number + 1
        i = 0
        for i, data in enumerate(row_data):
            self.__setattr__('column_%i' % i, data)
        self.columns = i + 1

    def __getattr__(self, attr_name):
        return None

    def __len__(self):
        return self.columns

    def __getitem__(self, i):
        return getattr(self, 'column_%i'%i)

def column_name(column):
    """Create a column name starting from an index starting at 0
    eg : column=0 -> name='A'
    """
    if column <= 25:
        return string.ascii_uppercase[column];
    else:
        return column_name((column//26)-1) + column_name(column%26)

class ColumnMapping( object ):
    """
    Object that maps a column in the rows to import to a field of the 
    data model.
    
    :param column: a number that indicates which column is mapped
    :param rows: the list of RowData objects to import, the list should
        not be empty    
    :param default_field: the default field that is mapped, or `None`
    
    """
    
    def __init__(self, column, rows, default_field=None):
        # show row is the row that will be previewed in the column
        # selection form
        self.column = column
        self.column_name = column_name(column)
        self.rows = rows
        self.field = default_field
        self.value = None
        self.preview_row = None
        self.set_preview_row(0)

    def get_preview_row(self):
        return self.preview_row

    def set_preview_row(self, row):
        if row >= 0 and row < len(self.rows):
            self.preview_row = row
            if self.column < len(self.rows[row]):
                self.value = self.rows[row][self.column]
            else:
                self.value = None

class ShowNext(Action):
    
    verbose_name = _('Show next')
    name = 'show_next'
    
    def model_run(self, model_context, mode):
        for mapping in model_context.get_collection():
            mapping.set_preview_row(mapping.get_preview_row()+1)
        yield action_steps.UpdateObjects(model_context.get_collection())

class ShowPrevious(Action):
    
    verbose_name = _('Show previous')
    name = 'show_previous'
    
    def model_run(self, model_context, mode):
        for mapping in model_context.get_collection():
            mapping.set_preview_row(mapping.get_preview_row()-1)
        yield action_steps.UpdateObjects(model_context.get_collection())

class MatchNames(Action):
    """Use the data in the current row to determine field names"""
    
    verbose_name = _('Match names')
    name = 'match_names'
    
    def model_run(self, model_context, mode):
        field_choices = model_context.admin.field_choices
        # create a dict that  will be used to search field names
        matches = dict( (str(verbose_name).lower(), fn)
                         for fn, verbose_name in field_choices if fn )
        matches.update( dict( (fn.lower().replace('_',''), fn)
                              for fn, _verbose_name in field_choices if fn) )
        for mapping in model_context.get_collection():
            if mapping.value is not None:
                field = matches.get(mapping.value.replace('_','').lower(), None)
                mapping.field = field
            else:
                mapping.field = None
        yield action_steps.UpdateObjects(model_context.get_collection())

class ColumnMappingAdmin(ObjectAdmin):
    """Admin class that allows the user to manipulate the column mappings
    
    :param admin: the admin object of the model in which to import
    :param entity: the class that is used to define the column mapping
    :param field_choices: the list of fields out of which the user can select
    """
    
    verbose_name = _('Select field')
    verbose_name_plural = _('Select fields')
    toolbar_actions = [ShowNext(), ShowPrevious(), MatchNames()]

    # list_action = None
    list_display = ['column_name', 'field', 'value']
    field_attributes = {'column_name': {'name':_('Column'),},}
    
    def __init__(self, admin, entity = ColumnMapping, field_choices=[]):
        super(ColumnMappingAdmin, self).__init__(admin, entity)
        self.field_choices = [(None,'')] + field_choices
        
    def get_field_attributes( self, field_name ):
        fa = ObjectAdmin.get_field_attributes(self, field_name)
        if field_name=='field':
            fa.update({'delegate':delegates.ComboBoxDelegate,
                        'editable':True,
                        'choices': self.field_choices })
        return fa
    
    @register_list_actions('_admin_route')
    def get_related_toolbar_actions(self, direction):
        return self.toolbar_actions

class ColumnSelectionAdmin(ColumnMappingAdmin):
    """Admin to edit a `ColumnMapping` class without data preview
    """
    
    list_display = ['column_name', 'field']
    list_actions = []
    related_toolbar_actions = []
    
    @register_list_actions('_admin_route')
    def get_related_toolbar_actions(self, direction):
        return self.related_toolbar_actions

# see http://docs.python.org/library/csv.html
class UTF8Recoder(object):
    """Iterator that reads an encoded stream and reencodes the input to
    UTF-8."""

    def __init__(self, f, encoding):
        self.reader = f

    def __iter__(self):
        return self

    def __next__(self):
        return next(self.reader)

# see http://docs.python.org/library/csv.html
class UnicodeReader( object ):
    """A CSV reader which will iterate over lines in the CSV file "f", which is
    encoded in the given encoding."""

    def __init__(self, f, dialect=csv.excel, encoding='utf-8', **kwds):
        f = UTF8Recoder(f, encoding)
        self.encoding = encoding
        self.reader = csv.reader(f, dialect=dialect, **kwds)
        self.line = 0

    def __next__( self ):
        self.line += 1
        try:
            row = next(self.reader)
            return row
        except UnicodeError as exception:
            raise UserException( text = ugettext('This file contains unexpected characters'),
                                 resolution = ugettext('Recreate the file with %s encoding') % self.encoding,
                                 detail = ugettext('Exception occured at line %s : ') % self.line + str( exception ) )

    def __iter__( self ):
        return self
    
class XlsReader( object ):
    """Read an XLS/XLSX file and iterator over its lines.
    
    The iterator returns each line of the excel as a list of strings.
    
    The to_string field attribute is supposed to be able to interprete those
    strings and create a valid datatype.
    
    :param filename: the name of the xls or xlsx file
    """
    
    def __init__( self, filename ):
        SUPPORTED_FORMATS = ('.xlsx', '.xlsm', '.xltx', '.xltm')
        extension = os.path.splitext(filename)[1]
        if extension not in SUPPORTED_FORMATS:
            raise UserException(
                u'{0} is not a supported file format'.format(extension),
                detail = u'supported formats are ' + u', '.join(SUPPORTED_FORMATS)
            )
        import openpyxl
        # use these options to keep memory usage under control
        workbook = openpyxl.load_workbook(
            filename, data_only=True, keep_vba=False, read_only=True
        )
        self.sheets = workbook.worksheets
        self.sheet = workbook.active
        self.date_format = local_date_format()
        self.locale = QtCore.QLocale()

    def __iter__( self ):
        for row in self.sheet.iter_rows():
            vector = []
            for cell in row:
                value = cell.value
                if value is None:
                    value = u''
                if value is True:
                    value = u'true'
                elif value is False:
                    value = u'false'
                elif isinstance(value, int):
                    # QLocale.toString doesn't seems to work with long ints
                    value = str(value)
                elif isinstance(value, float):
                    format_string = cell.number_format
                    ## try to display the number with the same precision as
                    ## it was displayed in excel
                    precision = max( 0, format_string.count('0') - 1 )
                    ## see the arguments format documentation of QString
                    ## format can be eiter 'f' or 'e', where 'e' is scientific
                    ## so maybe the format string should be parsed further to
                    ## see if it specifies scientific notation.  scientific
                    ## notation is not used because it loses precision when 
                    ## converting to a string
                    value = str(self.locale.toString(
                        value, format = 'f', precision = precision
                    ))
                elif isinstance(value, datetime.datetime):
                    dt = QtCore.QDate(value.year, value.month, value.day)
                    value = str(dt.toString(self.date_format))
                elif isinstance(value, bytes):
                    value = value.decode('utf-8')
                elif isinstance(value, str):
                    pass
                else:
                    logger.error('unknown type {0} when importing excel'.format(type(value)))
                vector.append( value )
            yield vector

class RowDataAdmin(ObjectAdmin):
    """Decorator that transforms the Admin of the class to be imported to an
    Admin of the RowData objects to be used when previewing and validating the
    data to be imported.

    based on the field attributes of the original mode, it will turn the
    background color pink if the data is invalid for being imported.
    
    :param admin: the `camelot.admin.object_admin.ObjectAdmin` admin object 
        of the objects that will be imported
    :param column_mappings: list of `ColumnMapping` object that maps the columns
        in the row data to fields of the objects.
    """

    list_action = RowNumberAction()
    list_actions = [delete_selection]
    
    def __init__(self, admin, column_mappings):
        super(RowDataAdmin, self).__init__(admin, RowData)
        self.admin = admin
        self._new_field_attributes = {}
        self._fields = []
        for column_mapping in column_mappings:
            field_name = 'column_%i'%column_mapping.column
            original_field = column_mapping.field
            if original_field != None:
                fa = self.new_field_attributes(original_field)
                self._fields.append( (field_name, fa) )
                self._new_field_attributes[field_name] = fa

    def get_columns(self):
        return [field for field, fa in self._fields]

    def get_verbose_name(self):
        return self.admin.get_verbose_name()

    def get_verbose_name_plural(self):
        return self.admin.get_verbose_name_plural()

    def get_verbose_identifier(self, obj):
        return str()

    def get_fields(self):
        return self._fields

    def get_settings(self):
        settings = self.admin.get_settings()
        settings.beginGroup('import')
        return settings

    def get_all_fields_and_attributes(self):
        """
        reimplementation needed to support replace field contents during import
        """
        return self._new_field_attributes

    def get_validator(self, model=None):
        """Creates a validator that validates the data to be imported, the
        validator will check if the background of the cell is pink, and if it
        is it will mark that object as invalid.
        """
        from camelot.admin.validator.object_validator import ObjectValidator

        class NewObjectValidator(ObjectValidator):

            def validate_object(self, obj):
                columns = self.admin.get_columns()
                dynamic_attributes = self.admin.get_dynamic_field_attributes(
                    obj,
                    columns
                )
                for attrs in dynamic_attributes:
                    if attrs['background_color'] == ColorScheme.pink_1:
                        logger.debug('we have an invalid field')
                        return ['invalid field']
                return []

        return NewObjectValidator(self, model)

    def get_related_admin(self, cls):
        return self.admin.get_related_admin(cls)

    @register_list_actions('_admin_route')
    def get_related_toolbar_actions(self, direction):
        return self.list_actions

    def get_field_attributes(self, field_name):
        return self._new_field_attributes[field_name]

    def get_static_field_attributes(self, field_names):
        for field_name in field_names:
            attributes = self.get_field_attributes(field_name)
            yield {'editable':True,
                   'name': attributes['name'],
                   'delegate': attributes['delegate'],
                   'column_width': attributes['column_width'],
                   'field_name': field_name}

    def get_dynamic_field_attributes(self, obj, field_names):
        for field_name in field_names:
            attributes = self.get_field_attributes(field_name)
            string_value = getattr(obj, field_name)
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

    def new_field_attributes(self, original_field):
        from camelot.view.controls import delegates

        original_field_attributes = self.admin.get_field_attributes(original_field)
        attributes = dict(original_field_attributes)
        attributes['delegate'] = delegates.PlainTextDelegate
        attributes['python_type'] = str
        attributes['original_field'] = original_field

        # remove some attributes that might disturb the import wizard
        for attribute in ['background_color', 'tooltip']:
            attributes[attribute] = None

        return attributes




