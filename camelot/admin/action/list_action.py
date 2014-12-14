#  ============================================================================
#
#  Copyright (C) 2007-2013 Conceptive Engineering bvba. All rights reserved.
#  www.conceptive.be / info@conceptive.be
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
#  visit www.python-camelot.com or contact info@conceptive.be
#
#  This file is provided AS IS with NO WARRANTY OF ANY KIND, INCLUDING THE
#  WARRANTY OF DESIGN, MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE.
#
#  For use of this library in commercial applications, please contact
#  info@conceptive.be
#
#  ============================================================================

import codecs
import copy
import datetime
import logging

import six

from ...core.qt import QtGui, variant_to_py, py_to_variant
from .base import Action
from .application_action import ( ApplicationActionGuiContext,
                                 ApplicationActionModelContext )
from camelot.core.exception import UserException
from camelot.core.utils import ugettext, ugettext_lazy as _
from camelot.view.art import Icon

LOGGER = logging.getLogger( 'camelot.admin.action.list_action' )

class ListActionModelContext( ApplicationActionModelContext ):
    """On top of the attributes of the 
    :class:`camelot.admin.action.application_action.ApplicationActionModelContext`, 
    this context contains :
        
    .. attribute:: selection_count
    
        the number of selected rows.
        
    .. attribute:: collection_count
    
        the number of rows in the list.
        
    .. attribute:: selected_rows
    
        an ordered list with tuples of selected row ranges.  the range is
        inclusive.
        
    .. attribute:: current_row
    
        the current row in the list
        
    .. attribute:: session
    
        The session to which the objects in the list belong.
        
    .. attribute:: field_attributes
    
        The field attributes of the field to which the list relates, for example
        the attributes of Person.addresses if the list is the list of addresses
        of the Person.
       
    The :attr:`collection_count` and :attr:`selection_count` attributes allow the 
    :meth:`model_run` to quickly evaluate the size of the collection or the
    selection without calling the potentially time consuming methods
    :meth:`get_collection` and :meth:`get_selection`.

    """
    
    def __init__( self ):
        super( ListActionModelContext, self ).__init__()
        self._model = None
        self.admin = None
        self.current_row = None
        self.selection_count = 0
        self.collection_count = 0
        self.selected_rows = []
        self.field_attributes = dict()
        
    def get_selection( self, yield_per = None ):
        """
        :param yield_per: an integer number giving a hint on how many objects
            should fetched from the database at the same time.
        :return: a generator over the objects selected
        """
        # during deletion or duplication, the collection might
        # change, while the selection remains the same, so we should
        # be careful when using the collection to generate selection data
        for (first_row, last_row) in self.selected_rows:
            for row in range( first_row, last_row + 1 ):
                yield self._model._get_object( row )
    
    def get_collection( self, yield_per = None ):
        """
        :param yield_per: an integer number giving a hint on how many objects
            should fetched from the database at the same time.
        :return: a generator over the objects in the list
        """
        for obj in self._model.get_collection():
            yield obj
            
    def get_object( self ):
        """
        :return: the object displayed in the current row or None
        """
        if self.current_row is not None:
            return self._model._get_object( self.current_row )
        
