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

import codecs
import copy
import datetime
import logging

import six

from ...core.item_model.proxy import AbstractModelFilter
from ...core.qt import Qt, QtGui, QtWidgets, variant_to_py, py_to_variant
from .base import Action, Mode
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
    
        the current row in the list if a cell is active
    
    .. attribute:: current_column
    
        the current column in the table if a cell is active
    
    .. attribute:: current_field_name
    
        the name of the field displayed in the current column
        
    .. attribute:: session
    
        The session to which the objects in the list belong.

    .. attribute:: proxy

        A :class:`camelot.core.item_model.AbstractModelProxy` object that gives
        access to the objects in the list

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
        self.proxy = None
        self.admin = None
        self.current_row = None
        self.current_column = None
        self.current_field_name = None
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
            for obj in self.proxy[first_row:last_row + 1]:
                yield obj

    def get_collection( self, yield_per = None ):
        """
        :param yield_per: an integer number giving a hint on how many objects
            should fetched from the database at the same time.
        :return: a generator over the objects in the list
        """
        for obj in self.proxy[0:self.collection_count]:
            yield obj
            
    def get_object( self ):
        """
        :return: the object displayed in the current row or None
        """
        if self.current_row != None:
            for obj in self.proxy[self.current_row:self.current_row+1]:
                return obj
        
