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
import logging
import string

import six

from ..core.qt import QtCore, Qt
from camelot.view.controls import delegates
from camelot.admin.action.list_action import DeleteSelection
from camelot.admin.object_admin import ObjectAdmin
from camelot.admin.table import Table
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
    
    def model_run(self, model_context):
        for mapping in model_context.get_collection():
            mapping.set_preview_row(mapping.get_preview_row()+1)
            yield action_steps.UpdateObject(mapping)

class ShowPrevious(Action):
    
    verbose_name = _('Show previous')
    
    def model_run(self, model_context):
        for mapping in model_context.get_collection():
            mapping.set_preview_row(mapping.get_preview_row()-1)
            yield action_steps.UpdateObject(mapping)

class MatchNames(Action):
    """Use the data in the current row to determine field names"""
    
    verbose_name = _('Match names')
    
    def model_run(self, model_context):
        field_choices = model_context.admin.field_choices
        # create a dict that  will be used to search field names
        matches = dict( (six.text_type(verbose_name).lower(), fn)
                         for fn, verbose_name in field_choices if fn )
        matches.update( dict( (fn.lower().replace('_',''), fn)
                              for fn, _verbose_name in field_choices if fn) )
        for mapping in model_context.get_collection():
            if mapping.value is not None:
                field = matches.get(mapping.value.replace('_','').lower(), None)
                mapping.field = field
            else:
                mapping.field = None
            yield action_steps.UpdateObject(mapping)

class ColumnMappingAdmin(ObjectAdmin):
    """Admin class that allows the user to manipulate the column mappings
    
    :param admin: the admin object of the model in which to import
    :param entity: the class that is used to define the column mapping
    :param field_choices: the list of fields out of which the user can select
    """
    
    verbose_name = _('Select field')
    verbose_name_plural = _('Select fields')

    list_action = None
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
    
    def get_related_toolbar_actions(self, toolbar_area, direction):
        return [ShowNext(), ShowPrevious(), MatchNames()]

class ColumnSelectionAdmin(ColumnMappingAdmin):
    """Admin to edit a `ColumnMapping` class without data preview
    """
    
    list_display = ['column_name', 'field']
    list_actions = []
    related_toolbar_actions = []
    
    def get_related_toolbar_actions(self, toolbar_area, direction):
        return self.related_toolbar_actions

# see http://docs.python.org/library/csv.html
class UTF8Recoder( six.Iterator ):
    """Iterator that reads an encoded stream and reencodes the input to
    UTF-8."""

    def __init__(self, f, encoding):
        self.reader = f

    def __iter__(self):
        return self

    def __next__(self):
        return six.next(self.reader).encode('utf-8')

# see http://docs.python.org/library/csv.html
class UnicodeReader( six.Iterator ):
    """A CSV reader which will iterate over lines in the CSV file "f", which is
    encoded in the given encoding."""

    def __init__(self, f, dialect=csv.excel, encoding='utf-8', **kwds):
        if six.PY3==False:
            f = UTF8Recoder(f, encoding)
        self.encoding = encoding
        self.reader = csv.reader(f, dialect=dialect, **kwds)
        self.line = 0

    def __next__( self ):
        self.line += 1
        try:
            row = six.next(self.reader)
            if six.PY3==False:
                return [six.text_type(s, 'utf-8') for s in row]
            else:
                return row
        except UnicodeError as exception:
            raise UserException( text = ugettext('This file contains unexpected characters'),
                                 resolution = ugettext('Recreate the file with %s encoding') % self.encoding,
                                 detail = ugettext('Exception occured at line %s : ') % self.line + six.text_type( exception ) )

    def __iter__( self ):
        return self
    