class ListActionGuiContext( ApplicationActionGuiContext ):
    """The context for an :class:`Action` on a table view.  On top of the attributes of the 
    :class:`camelot.admin.action.application_action.ApplicationActionGuiContext`, 
    this context contains :

    .. attribute:: item_view
    
       the :class:`QtGui.QAbstractItemView` class that relates to the table 
       view on which the widget will be placed.
       
    .. attribute:: view
    
       a :class:`camelot.view.controls.view.AbstractView` class that represents
       the view in which the action is triggered.
       
    .. attribute:: field_attributes
    
       a dictionary with the field attributes of the list.  This dictionary will
       be filled in case if the list displayed is related to a field on another
       object.  For example, the list of addresses of Person will have the field
       attributes of the Person.addresses field when displayed on the Person 
       form.
       
    """
        
    model_context = ListActionModelContext
    
    def __init__( self ):
        super( ListActionGuiContext, self ).__init__()
        self.item_view = None
        self.view = None
        self.field_attributes = dict()

    def get_window(self):
        if self.item_view is not None:
            return self.item_view.window()
        return super(ListActionGuiContext, self).get_window()

    def create_model_context( self ):
        context = super( ListActionGuiContext, self ).create_model_context()
        context.field_attributes = copy.copy( self.field_attributes )
        current_row = None
        model = None
        collection_count = 0
        selection_count = 0
        selected_rows = []
        if self.item_view is not None:
            current_index = self.item_view.currentIndex()
            if current_index.isValid():
                current_row = current_index.row()
            model = self.item_view.model()
            if model is not None:
                collection_count = model.rowCount()
            if self.item_view.selectionModel() is not None:
                selection = self.item_view.selectionModel().selection()
                for i in range( len( selection ) ):
                    selection_range = selection[i]
                    rows_range = ( selection_range.top(), selection_range.bottom() )
                    selected_rows.append( rows_range )
                    selection_count += ( rows_range[1] - rows_range[0] ) + 1
        context.selection_count = selection_count
        context.collection_count = collection_count
        context.selected_rows = selected_rows
        context.current_row = current_row
        context._model = model
        return context
        
    def copy( self, base_class = None ):
        new_context = super( ListActionGuiContext, self ).copy( base_class )
        new_context.item_view = self.item_view
        new_context.view = self.view
        return new_context

class CallMethod( Action ):
    """
    Call a method on all objects in a selection, and flush the
    session.
    
    :param verbose_name: the name of the action, as it should appear
        to the user
    :param method: the method to call on the objects
    :param enabled: method to call on objects to verify if the action is
        enabled, by default the action is always enabled
        
    This action can be used either within :attr:`list_actions` or within
    :attr:`form_actions`.
    """
        
    def __init__( self, verbose_name, method, enabled=None ):
        self.verbose_name = verbose_name
        self.method = method
        self.enabled = enabled
        
    def model_run( self, model_context ):
        from camelot.view.action_steps import ( UpdateProgress, 
                                                FlushSession,
                                                UpdateObject )
        step = max( 1, model_context.selection_count / 100 )
        for i, obj in enumerate( model_context.get_selection() ):
            if i%step == 0:
                yield UpdateProgress( i, model_context.selection_count )
            self.method( obj )
            # the object might have changed without the need to be flushed
            # to the database
            yield UpdateObject( obj )
        yield FlushSession( model_context.session )
        
    def get_state( self, model_context ):
        state = super( CallMethod, self ).get_state( model_context )
        if self.enabled != None:
            for obj in model_context.get_selection():
                if not self.enabled( obj ):
                    state.enabled = False
                    break
        return state
            
class ListContextAction( Action ):
    """An base class for actions that should only be enabled if the
    gui_context is a :class:`ListActionModelContext`
    """
    
    def get_state( self, model_context ):
        state = super( ListContextAction, self ).get_state( model_context )
        if isinstance( model_context, ListActionModelContext ):
            state.enabled = True
        else:
            state.enabled = False
        return state

class RowNumberAction( Action ):
    """
    An action that simply displays the current row number as its name to
    the user.
    """

    def get_state( self, model_context ):
        state = super(RowNumberAction, self).get_state(model_context)
        state.verbose_name = str(model_context.current_row + 1)
        return state

class EditAction( ListContextAction ):
    """A base class for an action that will modify the model, it will be
    disabled when the field_attributes for the relation field are set to 
    not-editable.
    """

    def get_state( self, model_context ):
        state = super( EditAction, self ).get_state( model_context )
        if isinstance( model_context, ListActionModelContext ):
            editable = model_context.field_attributes.get( 'editable', True )
            if editable == False:
                state.enabled = False
        return state

class OpenFormView( ListContextAction ):
    """Open a form view for the current row of a list."""
    
    shortcut = QtGui.QKeySequence.Open
    icon = Icon('tango/16x16/places/folder.png')
    tooltip = _('Open')
    # verbose name is set to None to avoid displaying it in the vertical
    # header of the table view
    verbose_name = None

    def model_run(self, model_context):
        from camelot.view import action_steps
        yield action_steps.OpenFormView(objects=None, admin=model_context.admin)