class ListActionGuiContext( ApplicationActionGuiContext ):
    """The context for an :class:`Action` on a table view.  On top of the attributes of the 
    :class:`camelot.admin.action.application_action.ApplicationActionGuiContext`, 
    this context contains :

    .. attribute:: item_view
    
       the :class:`QtWidgets.QAbstractItemView` class that relates to the table 
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
        current_row, current_column, current_field_name = None, None, None
        model = None
        collection_count = 0
        selection_count = 0
        selected_rows = []
        if self.item_view is not None:
            current_index = self.item_view.currentIndex()
            if current_index.isValid():
                current_row = current_index.row()
                current_column = current_index.column()
            model = self.item_view.model()
            if model is not None:
                collection_count = model.rowCount()
                if current_column is not None:
                    current_field_name = variant_to_py(
                        model.headerData(
                            current_column, Qt.Horizontal, Qt.UserRole
                        )
                    )
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
        context.current_column = current_column
        context.current_field_name = current_field_name
        context.proxy = model.get_value()
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
                                                UpdateObjects )
        step = max( 1, model_context.selection_count / 100 )
        for i, obj in enumerate( model_context.get_selection() ):
            if i%step == 0:
                yield UpdateProgress( i, model_context.selection_count )
            self.method( obj )
            # the object might have changed without the need to be flushed
            # to the database
            yield UpdateObjects((obj,))
        yield FlushSession(model_context.session)
        
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
        state.verbose_name = six.text_type(model_context.current_row + 1)
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

    def get_state( self, model_context ):
        state = Action.get_state(self, model_context)
        state.verbose_name = six.text_type(model_context.current_row + 1)
        return state

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
    
    # no shortcut here, as this is too dangerous if the user
    # presses the shortcut without being aware of the consequences
    icon = Icon('tango/16x16/actions/edit-copy.png')
    tooltip = _('Duplicate')
    verbose_name = _('Duplicate')
    
    def model_run( self, model_context ):
        from camelot.view import action_steps
        admin = model_context.admin
        new_objects = list()
        updated_objects = set()
        for i, obj in enumerate(model_context.get_selection()):
            yield action_steps.UpdateProgress(i, 
                                              model_context.selection_count,
                                              self.verbose_name )
            new_object = admin.copy(obj)
            model_context.proxy.append(new_object)
            new_objects.append(new_object)
            updated_objects.update(set(admin.get_depending_objects(new_object)))
        yield action_steps.CreateObjects(new_objects)
        yield action_steps.UpdateObjects(updated_objects)
        yield action_steps.FlushSession(model_context.session)
            
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
        yield action_steps.UpdateObjects(depending_objects)
        yield action_steps.FlushSession( model_context.session )
        
    def handle_object( self, model_context, obj ):
        from camelot.view import action_steps
        model_context.proxy.remove(obj)
        yield action_steps.DeleteObjects((obj,))
        model_context.admin.delete(obj)

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
        self.settings.sync()
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
        self.settings.sync()

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
        if mapping_name is not None:
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
            yield action_steps.UpdateObjects(model_context.get_collection())

class RemoveExportMapping( SaveExportMapping ):
    """
    Remove a user defined order of columns to export
    """

    verbose_name = _('Remove')
    tooltip = _('Remove the previously stored order of the columns')

    def model_run(self, model_context):
        from camelot.view import action_steps
    
        mappings = self.read_mappings()
        mapping_names = [(k,k) for k in six.iterkeys(mappings)]
        mapping_name = yield action_steps.SelectItem(mapping_names)
        if mapping_name is not None:
            mappings.pop(mapping_name)
            self.write_mappings(mappings)


class ClearMapping(Action):
    """
    Clear a selection of mappings
    """

    verbose_name = _('Clear')

    def model_run(self, model_context):
        from camelot.view import action_steps

        cleared_mappings = list()
        for mapping in model_context.get_selection():
            if mapping.field is not None:
                mapping.field = None
                cleared_mappings.append(mapping)
        yield action_steps.UpdateObjects(cleared_mappings)


class ExportSpreadsheet( ListContextAction ):
    """Export all rows in a table to a spreadsheet"""
    
    icon = Icon('tango/16x16/mimetypes/x-office-spreadsheet.png')
    tooltip = _('Export to MS Excel')
    verbose_name = _('Export to MS Excel')

    # xlwt options
    max_width = 10000
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
                                                 RestoreExportMapping(settings),
                                                 RemoveExportMapping(settings),
                                                 ClearMapping(),
                                                 ]
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
                worksheet.col( i ).width = min(self.max_width, max(
                    min_width,
                    worksheet.col( i ).width)
                )

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
            # 
            # it should be possible to select not editable fields, to be able to
            # import foreign keys, these are not editable by default, it might
            # be better to explicitly allow foreign keys, but this info is not
            # in the field attributes
            #
            all_fields = [(f,six.text_type(entity_fa['name'])) for f,entity_fa in 
                         six.iteritems(admin.get_all_fields_and_attributes()) if entity_fa.get('from_string')]
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
            yield action_steps.MessageBox( icon = QtWidgets.QMessageBox.Warning, 
                                           title = _('Proceed with import'), 
                                           text = _('Importing data cannot be undone,\n'
                                                    'are you sure you want to continue') )
            #
            # import the temporary objects into real objects
            #
            with model_context.session.begin():
                for i,row in enumerate(collection):
                    new_entity_instance = admin.entity()
                    for field_name, attributes in row_data_admin.get_columns():
                        from_string = attributes['from_string']
                        setattr(
                            new_entity_instance,
                            attributes['original_field'],
                            from_string(getattr(row, field_name))
                        )
                    admin.add( new_entity_instance )
                    # in case the model is a collection proxy, the new objects should
                    # be appended
                    model_context.proxy.append(new_entity_instance)
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
    shortcut = QtGui.QKeySequence.Replace

    def gui_run( self, gui_context ):
        #
        # if there is an open editor on a row that will be deleted, there
        # might be an assertion failure in QT, or the data of the editor 
        # might be pushed to the changed row
        #
        gui_context.item_view.close_editor()
        super(ReplaceFieldContents, self ).gui_run(gui_context)

    def model_run( self, model_context ):
        from camelot.view import action_steps
        field_name, value = yield action_steps.ChangeField(
            model_context.admin,
            field_name = model_context.current_field_name
        )
        yield action_steps.UpdateProgress( text = _('Replacing field') )
        dynamic_field_attributes = model_context.admin.get_dynamic_field_attributes
        with model_context.session.begin():
            for obj in model_context.get_selection():
                dynamic_fa = list(dynamic_field_attributes(obj, [field_name]))[0]
                if dynamic_fa.get('editable', True) == False:
                    raise UserException(self.message, resolution=self.resolution)
                setattr( obj, field_name, value )
                # dont rely on the session to update the gui, since the objects
                # might not be in a session
            yield action_steps.UpdateObjects(model_context.get_selection())
            yield action_steps.FlushSession(model_context.session)

class SetFilters(Action, AbstractModelFilter):
    """
    Apply a set of filters on a list.
    This action differs from those in `list_filter` in the sense that it will
    pop up a dialog to configure a complete filter and wont allow the user
    to apply filters from within its widget.
    """

    verbose_name = _('Find')
    tooltip = _('Filter the data')
    icon = Icon('tango/16x16/actions/system-search.png')

    def filter(self, it, value):
        if value is None:
            for obj in it:
                yield obj
        else:
            field_name, field_value = value
            for obj in it:
                if getattr(obj, value[0]) == value[1]:
                    yield obj

    def model_run( self, model_context ):
        from camelot.view import action_steps

        if model_context.mode_name == 'clear':
            yield action_steps.SetFilter(self, None)

        else:
            current_field_name = model_context.current_field_name
            current_field_value  = None
            current_obj = model_context.get_object()
            if (current_field_name is not None) and (current_obj is not None):
                current_field_value = getattr(current_obj, current_field_name)

            select_field = action_steps.ChangeField(
                model_context.admin,
                # explicit pass of field attributes because not editable
                # fields should appear in the selection box
                field_attributes = model_context.admin.get_all_fields_and_attributes(),
                field_name = model_context.current_field_name,
                field_value = current_field_value
            )
            select_field.title = _('Filter')
            select_field.subtitle = _('Select field and value')

            field_name, value = yield select_field
            if field_name is None:
                yield action_steps.SetFilter(self, None)
            yield action_steps.SetFilter(self, (field_name, value))

    def get_state(self, model_context):
        state = super(SetFilters, self).get_state(model_context)
        state.modes = [
            Mode('filter', _('Apply filter')),
            Mode('clear', _('Clear filter')),
        ]
        return state

class AddExistingObject( EditAction ):
    """Add an existing object to a list if it is not yet in the
    list"""
    
    tooltip = _('Add')
    verbose_name = _('Add')
    icon = Icon( 'tango/16x16/actions/list-add.png' )
    
    def model_run( self, model_context ):
        from sqlalchemy.orm import object_session
        from camelot.view import action_steps
        objs_to_add = yield action_steps.SelectObjects(model_context.admin)
        for obj_to_add in objs_to_add:
            for obj in model_context.get_collection():
                if obj_to_add == obj:
                    raise StopIteration()
            model_context.proxy.append(obj_to_add)
        yield action_steps.UpdateObjects(objs_to_add)
        yield action_steps.FlushSession(object_session(obj_to_add))
        
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
        model_context.proxy.append(new_object)
        # Give the default fields their value
        admin.set_defaults(new_object)
        # if the object is valid, flush it, but in ancy case inform the gui
        # the object has been created
        yield action_steps.CreateObjects((new_object,))
        if not len(admin.get_validator().validate_object(new_object)):
            yield action_steps.FlushSession(model_context.session)
        # Even if the object was not flushed, it's now part of a collection,
        # so it's dependent objects should be updated
        yield action_steps.UpdateObjects(
            tuple(admin.get_depending_objects(new_object))
        )
        if create_inline is False:
            yield action_steps.OpenFormView([new_object], admin)

class RemoveSelection(DeleteSelection):
    """Remove the selected objects from a list without deleting them"""
    
    shortcut = None
    tooltip = _('Remove')
    verbose_name = _('Remove')
    icon = Icon( 'tango/16x16/actions/list-remove.png' )
            
    def handle_object( self, model_context, obj ):
        model_context.proxy.remove( obj )
        # no StopIteration, since the supergenerator needs to
        # continue to flush the session
        yield None


