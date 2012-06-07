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

import copy
import datetime
import logging

from camelot.admin.action.base import Action
from application_action import ( ApplicationActionGuiContext,
                                 ApplicationActionModelContext )
from camelot.core.utils import ugettext, ugettext_lazy as _
from camelot.view.art import Icon

from PyQt4 import QtGui

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
        if self.selection_count == self.collection_count:
            # if all rows are selected, take a shortcut
            for obj in self.get_collection( yield_per ):
                yield obj
        else:
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
        if self.current_row != None:
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

    def create_model_context( self ):
        context = super( ListActionGuiContext, self ).create_model_context()
        context.field_attributes = copy.copy( self.field_attributes )
        current_row = None
        model = None
        collection_count = 0
        selection_count = 0
        selected_rows = []
        if self.item_view != None:
            current_row = self.item_view.currentIndex().row()
            model = self.item_view.model()
            if model != None:
                collection_count = model.rowCount()
            if self.item_view.selectionModel() != None:
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
    verbose_name = _('Open')
    
    def gui_run( self, gui_context ):
        from camelot.view.workspace import show_top_level
        from camelot.view.proxy.queryproxy import QueryTableProxy
        from camelot.view.proxy.collection_proxy import CollectionProxy
        related_model = gui_context.item_view.model()
        #
        # depending on the type of related model, create a new model
        #
        row = gui_context.item_view.currentIndex().row()
        if isinstance( related_model, QueryTableProxy ):
            model = QueryTableProxy(
                gui_context.admin,
                related_model.get_query_getter(),
                gui_context.admin.get_fields,
                max_number_of_rows = 1,
                cache_collection_proxy = related_model,
            ) 
        else:
            # no cache or sorting information is transferred
            model = CollectionProxy( 
                gui_context.admin,
                related_model.get_collection,
                gui_context.admin.get_fields,
                max_number_of_rows = 1,
            )
            # get the unsorted row
            row = related_model.map_to_source( row )
        formview = gui_context.admin.create_form_view(
            u' ', 
            model, 
            row, 
        )
        # make sure there is no 'pythonw' window title in windows for a
        # second
        formview.setWindowTitle( u' ' )
        show_top_level( formview, gui_context.item_view )
        
class OpenNewView( EditAction ):
    """Opens a new view of an Entity related to a table view.
    """
    
    shortcut = QtGui.QKeySequence.New
    icon = Icon('tango/16x16/actions/document-new.png')
    tooltip = _('New')
    verbose_name = _('New')
    
    def gui_run( self, gui_context ):
        from camelot.view.workspace import show_top_level
        admin = gui_context.admin
        model = gui_context.item_view.model()
        form = admin.create_new_view( related_collection_proxy=model,
                                      parent = None )
        show_top_level( form, gui_context.item_view )
    
class DuplicateSelection( EditAction ):
    """Duplicate the selected rows in a table"""
    
    shortcut = QtGui.QKeySequence.Copy
    icon = Icon('tango/16x16/actions/edit-copy.png')
    tooltip = _('Duplicate')
    verbose_name = _('Duplicate')
    
    def gui_run( self, gui_context ):
        model = gui_context.item_view.model()
        for row in set( map( lambda x: x.row(), gui_context.item_view.selectedIndexes() ) ):
            model.copy_row( row )

class DeleteSelection( EditAction ):
    """Delete the selected rows in a table"""
    
    shortcut = QtGui.QKeySequence.Delete
    icon = Icon('tango/16x16/places/user-trash.png')
    tooltip = _('Delete')
    verbose_name = _('Delete')
    
    def gui_run( self, gui_context):
        gui_context.item_view.delete_selected_rows()

class ToPreviousRow( ListContextAction ):
    """Move to the previous row in a table"""
    
    shortcut = QtGui.QKeySequence.MoveToPreviousPage
    icon = Icon('tango/16x16/actions/go-previous.png')
    tooltip = _('Previous')
    verbose_name = _('Previous')

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
    
class ToFirstRow( ToPreviousRow ):
    """Move to the first row in a table"""
    
    shortcut = QtGui.QKeySequence.MoveToStartOfDocument
    icon = Icon('tango/16x16/actions/go-first.png')
    tooltip = _('First')
    verbose_name = _('First')
    
    def gui_run( self, gui_context ):
        gui_context.item_view.selectRow( 0 )

class ToNextRow( ListContextAction ):
    """Move to the next row in a table"""
    
    shortcut = QtGui.QKeySequence.MoveToNextPage
    icon = Icon('tango/16x16/actions/go-next.png')
    tooltip = _('Next')
    verbose_name = _('Next')

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
    
class ToLastRow( ToNextRow ):
    """Move to the last row in a table"""
    
    shortcut = QtGui.QKeySequence.MoveToEndOfDocument
    icon = Icon('tango/16x16/actions/go-last.png')
    tooltip = _('Last')
    verbose_name = _('Last')

    def gui_run( self, gui_context ):
        item_view = gui_context.item_view
        item_view.selectRow( item_view.model().rowCount() - 1 )