class ChangeAdmin( Action ):
    """Change the admin of a tableview, this action is used to switch from
    one subclass to another in a table view.
    """
    
    def __init__(self, admin):
        super(ChangeAdmin, self).__init__()
        self.admin = admin
    
    def model_run(self, model_context):
        from camelot.view import action_steps
        yield action_steps.UpdateTableView(self.admin,
                                           self.admin.get_query())
    
class DuplicateSelection( EditAction ):
    """Duplicate the selected rows in a table"""
    
    shortcut = QtGui.QKeySequence.Copy
    icon = Icon('tango/16x16/actions/edit-copy.png')
    tooltip = _('Duplicate')
    verbose_name = _('Duplicate')
    
    def model_run( self, model_context ):
        from camelot.view import action_steps
        for i, obj in enumerate( model_context.get_selection() ):
            yield action_steps.UpdateProgress( i, 
                                               model_context.selection_count,
                                               self.verbose_name )
            new_object = model_context.admin.copy( obj )
            model_context._model.append_object( new_object )
        yield action_steps.FlushSession( model_context.session )
            
class DeleteSelection( EditAction ):
    """Delete the selected rows in a table"""
    
    shortcut = QtGui.QKeySequence.Delete
    icon = Icon('tango/16x16/places/user-trash.png')
    tooltip = _('Delete')
    verbose_name = _('Delete')
    
    def gui_run( self, gui_context ):
        #
        # if there is an open editor on a row that will be deleted, there
        # might be an assertion failure in QT, or the data of the editor 
        # might be pushed to the row that replaces the deleted one
        #
        gui_context.item_view.close_editor()
        super( DeleteSelection, self ).gui_run( gui_context )
        # this refresh call could be avoided if the removal of an object
        # in the collection through the DeleteObject action step handled this
        gui_context.item_view.model().refresh()
        gui_context.item_view.clearSelection()

    def model_run( self, model_context ):
        from camelot.view import action_steps
        if model_context.selection_count <= 0:
            raise StopIteration
        admin = model_context.admin
        objects_to_remove = list( model_context.get_selection() )
        #
        # it might be impossible to determine the depending objects once
        # the object has been removed from the collection
        #
        depending_objects = set()
        for o in objects_to_remove:
            depending_objects.update( set( admin.get_depending_objects( o ) ) )
        for i, obj in enumerate( objects_to_remove ):
            yield action_steps.UpdateProgress( i, 
                                               model_context.selection_count,
                                               _('Removing') )
            #
            # We should not update depending objects that have
            # been deleted themselves
            #
            try:
                depending_objects.remove( obj )
            except KeyError:
                pass
            for step in self.handle_object( model_context, obj ):
                yield step
        for depending_obj in depending_objects:
            yield action_steps.UpdateObject( depending_obj )
        yield action_steps.FlushSession( model_context.session )
        
    def handle_object( self, model_context, obj ):
        from camelot.view import action_steps
        yield action_steps.DeleteObject( obj )
        model_context.admin.delete( obj )

class AbstractToPrevious(object):
    shortcut = QtGui.QKeySequence.MoveToPreviousPage
    icon = Icon('tango/16x16/actions/go-previous.png')
    tooltip = _('Previous')
    verbose_name = _('Previous')
    
class ToPreviousRow( AbstractToPrevious, ListContextAction ):
    """Move to the previous row in a table"""

    def gui_run( self, gui_context ):
        item_view = gui_context.item_view
        selection = item_view.selectedIndexes()
        rows = item_view.model().rowCount()
        if rows <= 0:
            return
        if selection:
            current_row = selection[0].row()
            previous_row = ( current_row - 1 ) % rows
        else:
            previous_row = 0
        item_view.selectRow( previous_row )

    def get_state( self, model_context ):
        state = super( ToPreviousRow, self ).get_state( model_context )
        #if state.enabled:
        #    state.enabled = ( model_context.current_row > 0 )
        return state