class XlsReader( six.Iterator ):
    """Read an XLS/XLSX file and iterator over its lines.
    
    The iterator returns each line of the excel as a list of strings.
    
    The to_string field attribute is supposed to be able to interprete those
    strings and create a valid datatype.
    
    :param filename: the name of the xls or xlsx file
    """
    
    def __init__( self, filename ):
        import xlrd
        try:
            workbook = xlrd.open_workbook(filename, formatting_info=True)
        except NotImplementedError:
            # xlsx does not yet support formatting info
            workbook = xlrd.open_workbook(filename)
        self.xf_list = workbook.xf_list
        self.datemode = workbook.datemode
        self.format_map = workbook.format_map
        self.sheets = workbook.sheets()
        self.sheet = self.sheets[0]
        self.current_row = 0
        self.date_format = local_date_format()
        self.locale = QtCore.QLocale()
        
    def get_format_string( self, xf_index ):
        """:return: the string that specifies the format of a cell"""
        # xlsx has no formatting info, as such the xf_index is None
        if xf_index == None:
            return '0.00'
        try:
            xf = self.xf_list[ xf_index ]
        except IndexError:
            return '0.00'
        if xf._format_flag == 0:
            return self.get_format_string( xf.parent_style_index )
        f = self.format_map[ xf.format_key ]
        return f.format_str
        
    def __next__( self ):
        import xlrd
        if self.current_row < self.sheet.nrows:
            vector = []    
            for column in range( self.sheet.ncols ):
                cell = self.sheet.cell( self.current_row, column )
                ctype = cell.ctype
                value = ''
                if ctype in( xlrd.XL_CELL_EMPTY, 
                             xlrd.XL_CELL_ERROR,
                             xlrd.XL_CELL_BLANK ):
                    pass
                elif ctype == xlrd.XL_CELL_TEXT:
                    value = six.text_type( cell.value )
                elif ctype == xlrd.XL_CELL_NUMBER:
                    format_string = self.get_format_string( cell.xf_index )
                    # try to display the number with the same precision as
                    # it was displayed in excel
                    precision = max( 0, format_string.count('0') - 1 )
                    # see the arguments format documentation of QString
                    # format can be eiter 'f' or 'e', where 'e' is scientific
                    # so maybe the format string should be parsed further to
                    # see if it specifies scientific notation.  scientific
                    # notation is not used because it loses precision when 
                    # converting to a string
                    value = six.text_type( self.locale.toString( cell.value, 
                                                           format = 'f',
                                                           precision = precision ) )
                elif ctype == xlrd.XL_CELL_DATE:
                    # this only handles dates, no datetime or time
                    date_tuple = xlrd.xldate_as_tuple( cell.value, 
                                                       self.datemode )
                    dt = QtCore.QDate( *date_tuple[:3] )
                    value = six.text_type( dt.toString( self.date_format ) )
                elif ctype == xlrd.XL_CELL_BOOLEAN:
                    value = 'false'
                    if cell.value == 1:
                        value = 'true'
                else:
                    logger.error( 'unknown ctype %s when importing excel'%ctype )
                vector.append( value )
            self.current_row += 1
            return vector
        else:
            raise StopIteration()

    def __iter__( self ):
        return self
    
class RowDataAdmin(object):
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
    list_actions = [DeleteSelection()]
    
    def __init__(self, admin, column_mappings):
        self.admin = admin
        self._new_field_attributes = {}
        self._columns = []
        for column_mapping in column_mappings:
            field_name = 'column_%i'%column_mapping.column
            original_field = column_mapping.field
            if original_field != None:
                fa = self.new_field_attributes(original_field)
                self._columns.append( (field_name, fa) )
                self._new_field_attributes[field_name] = fa

    def get_columns(self):
        return self._columns

    def __getattr__(self, attr):
        return getattr(self.admin, attr)

    def get_fields(self):
        return self.get_columns()
    
    def get_table(self):
        return Table( [fn for fn, _fa in self.get_columns()] )

    def get_validator(self, model):
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
                    [c[0] for c in columns]
                )
                for attrs in dynamic_attributes:
                    if attrs['background_color'] == ColorScheme.pink_1:
                        logger.debug('we have an invalid field')
                        return ['invalid field']
                return []

        return NewObjectValidator(self, model)

    def flush(self, obj):
        """When flush is called, don't do anything, since we'll only save the
        object when importing them for real"""
        pass

    def is_persistent(self, obj):
        return True

    def delete(self, obj):
        pass

    def get_related_toolbar_actions(self, toolbar_area, direction):
        if toolbar_area==Qt.RightToolBarArea:
            return self.list_actions

    def get_field_attributes(self, field_name):
        return self._new_field_attributes[field_name]

    def get_static_field_attributes(self, field_names):
        for _field_name in field_names:
            yield {'editable':True}

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

        original_field_attributes = self.admin.get_field_attributes( original_field )
        attributes = dict(original_field_attributes)
        attributes['delegate'] = delegates.PlainTextDelegate
        attributes['python_type'] = str
        attributes['original_field'] = original_field

        # remove some attributes that might disturb the import wizard
        for attribute in ['background_color', 'tooltip']:
            attributes[attribute] = None

        return attributes




