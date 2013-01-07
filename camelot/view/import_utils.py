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

"""Utility classes to import files into Camelot"""

from PyQt4 import QtCore

import csv
import codecs
import itertools
import logging

from camelot.view import forms
from camelot.view.controls import delegates
from camelot.admin.object_admin import ObjectAdmin
from camelot.view.art import ColorScheme
from camelot.core.exception import UserException
from camelot.core.utils import ugettext, ugettext_lazy as _
from camelot.view.utils import local_date_format

logger = logging.getLogger('camelot.view.import_utils')

class RowData(object):
    """Class representing the data in a single row of the imported file as an
    object with attributes column_1, column_2, ..., each representing the data
    in a single column of that row.

    since the imported file might contain less columns than expected in
    some rows, the RowData object returns None for not existing attributes"""

    def __init__(self, row_number, row_data):
        """:param row_data: a list containing the data
        [column_1_data, column_2_data, ...] for a single row
        """
        self.id = row_number + 1
        for i, data in enumerate(row_data):
            self.__setattr__('column_%i' % i, data)
        self.columns = i + 1

    def __getattr__(self, attr_name):
        return None
    
class ColumnMapping( object ):
    """
    Object that maps the columns in the rows to import onto the fields of the 
    data model.  This object has attributes named `column_1_field`, 
    `column_2_field`, ...  Each of these attributes should be set to the field
    name in which the data of the column should be imported.
    
    :param columns: the number of columns in the rows
    :param rows: the list of RowData objects to import, the list should
        not be empty    
    :param admin: the admin object of the model in which to import
    """
    
    def __init__( self, columns, rows, admin ):
        # show row is the row that will be previewed in the column
        # selection form
        self.columns = columns
        self.rows = rows
        for i in range( self.columns ):
            setattr( self, 'column_%i_field'%i, None )
        self.__setattr__( 'show_row', 1 )
        # by default use the order of the fields as they appear
        # in the list_display
        for i, (list_field, fa) in itertools.izip( range( self.columns ), 
                                                    admin.get_columns() ):
            if fa.get('editable', False):
                setattr( self, 'column_%i_field'%i, list_field )        
    
    def __setattr__( self, attr, value ):
        if attr == 'show_row':
            if value > 0 and value <= len(self.rows):
                for i in range( self.columns ):
                    setattr( self, 'column_%i_value'%i, getattr( self.rows[value - 1],
                                                                 'column_%i'%i ) )
        super( ColumnMapping, self ).__setattr__( attr, value )        
            
class ColumnMappingAdmin( ObjectAdmin ):
    """Admin class that allows the user to manipulate the column mapping
    
    :param columns: the number of columns for which to edit the mapping
    :param admin: the admin object of the model in which to import
    :param entity: the class that is used to define the column mapping
    """
    
    verbose_name = _('Select fields')
    
    field_attributes = { 'show_row' : { 'editable':True,
                                        'calculator':False,
                                        'delegate':delegates.IntegerDelegate }
                         }
    
    def __init__( self, columns, admin, entity = ColumnMapping ):
        self.columns = columns
        self.admin = admin
        super( ColumnMappingAdmin, self ).__init__( admin, entity )
        
    def get_field_attributes( self, field_name ):
        fa = ObjectAdmin.get_field_attributes( self, field_name )
        if field_name.startswith( 'column' ) and field_name.endswith('field'):
            field_choices = [(f,entity_fa['name']) for f,entity_fa in 
                             self.admin.get_all_fields_and_attributes().items() 
                             if entity_fa.get('editable', True)]
            fa.update( { 'delegate':delegates.ComboBoxDelegate,
                         'editable':True,
                         'choices': [(None,'')] + field_choices } )
        return fa
            
    def get_form_display( self ):
        columns = self.columns
        rows = [ [ 'column_%i_value'%i,
                   'column_%i_field'%i ] for i in range( columns ) 
                                 ]
        return forms.Form( [ 'show_row',
                             forms.GridForm( rows ) ], scrollbars = True )

# see http://docs.python.org/library/csv.html
class UTF8Recoder( object ):
    """Iterator that reads an encoded stream and reencodes the input to
    UTF-8."""

    def __init__(self, f, encoding):
        self.reader = codecs.getreader(encoding)(f)

    def __iter__(self):
        return self

    def next(self):
        return self.reader.next().encode('utf-8')

# see http://docs.python.org/library/csv.html
class UnicodeReader( object ):
    """A CSV reader which will iterate over lines in the CSV file "f", which is
    encoded in the given encoding."""

    def __init__(self, f, dialect=csv.excel, encoding='utf-8', **kwds):
        f = UTF8Recoder(f, encoding)
        self.encoding = encoding
        self.reader = csv.reader(f, dialect=dialect, **kwds)
        self.line = 0

    def next( self ):
        self.line += 1
        try:
            row = self.reader.next()
            return [unicode(s, 'utf-8') for s in row]
        except UnicodeError, exception:
            raise UserException( text = ugettext('This file contains unexpected characters'),
                                 resolution = ugettext('Recreate the file with %s encoding') % self.encoding,
                                 detail = ugettext('Exception occured at line %s : ') % self.line + unicode( exception ) )

    def __iter__( self ):
        return self
    
class XlsReader( object ):
    """Read an XLS file and iterator over its lines.
    
    The iterator returns each line of the excel as a list of strings.
    
    The to_string field attribute is supposed to be able to interprete those
    strings and create a valid datatype.
    """
    
    def __init__( self, filename ):
        import xlrd
        # assume a single sheet xls doc
        workbook = xlrd.open_workbook( filename,
                                       formatting_info = True )
        self.xf_list = workbook.xf_list
        self.datemode = workbook.datemode
        self.format_map = workbook.format_map
        self.sheet = workbook.sheets()[0]
        self.current_row = 0
        self.rows = self.sheet.nrows
        self.date_format = local_date_format()
        self.locale = QtCore.QLocale()
        
    def get_format_string( self, xf_index ):
        """:return: the string that specifies the format of a cell"""
        try:
            xf = self.xf_list[ xf_index ]
        except IndexError:
            return '0.00'
        if xf._format_flag == 0:
            return self.get_format_string( xf.parent_style_index )
        f = self.format_map[ xf.format_key ]
        return f.format_str
        
    def next( self ):
        import xlrd
        if self.current_row < self.rows:
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
                    value = unicode( cell.value )
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
                    value = unicode( self.locale.toString( cell.value, 
                                                           format = 'f',
                                                           precision = precision ) )
                elif ctype == xlrd.XL_CELL_DATE:
                    # this only handles dates, no datetime or time
                    date_tuple = xlrd.xldate_as_tuple( cell.value, 
                                                       self.datemode )
                    dt = QtCore.QDate( *date_tuple[:3] )
                    value = unicode( dt.toString( self.date_format ) )
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
    :param column_mapping: the `ColumnMapping` object that maps the columns
        in the row data to fields of the objects.
    """

    list_action = None
    
    def __init__(self, admin, column_mapping):
        self.admin = admin
        self._new_field_attributes = {}
        self._columns = None

    def __getattr__(self, attr):
        return getattr(self._object_admin, attr)

    def get_fields(self):
        return self.get_columns()

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

        original_columns = self.admin.get_columns()
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