class AbstractToFirst(object):
    shortcut = QtGui.QKeySequence.MoveToStartOfDocument
    icon = Icon('tango/16x16/actions/go-first.png')
    tooltip = _('First')
    verbose_name = _('First')

class ToFirstRow( AbstractToFirst, ToPreviousRow ):
    """Move to the first row in a table"""

    def gui_run( self, gui_context ):
        gui_context.item_view.selectRow( 0 )

class AbstractToNext(object):
    shortcut = QtGui.QKeySequence.MoveToNextPage
    icon = Icon('tango/16x16/actions/go-next.png')
    tooltip = _('Next')
    verbose_name = _('Next')
    
class ToNextRow( AbstractToNext, ListContextAction ):
    """Move to the next row in a table"""
    
    def gui_run( self, gui_context ):
        item_view = gui_context.item_view
        selection = item_view.selectedIndexes()
        rows = item_view.model().rowCount()
        if rows <= 0:
            return
        if selection:
            current_row = selection[0].row()
            next_row = ( current_row + 1 ) % rows
        else:
            next_row = 0
        item_view.selectRow( next_row )

    def get_state( self, model_context ):
        state = super( ToNextRow, self ).get_state( model_context )
        #if state.enabled:
        #    max_row = model_context.collection_count - 1
        #    state.enabled = ( model_context.current_row < max_row )
        return state

class AbstractToLast(object):
    shortcut = QtGui.QKeySequence.MoveToEndOfDocument
    icon = Icon('tango/16x16/actions/go-last.png')
    tooltip = _('Last')
    verbose_name = _('Last')
    
class ToLastRow( AbstractToLast, ToNextRow ):
    """Move to the last row in a table"""

    def gui_run( self, gui_context ):
        item_view = gui_context.item_view
        item_view.selectRow( item_view.model().rowCount() - 1 )

class SaveExportMapping( Action ):
    """
    Save the user defined order of columns to export
    """

    verbose_name = _('Save')
    tooltip = _('Save the order of the columns for future use')

    def __init__(self, settings):
        self.settings = settings

    def read_mappings(self):
        mappings = dict()
        number_of_mappings = self.settings.beginReadArray('mappings')
        for i in range(number_of_mappings):
            self.settings.setArrayIndex(i)
            name = variant_to_py(self.settings.value('name', py_to_variant(b'')))
            number_of_columns = self.settings.beginReadArray('columns')
            columns = list()
            for j in range(number_of_columns):
                self.settings.setArrayIndex(j)
                field = variant_to_py(self.settings.value('field',
                                                          py_to_variant(b'')))
                columns.append(field)
            self.settings.endArray()
            mappings[name] = columns
        self.settings.endArray()
        return mappings

    def write_mappings(self, mappings):
        self.settings.beginWriteArray('mappings')
        for i, (name, columns) in enumerate(mappings.items()):
            self.settings.setArrayIndex(i)
            self.settings.setValue('name', name)
            self.settings.beginWriteArray('columns')
            for j, column in enumerate(columns):
                self.settings.setArrayIndex(j)
                self.settings.setValue('field', column)
            self.settings.endArray()
        self.settings.endArray()

    def model_run(self, model_context):
        from ..object_admin import ObjectAdmin
        from camelot.view import action_steps

        class ExportMappingOptions(object):

            def __init__(self):
                self.name = None

            class Admin(ObjectAdmin):
                list_display = ['name']
                field_attributes = {'name': {'editable': True,
                                             'nullable': False}}

        if model_context.collection_count:
            mappings = self.read_mappings()
            options = ExportMappingOptions()
            yield action_steps.ChangeObject(options)
            columns = [column_mapping.field for column_mapping in model_context.get_collection() if column_mapping.field]
            mappings[options.name] = columns
            self.write_mappings(mappings)