class ExportSpreadsheet( ListContextAction ):
    """Export all rows in a table to a spreadsheet"""
    
    icon = Icon('tango/16x16/mimetypes/x-office-spreadsheet.png')
    tooltip = _('Export to MS Excel')
    verbose_name = _('Export to MS Excel')
    font_name = 'Arial'
    
    def model_run( self, model_context ):
        from decimal import Decimal
        from xlwt import Font, Borders, XFStyle, Pattern, Workbook
        from camelot.view.utils import ( local_date_format, 
                                         local_datetime_format,
                                         local_time_format )
        from camelot.view import action_steps
        #
        # setup worksheet
        #
        yield action_steps.UpdateProgress( text = _('Create worksheet') )
        admin = model_context.admin
        workbook = Workbook()
        worksheet = workbook.add_sheet('Sheet1')
        #
        # keep a global cache of styles, since the number of styles that
        # can be used is limited.
        #
        styles = dict()
        freeze = lambda d:tuple(sorted(d.iteritems()))
        
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
                for key, value in font_specs.items():
                    setattr( style.font, key, value )
                style.borders = Borders()
                for key, value in border_specs.items():
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
        columns = admin.get_columns()
        field_names = []
        for i, (name, field_attributes) in enumerate( columns ):
            verbose_name = unicode( field_attributes.get( 'name', name ) )
            field_names.append( name )
            font_specs = dict( font_name = self.font_name, 
                               bold = True, 
                               height = 200 )
            border_specs = dict( top = 0x01 )
            name = unicode( name )
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
        for j, obj in enumerate( model_context.get_collection( yield_per = 100 ) ):
            dynamic_attributes = admin.get_dynamic_field_attributes( obj, 
                                                                     field_names )
            row = offset + j
            if j % 100 == 0:
                yield action_steps.UpdateProgress( j, model_context.collection_count )
            for i, ((_name, attributes), delta_attributes)  in enumerate( zip( columns, dynamic_attributes ) ):
                attributes.update( delta_attributes )
                value = attributes['getter']( obj )
                format_string = '0'
                if value != None:
                    if isinstance( value, Decimal ):
                        value = float( str( value ) )
                    if isinstance( value, (unicode, str) ):
                        if attributes.get( 'translate_content', False ) == True:
                            value = ugettext( value )
                    # handle fields of type code
                    elif isinstance( value, list ):
                        value = u'.'.join(value)
                    elif isinstance( value, float ):
                        precision = attributes.get( 'precision', 2 )
                        format_string = '0.' + '0'*precision
                    elif isinstance( value, datetime.date ):
                        format_string = date_format
                    elif isinstance( value, datetime.datetime ):
                        format_string = datetime_format
                    elif isinstance( value, datetime.time ):
                        format_string = time_format
                    else:
                        value = unicode( value )
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
                min_width = len( unicode( value ) ) * 300
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
        getters = [field_attributes['getter'] for _field, field_attributes in columns]
        to_strings = [field_attributes['to_string'] for _field, field_attributes in columns]
        column_range = range( len( columns ) )
        for obj in model_context.get_collection():
            table.append( [to_strings[i]( getters[i]( obj ) ) for i in column_range] )
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
                                                RowDataAdminDecorator,
                                                XlsReader )
        file_names = yield action_steps.SelectFile()
        if not len( file_names ):
            return
        file_name = file_names[0]
        yield action_steps.UpdateProgress( text = _('Reading data') )
        #
        # read the data into temporary row_data objects
        #
        if os.path.splitext( file_name )[-1] == '.xls':
            items = XlsReader( file_name )
        else:
            detected = chardet.detect( open( file_name ).read() )['encoding']
            enc = detected or 'utf-8'
            items = UnicodeReader( open( file_name ), encoding = enc )
        collection = [ RowData(i, row_data) for i, row_data in enumerate( items ) ]
        #
        # validate the temporary data
        #
        admin = model_context.admin
        row_data_admin = RowDataAdminDecorator( admin )
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

    def model_run( self, model_context ):
        from camelot.view import action_steps
        field_name, value_getter = yield action_steps.ChangeField( model_context.admin )
        yield action_steps.UpdateProgress( text = _('Replacing field') )
        value = value_getter()
        for obj in model_context.get_selection():
            setattr( obj, field_name, value )
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
        obj_getter = yield action_steps.SelectObject( model_context.admin )
        obj_to_add = obj_getter()
        for obj in model_context.get_collection():
            if obj_to_add == obj:
                raise StopIteration()
        model_context._model.append_object( obj_to_add )
        yield action_steps.FlushSession( object_session( obj_to_add ) )
        
class AddNewObject( OpenNewView ):
    """Add a new object to a collection. Depending on the
    'create_inline' field attribute, a new form is opened or not"""
    
    def gui_run( self, gui_context ):
        create_inline = gui_context.field_attributes.get( 'create_inline',
                                                          False )                                                            
        if create_inline == True:
            super( OpenNewView, self ).gui_run( gui_context )
        else:
            super( AddNewObject, self ).gui_run( gui_context )
        
    def model_run( self, model_context ):
        admin = model_context.admin
        model_context._model.append_object( admin.entity() )
    
class RemoveSelection( EditAction ):
    """Remove the selected objects from a list without deleting them"""
    
    tooltip = _('Remove')
    verbose_name = _('Remove')
    icon = Icon( 'tango/16x16/actions/list-remove.png' )

    def model_run( self, model_context ):
        from sqlalchemy.orm import object_session
        from camelot.view import action_steps
        objects_to_remove = list( model_context.get_selection() )
        if len( objects_to_remove ):
            session = object_session( objects_to_remove[0] )
        model_context._model.remove_objects( objects_to_remove, delete = False )
        yield action_steps.FlushSession( session )