class RestoreExportMapping( SaveExportMapping ):
    """
    Restore the user defined order of columns to export
    """

    verbose_name = _('Restore')
    tooltip = _('Restore the previously stored order of the columns')

    def model_run(self, model_context):
        from camelot.view import action_steps

        mappings = self.read_mappings()
        mapping_names = [(k,k) for k in six.iterkeys(mappings)]
        mapping_name = yield action_steps.SelectItem(mapping_names)
        if mapping_name:
            fields = mappings[mapping_name]
            for i, column_mapping in enumerate(model_context.get_collection()):
                if i<len(fields):
                    # the stored field might no longer exist
                    for field, _name in model_context.admin.field_choices:
                        if field==fields[i]:
                            column_mapping.field = fields[i]
                            break
                else:
                    column_mapping.field = None
                yield action_steps.UpdateObject(column_mapping)

class ExportSpreadsheet( ListContextAction ):
    """Export all rows in a table to a spreadsheet"""
    
    icon = Icon('tango/16x16/mimetypes/x-office-spreadsheet.png')
    tooltip = _('Export to MS Excel')
    verbose_name = _('Export to MS Excel')
    
    font_name = 'Arial'
    
    def model_run( self, model_context ):
        from decimal import Decimal
        from xlwt import Font, Borders, XFStyle, Pattern, Workbook
        from camelot.view.import_utils import ( ColumnMapping,
                                                ColumnSelectionAdmin )
        from camelot.view.utils import ( local_date_format, 
                                         local_datetime_format,
                                         local_time_format )
        from camelot.view import action_steps
        #
        # Select the columns that need to be exported
        # 
        yield action_steps.UpdateProgress(text=_('Prepare export'))
        admin = model_context.admin
        settings = admin.get_settings()
        settings.beginGroup('export_spreadsheet')
        all_fields = admin.get_all_fields_and_attributes()
        field_choices = [(f,six.text_type(entity_fa['name'])) for f,entity_fa in
                         six.iteritems(all_fields) ]
        field_choices.sort(key=lambda field_tuple:field_tuple[1])
        row_data = [None] * len(all_fields)
        column_range = six.moves.range(len(all_fields))
        mappings = []
        for i, default_field in six.moves.zip_longest(column_range,
                                                      admin.get_columns(),
                                                      fillvalue=(None,None)):
            mappings.append(ColumnMapping(i, [row_data], default_field[0]))
            
        mapping_admin = ColumnSelectionAdmin(admin, field_choices=field_choices)
        mapping_admin.related_toolbar_actions = [SaveExportMapping(settings),
                                                 RestoreExportMapping(settings)]
        change_mappings = action_steps.ChangeObjects(mappings, mapping_admin)
        change_mappings.title = _('Select field')
        change_mappings.subtitle = _('Specify for each column the field to export')
        yield change_mappings
        settings.endGroup()
        columns = []
        for i, mapping in enumerate(mappings):
            if mapping.field is not None:
                columns.append((mapping.field, all_fields[mapping.field]))
        #
        # setup worksheet
        #
        yield action_steps.UpdateProgress( text = _('Create worksheet') )
        workbook = Workbook()
        worksheet = workbook.add_sheet('Sheet1')
        #
        # keep a global cache of styles, since the number of styles that
        # can be used is limited.
        #
        styles = dict()
        freeze = lambda d:tuple(sorted(six.iteritems(d)))
        
        def get_style( font_specs=dict(), 
                       border_specs = dict(), 
                       pattern = None,
                       num_format_str = None, ):
            
            style_key = ( freeze(font_specs), 
                          freeze(border_specs), 
                          pattern, 
                          num_format_str )
            
            try:
                return styles[style_key]
            except KeyError:
                style = XFStyle()
                style.font = Font()
                for key, value in six.iteritems(font_specs):
                    setattr( style.font, key, value )
                style.borders = Borders()
                for key, value in six.iteritems(border_specs):
                    setattr( style.borders, key, value )
                if pattern:
                    style.pattern = pattern
                if num_format_str:
                    style.num_format_str = num_format_str
                styles[ style_key ] = style
                return style
        
        #
        # write style
        #
        title_style = get_style( dict( font_name = self.font_name,
                                       bold = True,
                                       height = 240 ) )
        worksheet.write( 0, 0, admin.get_verbose_name_plural(), title_style )
        #
        # create some patterns and formats
        #
        date_format = local_date_format()
        datetime_format = local_datetime_format()
        time_format = local_time_format()
        header_pattern = Pattern()
        header_pattern.pattern = Pattern.SOLID_PATTERN
        header_pattern.pattern_fore_colour = 0x16
        #
        # write headers
        #
        field_names = []
        for i, (name, field_attributes) in enumerate( columns ):
            verbose_name = six.text_type( field_attributes.get( 'name', name ) )
            field_names.append( name )
            font_specs = dict( font_name = self.font_name, 
                               bold = True, 
                               height = 200 )
            border_specs = dict( top = 0x01 )
            name = six.text_type( name )
            if i == 0:
                border_specs[ 'left' ] = 0x01                
            elif i == len( columns ) - 1:
                border_specs[ 'right' ] = 0x01 
            header_style = get_style( font_specs, border_specs, header_pattern )
            worksheet.write( 2, i, verbose_name, header_style)
                
            if len( name ) < 8:
                worksheet.col( i ).width = 8 *  375
            else:
                worksheet.col( i ).width = len( verbose_name ) *  375
        #
        # write data
        #
        offset = 3
        static_attributes = list(admin.get_static_field_attributes(field_names)) 
        for j, obj in enumerate( model_context.get_collection( yield_per = 100 ) ):
            dynamic_attributes = admin.get_dynamic_field_attributes( obj, 
                                                                     field_names )
            row = offset + j
            if j % 100 == 0:
                yield action_steps.UpdateProgress( j, model_context.collection_count )
            fields = enumerate(six.moves.zip(field_names, 
                                             static_attributes,
                                             dynamic_attributes))
            for i, (name, attributes, delta_attributes) in fields:
                attributes.update( delta_attributes )
                value = getattr( obj, name )
                format_string = '0'
                if value != None:
                    if isinstance( value, Decimal ):
                        value = float( str( value ) )
                    if isinstance( value, six.string_types ):
                        if attributes.get( 'translate_content', False ) == True:
                            value = ugettext( value )
                    elif isinstance( value, list ):
                        separator = attributes.get('separator', u', ')
                        value = separator.join([six.text_type(el) for el in value])
                    elif isinstance( value, float ):
                        precision = attributes.get( 'precision', 2 )
                        format_string = '0.' + '0'*precision
                    elif isinstance( value, int ):
                        format_string = '0'
                    elif isinstance( value, datetime.date ):
                        format_string = date_format
                    elif isinstance( value, datetime.datetime ):
                        format_string = datetime_format
                    elif isinstance( value, datetime.time ):
                        format_string = time_format
                    else:
                        value = six.text_type( value )
                else:
                    # empty cells should be filled as well, to get the
                    # borders right
                    value = ''
                        
                font_specs = dict( font_name = self.font_name, height = 200 )
                border_specs = dict()
                if i == 0:
                    border_specs[ 'left' ] = 0x01                
                elif i == len( columns ) - 1:
                    border_specs[ 'right' ] = 0x01  
                if (row - offset + 1) == model_context.collection_count:
                    border_specs[ 'bottom' ] = 0x01
                style = get_style( font_specs, 
                                   border_specs, 
                                   None, 
                                   format_string )
                worksheet.write( row, i, value, style )
                min_width = len( six.text_type( value ) ) * 300
                worksheet.col( i ).width = max( min_width, worksheet.col( i ).width )
        
        yield action_steps.UpdateProgress( text = _('Saving file') )
        filename = action_steps.OpenFile.create_temporary_file( '.xls' )
        workbook.save( filename )
        yield action_steps.UpdateProgress( text = _('Opening file') )
        yield action_steps.OpenFile( filename )
    
class PrintPreview( ListContextAction ):
    """Print all rows in a table"""
    
    icon = Icon('tango/16x16/actions/document-print-preview.png')
    tooltip = _('Print Preview')
    verbose_name = _('Print Preview')

    def model_run( self, model_context ):
        from camelot.view import action_steps
        columns = model_context.admin.get_columns()
        
        table = []
        fields = [field for field, _field_attributes in columns]
        to_strings = [field_attributes['to_string'] for _field, field_attributes in columns]
        column_range = six.moves.range( len( columns ) )
        for obj in model_context.get_collection():
            table.append( [to_strings[i]( getattr( obj, fields[i] ) ) for i in column_range] )
        context = {
          'title': model_context.admin.get_verbose_name_plural(),
          'table': table,
          'columns': [field_attributes['name'] for _field, field_attributes in columns],
        }
        yield action_steps.PrintJinjaTemplate( template = 'list.html',
                                               context = context )

class SelectAll( ListContextAction ):
    """Select all rows in a table"""
    
    verbose_name = _('Select &All')
    shortcut = QtGui.QKeySequence.SelectAll
    tooltip = _('Select all rows in the table')

    def gui_run( self, gui_context ):
        gui_context.item_view.selectAll()
        
class ImportFromFile( EditAction ):
    """Import a csv file in the current table"""
    
    verbose_name = _('Import from file')
    icon = Icon('tango/16x16/mimetypes/text-x-generic.png')
    tooltip = _('Import from file')

    def model_run( self, model_context ):
        import os.path
        import chardet
        from camelot.view import action_steps
        from camelot.view.import_utils import ( UnicodeReader, 
                                                RowData, 
                                                RowDataAdmin,
                                                XlsReader,
                                                ColumnMapping,
                                                ColumnMappingAdmin )
        file_names = yield action_steps.SelectFile()
        for file_name in file_names:
            yield action_steps.UpdateProgress( text = _('Reading data') )
            #
            # read the data into temporary row_data objects
            #
            if os.path.splitext( file_name )[-1] in ('.xls', '.xlsx'):
                items = list(XlsReader(file_name))
            else:
                detected = chardet.detect(open(file_name, 'rb').read())['encoding']
                enc = detected or 'utf-8'
                items = list(UnicodeReader(codecs.open(file_name, encoding=enc), encoding = enc ))
            collection = [ RowData(i, row_data) for i, row_data in enumerate( items ) ]
            if len( collection ) < 1:
                raise UserException( _('No data in file' ) )
            #
            # select columns to import
            #
            admin = model_context.admin
            default_fields = [field for field, fa in admin.get_columns() 
                              if fa.get('editable', True)]
            mappings = []
            all_fields = [(f,six.text_type(entity_fa['name'])) for f,entity_fa in 
                         six.iteritems(admin.get_all_fields_and_attributes())
                          if entity_fa.get('editable', True)]
            all_fields.sort(key=lambda field_tuple:field_tuple[1])
            for i, default_field in six.moves.zip_longest(six.moves.range(len(all_fields)),
                                                          default_fields):
                mappings.append(ColumnMapping(i, items, default_field))
            
    
            column_mapping_admin = ColumnMappingAdmin(admin,
                                                      field_choices=all_fields)
    
            change_mappings = action_steps.ChangeObjects(mappings, 
                                                         column_mapping_admin)
            change_mappings.title = _('Select import column')
            change_mappings.subtitle = _('Select for each column in which field it should be imported')
            yield change_mappings
            #
            # validate the temporary data
            #
            row_data_admin = RowDataAdmin(admin, mappings)
            yield action_steps.ChangeObjects( collection, row_data_admin )
            #
            # Ask confirmation
            #
            yield action_steps.MessageBox( icon = QtGui.QMessageBox.Warning, 
                                           title = _('Proceed with import'), 
                                           text = _('Importing data cannot be undone,\n'
                                                    'are you sure you want to continue') )
            #
            # import the temporary objects into real objects
            #
            with model_context.session.begin():
                for i,row in enumerate( collection ):
                    new_entity_instance = admin.entity()
                    for field_name, attributes in row_data_admin.get_columns():
                        try:
                            from_string = attributes['from_string']
                        except KeyError:
                            LOGGER.warn( 'field %s has no from_string field attribute, dont know how to import it properly'%attributes['original_field'] )
                            from_string = lambda _a:None
                        setattr(
                            new_entity_instance,
                            attributes['original_field'],
                            from_string(getattr(row, field_name))
                        )
                    admin.add( new_entity_instance )
                    # in case the model is a collection proxy, the new objects should
                    # be appended
                    model_context._model.append( new_entity_instance )
                    yield action_steps.UpdateProgress( i, len( collection ), _('Importing data') )
                yield action_steps.FlushSession( model_context.session )
            yield action_steps.Refresh()
        

class ReplaceFieldContents( EditAction ):
    """Select a field an change the content for a whole selection"""
    
    verbose_name = _('Replace field contents')
    tooltip = _('Replace the content of a field for all rows in a selection')
    icon = Icon('tango/16x16/actions/edit-find-replace.png')
    message = _('Field is not editable')
    resolution = _('Only select editable rows')

    def model_run( self, model_context ):
        from camelot.view import action_steps
        field_name, value_getter = yield action_steps.ChangeField( model_context.admin )
        yield action_steps.UpdateProgress( text = _('Replacing field') )
        dynamic_field_attributes = model_context.admin.get_dynamic_field_attributes
        if value_getter != None:
            value = value_getter()
            with model_context.session.begin():
                for obj in model_context.get_selection():
                    dynamic_fa = list(dynamic_field_attributes(obj, [field_name]))[0]
                    if dynamic_fa.get('editable', True) == False:
                        raise UserException(self.message, resolution=self.resolution)
                    setattr( obj, field_name, value )
                    # dont rely on the session to update the gui, since the objects
                    # might not be in a session
                    yield action_steps.UpdateObject(obj)
                yield action_steps.FlushSession( model_context.session )
        
class AddExistingObject( EditAction ):
    """Add an existing object to a list if it is not yet in the
    list"""
    
    tooltip = _('Add')
    verbose_name = _('Add')
    icon = Icon( 'tango/16x16/actions/list-add.png' )
    
    def model_run( self, model_context ):
        from sqlalchemy.orm import object_session
        from camelot.view import action_steps
        objs_to_add = yield action_steps.SelectObjects( model_context.admin )
        for obj_to_add in objs_to_add:
            for obj in model_context.get_collection():
                if obj_to_add == obj:
                    raise StopIteration()
            model_context._model.append_object( obj_to_add )
        yield action_steps.FlushSession( object_session( obj_to_add ) )
        
class AddNewObject( EditAction ):
    """Add a new object to a collection. Depending on the
    'create_inline' field attribute, a new form is opened or not.
    
    This action will also set the default values of the new object, add the
    object to the session, and flush the object if it is valid.
    """

    shortcut = QtGui.QKeySequence.New
    icon = Icon('tango/16x16/actions/document-new.png')
    tooltip = _('New')
    verbose_name = _('New')

    def model_run( self, model_context ):
        from camelot.view import action_steps
        admin = yield action_steps.SelectSubclass(model_context.admin)
        create_inline = model_context.field_attributes.get('create_inline',
                                                           False)
        new_object = admin.entity()
        admin.add(new_object)
        # defaults might depend on object being part of a collection
        model_context._model.append_object(new_object)
        # Give the default fields their value
        admin.set_defaults(new_object)
        # if the object is valid, flush it
        if not len(admin.get_validator().validate_object(new_object)):
            yield action_steps.FlushSession(model_context.session)
        # Even if the object was not flushed, it's now part of a collection,
        # so it's dependent objects should be updated
        for depending_obj in admin.get_depending_objects( new_object ):
            yield action_steps.UpdateObject(depending_obj)
        if create_inline is False:
            yield action_steps.OpenFormView([new_object], admin)

class RemoveSelection( DeleteSelection ):
    """Remove the selected objects from a list without deleting them"""
    
    shortcut = None
    tooltip = _('Remove')
    verbose_name = _('Remove')
    icon = Icon( 'tango/16x16/actions/list-remove.png' )
            
    def handle_object( self, model_context, obj ):
        model_context._model.remove( obj )
        # no StopIteration, since the supergenerator needs to
        # continue to flush the session
        yield None

