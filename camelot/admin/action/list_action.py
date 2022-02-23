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
import enum
import logging
import itertools

from sqlalchemy import orm

from ...core.item_model.proxy import AbstractModelFilter
from ...core.qt import Qt, QtGui, QtWidgets, variant_to_py, is_deleted
from .base import Action, Mode, GuiContext, RenderHint
from .application_action import ( ApplicationActionGuiContext,
                                 ApplicationActionModelContext )
from camelot.core.exception import UserException
from camelot.core.utils import ugettext, ugettext_lazy as _
from camelot.admin.icon import Icon
from camelot.view.qml_view import qml_action_step, qml_action_dispatch

import xlsxwriter

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

    def get_progress_dialog(self):
        return GuiContext.get_progress_dialog(self)

    def get_window(self):
        if self.item_view is not None and not is_deleted(self.item_view):
            return self.item_view.window()
        return super(ListActionGuiContext, self).get_window()

    def create_model_context( self ):
        context = super( ListActionGuiContext, self ).create_model_context()
        context.field_attributes = copy.copy( self.field_attributes )
        current_row, current_column, current_field_name = None, None, None
        proxy = None
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
                proxy = model.get_value()
                collection_count = model.rowCount()
                if current_column is not None:
                    current_field_name = variant_to_py(
                        model.headerData(
                            current_column, Qt.Orientation.Horizontal, Qt.ItemDataRole.UserRole
                        )
                    )
            if self.item_view.selectionModel() is not None:
                selection = self.item_view.selectionModel().selection()
                for i in range( len( selection ) ):
                    selection_range = selection[i]
                    rows_range = ( selection_range.top(), selection_range.bottom() )
                    selected_rows.append( rows_range )
                    selection_count += ( rows_range[1] - rows_range[0] ) + 1
        else:
            model = qml_action_dispatch.get_model(self.context_id)
            if model is not None:
                collection_count = model.rowCount()
                proxy = model.get_value()
            response = qml_action_step(self, 'GetSelection', keep_context_id=True)
            selection_count = response['selection_count']
            current_row = response['current_row']
            for i in range(len(response['selected_rows']) // 2):
                selected_rows.append((response['selected_rows'][2 * i], response['selected_rows'][2 * i + 1]))
        context.selection_count = selection_count
        context.collection_count = collection_count
        context.selected_rows = selected_rows
        context.current_row = current_row
        context.current_column = current_column
        context.current_field_name = current_field_name
        context.proxy = proxy
        return context
        
    def copy( self, base_class = None ):
        new_context = super( ListActionGuiContext, self ).copy( base_class )
        new_context.item_view = self.item_view
        new_context.view = self.view
        new_context.field_attributes = self.field_attributes
        return new_context

class ListContextAction( Action ):
    """An base class for actions that should only be enabled if the
    gui_context is a :class:`ListActionModelContext`
    """

    name = 'list_context_action'
    
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

    name = 'row_number'

    def get_state( self, model_context ):
        state = super(RowNumberAction, self).get_state(model_context)
        state.verbose_name = str(model_context.current_row + 1)
        return state

row_number_action = RowNumberAction()

class EditAction( ListContextAction ):
    """A base class for an action that will modify the model, it will be
    disabled when the field_attributes for the relation field are set to 
    not-editable. It will also be disabled and hidden if the entity is set
    to be non-editable using __entity_args__ = { 'editable': False }.
    """

    name = 'edit_action'
    render_hint = RenderHint.TOOL_BUTTON

    class Message(enum.Enum):

        no_single_selection = _('Can only select 1 line')
        select_2_lines = _('Please select 2 lines')
        entity_not_rank_based = '{} has no rank column registered'
        incompatible_rank_dimension = _('The selected lines are not part of the same rank dimension')

    def get_state( self, model_context ):
        state = super( EditAction, self ).get_state( model_context )
        # Check for editability on the level of the field
        if isinstance( model_context, ListActionModelContext ):
            editable = model_context.field_attributes.get( 'editable', True )
            if editable == False:
                state.enabled = False
        # Check for editability on the level of the entity
        admin = model_context.admin
        if admin and not admin.is_editable():
            state.visible = False
            state.enabled = False
        return state

    def model_run( self, model_context, mode ):
        admin = model_context.admin
        if not admin.is_editable():
            raise RuntimeError("Action's model_run() called on noneditable entity")

class CloseList(Action):
    """
    Close the currently open table view
    """

    render_hint = RenderHint.TOOL_BUTTON

    icon = Icon('backspace')
    tooltip = _('Close')
    name = 'close'
    shortcut = QtGui.QKeySequence.StandardKey.Close

    def model_run(self, model_context, mode):
        from camelot.view import action_steps
        yield action_steps.CloseView()

close_list = CloseList()

class ListLabel(Action):
    """
    A simple action that displays the name of the table
    """

    render_hint = RenderHint.LABEL
    name = 'label'

    def get_state(self, model_context):
        state = super().get_state(model_context)
        state.verbose_name = str(model_context.admin.get_verbose_name_plural())
        return state

list_label = ListLabel()

class OpenFormView( ListContextAction ):
    """Open a form view for the current row of a list."""
    
    shortcut = QtGui.QKeySequence.StandardKey.Open
    icon = Icon('folder') # 'tango/16x16/places/folder.png'
    tooltip = _('Open')
    # verbose name is set to None to avoid displaying it in the vertical
    # header of the table view
    verbose_name = None
    name = 'open_form_view'

    def model_run(self, model_context, mode):
        from camelot.view import action_steps
        yield action_steps.OpenFormView(model_context.get_object(), model_context.proxy, admin=model_context.admin)

    def get_state( self, model_context ):
        state = Action.get_state(self, model_context)
        state.verbose_name = str()
        return state

open_form_view = OpenFormView()

class DuplicateSelection( EditAction ):
    """Duplicate the selected rows in a table"""
    
    # no shortcut here, as this is too dangerous if the user
    # presses the shortcut without being aware of the consequences
    icon = Icon('copy') # 'tango/16x16/actions/edit-copy.png'
    #icon = Icon('clone') # 'tango/16x16/actions/edit-copy.png'
    tooltip = _('Duplicate')
    verbose_name = _('Duplicate')
    name = 'duplicate_selection'

    def model_run( self, model_context, mode ):
        from camelot.view import action_steps
        super().model_run(model_context, mode)
        admin = model_context.admin
        if model_context.selection_count > 1:
            raise UserException(self.Message.no_single_selection.value)
        for obj in model_context.get_selection():
            new_object = admin.copy(obj)
            model_context.proxy.append(new_object)
            yield action_steps.CreateObjects([new_object])
            if not len(admin.get_validator().validate_object(new_object)):
                updated_objects = set(admin.get_depending_objects(new_object))
                yield action_steps.UpdateObjects(updated_objects)
                yield action_steps.FlushSession(model_context.session)
            else:
                yield action_steps.OpenFormView(new_object, admin.get_proxy([new_object]), admin)

    def get_state(self, model_context):
        assert isinstance(model_context, ListActionModelContext)
        state = super().get_state(model_context)
        if model_context.selection_count <= 0:
            state.enabled = False
        return state

duplicate_selection = DuplicateSelection()


class DeleteSelection( EditAction ):
    """Delete the selected rows in a table"""
    
    shortcut = QtGui.QKeySequence.StandardKey.Delete
    name = 'delete_selection'
    icon = Icon('trash') # 'tango/16x16/places/user-trash.png'
    tooltip = _('Delete')
    verbose_name = _('Delete')

    def gui_run( self, gui_context ):
        if gui_context.item_view is not None:
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
        else:
            super().gui_run(gui_context)
            model = qml_action_dispatch.get_model(gui_context.context_id)
            if model is not None:
                model.refresh() # this will also clear the selection

    def model_run( self, model_context, mode ):
        from camelot.view import action_steps
        super().model_run(model_context, mode)
        admin = model_context.admin
        if model_context.selection_count <= 0:
            return
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

    def get_state(self, model_context):
        assert isinstance(model_context, ListActionModelContext)
        state = super().get_state(model_context)
        if model_context.selection_count <= 0:
            state.enabled = False
        return state

delete_selection = DeleteSelection()

class MoveRankUp(EditAction):
    """
    Switch the rank of the selected rank-based row in a table with that of the row that is ranked directly higher within the same rank dimension.
    Note that ranking higher in this context refers to a rank value that is lower in numerical value.
    """

    icon = Icon('arrow-up')
    tooltip = _('Move rank up')
    verbose_name = _('Move rank up')
    name = 'move_rank_up'

    def get_obj_to_switch(self, obj_rank, objects):
        """
        Based on the given selected object's rank, return the suited rank-object tuple candidate to switch with out of the given list of objects within the same rank dimension.
        For this rank-up action, this is defined as the object with the lowest rank that is ranked higher as the selected object.
        Note that ranking higher in this context refers to a rank value that is lower in numerical value, and vice versa.
        :obj_rank: The rank of the selected object.
        :objects: list of rank-object tuples within the same rank dimension as the selected object.
        """
        return max([(rank, obj) for (rank, obj) in objects if rank < obj_rank] or [(None, None)])

    def model_run( self, model_context, mode ):
        from camelot.view import action_steps
        super().model_run(model_context, mode)
        admin = model_context.admin
        ranked_by = admin.entity.get_ranked_by()
        assert ranked_by is not None, self.Message.entity_not_rank_based.value.format(admin.entity)
        rank_prop = ranked_by[0] if isinstance(ranked_by, tuple) else ranked_by
        if model_context.selection_count != 1:
            raise UserException(self.Message.no_single_selection.value)
        for obj in model_context.get_selection():
            obj_rank = rank_prop.__get__(obj, None)
            # Compose a list of rank-object tuples of objects within the same rank dimension.
            compatible_objects = []
            for other_obj in model_context.get_collection():
                for rank_col in ranked_by[1:]:
                    if rank_col.__get__(obj, None) != rank_col.__get__(other_obj, None):
                        break
                else:
                    compatible_objects.append((rank_prop.__get__(other_obj, None), other_obj))

            # Determine the object to switch it and perform the switch if there's a switch candidate found.
            obj_to_switch_rank, obj_to_switch = self.get_obj_to_switch(obj_rank, compatible_objects)
            if obj_to_switch is not None:
                rank_prop.__set__(obj, obj_to_switch_rank)
                rank_prop.__set__(obj_to_switch, obj_rank)
                updated_objects = set(list(admin.get_depending_objects(obj)) + list(admin.get_depending_objects(obj_to_switch)))
                yield action_steps.UpdateObjects(updated_objects)
                yield action_steps.FlushSession(model_context.session)
                for updated_obj in updated_objects:
                    model_context.session.refresh(updated_obj)

    def get_state(self, model_context):
        assert isinstance(model_context, ListActionModelContext)
        state = super().get_state(model_context)
        state.enabled = model_context.selection_count == 1
        return state

move_rank_up = MoveRankUp()

class MoveRankDown(MoveRankUp):
    """
    Switch the rank of the selected rank-based row in a table with that of the row that is ranked directly lower within the same rank dimension.
    Note that ranking lower in this context refers to a rank value that is higher in numerical value.
    """

    icon = Icon('arrow-down')
    tooltip = _('Move rank down')
    verbose_name = _('Move rank down')
    name = 'move_rank_down'

    def get_obj_to_switch(self, obj_rank, objects):
        """
        For this rank-down action, the object to switch with is defined as the object with the highest rank that is ranked lower as the selected object.
        Note that ranking lower in this context refers to a rank value that is higher in numerical value, and vice versa.
        """
        return min([(rank, obj) for (rank, obj) in objects if rank > obj_rank] or [(None, None)])

move_rank_down = MoveRankDown()

class AbstractToPrevious(object):

    render_hint = RenderHint.TOOL_BUTTON
    shortcut = QtGui.QKeySequence.StandardKey.MoveToPreviousPage
    icon = Icon('step-backward') # 'tango/16x16/actions/go-previous.png'
    tooltip = _('Previous')
    verbose_name = _('Previous')
    
class ToPreviousRow( AbstractToPrevious, ListContextAction ):
    """Move to the previous row in a table"""

    name = 'to_previous'

    def gui_run( self, gui_context ):
        if gui_context.item_view is not None:
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
        else:
            qml_action_step(gui_context, 'ToPreviousRow', keep_context_id=True)

    def get_state( self, model_context ):
        state = super( ToPreviousRow, self ).get_state( model_context )
        #if state.enabled:
        #    state.enabled = ( model_context.current_row > 0 )
        return state

to_previous_row = ToPreviousRow()

class AbstractToFirst(object):

    render_hint = RenderHint.TOOL_BUTTON
    shortcut = QtGui.QKeySequence.StandardKey.MoveToStartOfDocument
    icon = Icon('fast-backward') # 'tango/16x16/actions/go-first.png'
    tooltip = _('First')
    verbose_name = _('First')

class ToFirstRow( AbstractToFirst, ToPreviousRow ):
    """Move to the first row in a table"""

    name = 'to_first'

    def gui_run( self, gui_context ):
        if gui_context.item_view is not None:
            gui_context.item_view.selectRow( 0 )
        else:
            qml_action_step(gui_context, 'ToFirstRow', keep_context_id=True)

to_first_row = ToFirstRow()

class AbstractToNext(object):

    render_hint = RenderHint.TOOL_BUTTON
    shortcut = QtGui.QKeySequence.StandardKey.MoveToNextPage
    icon = Icon('step-forward') # 'tango/16x16/actions/go-next.png'
    tooltip = _('Next')
    verbose_name = _('Next')
    
class ToNextRow( AbstractToNext, ListContextAction ):
    """Move to the next row in a table"""

    name = 'to_next'

    def gui_run( self, gui_context ):
        if gui_context.item_view is not None:
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
        else:
            qml_action_step(gui_context, 'ToNextRow', keep_context_id=True)

    def get_state( self, model_context ):
        state = super( ToNextRow, self ).get_state( model_context )
        #if state.enabled:
        #    max_row = model_context.collection_count - 1
        #    state.enabled = ( model_context.current_row < max_row )
        return state

to_next_row = ToNextRow()

class AbstractToLast(object):

    render_hint = RenderHint.TOOL_BUTTON
    shortcut = QtGui.QKeySequence.StandardKey.MoveToEndOfDocument
    icon = Icon('fast-forward') # 'tango/16x16/actions/go-last.png'
    tooltip = _('Last')
    verbose_name = _('Last')
    
class ToLastRow( AbstractToLast, ToNextRow ):
    """Move to the last row in a table"""

    name = 'to_last'

    def gui_run( self, gui_context ):
        if gui_context.item_view is not None:
            item_view = gui_context.item_view
            item_view.selectRow( item_view.model().rowCount() - 1 )
        else:
            qml_action_step(gui_context, 'ToLastRow', keep_context_id=True)

to_last_row = ToLastRow()

class ClearMapping(Action):
    """
    Clear a selection of mappings
    """

    verbose_name = _('Clear')
    name = 'clear_mapping'

    def model_run(self, model_context, mode):
        from camelot.view import action_steps

        cleared_mappings = list()
        for mapping in model_context.get_selection():
            if mapping.field is not None:
                mapping.field = None
                cleared_mappings.append(mapping)
        yield action_steps.UpdateObjects(cleared_mappings)


class ExportSpreadsheet( ListContextAction ):
    """Export all rows in a table to a spreadsheet"""

    render_hint = RenderHint.TOOL_BUTTON
    icon = Icon('file-excel') # 'tango/16x16/mimetypes/x-office-spreadsheet.png'
    tooltip = _('Export to MS Excel')
    verbose_name = _('Export to MS Excel')
    name = 'export'

    max_width = 40
    font_name = 'Calibri'
    
    def model_run( self, model_context, mode ):
        from decimal import Decimal
        from camelot.view.import_utils import (
            ColumnMapping, ColumnSelectionAdmin
        )
        from camelot.view.utils import (
            get_settings, local_date_format, local_datetime_format,
            local_time_format
        )
        from camelot.view import action_steps
        from camelot.admin.action.export_mapping import SaveExportMapping, RestoreExportMapping, RemoveExportMapping
        #
        # Select the columns that need to be exported
        # 
        yield action_steps.UpdateProgress(text=_('Prepare export'))
        admin = model_context.admin
        # Todo : settings should not be accessed from the model
        settings = get_settings(admin.get_name())
        settings.beginGroup('export_spreadsheet')
        all_fields = admin.get_all_fields_and_attributes()
        field_choices = [(f,str(entity_fa['name'])) for f,entity_fa in
                         all_fields.items() ]
        field_choices.sort(key=lambda field_tuple:field_tuple[1])
        list_columns = admin.get_columns()
        # the admin might show more columns then fields available, if the
        # columns are generated dynamically
        max_mapping_length = max(len(list_columns), len(all_fields))
        row_data = [None] * max_mapping_length
        column_range = range(max_mapping_length)
        mappings = []
        for i, default_field in itertools.zip_longest(column_range,
                                                      admin.get_columns(),
                                                      fillvalue=None):
            mappings.append(ColumnMapping(i, [row_data], default_field))
            
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
        filename = action_steps.OpenFile.create_temporary_file( '.xlsx' )
        workbook = xlsxwriter.Workbook(filename, {'constant_memory': True})
        sheet = workbook.add_worksheet()
        
        #
        # write styles
        #
        title_style = workbook.add_format({
                                            'font_name':       self.font_name,
                                            'bold':            True,
                                            'font_size':       12,
                                            })
        header_style = workbook.add_format({
                                            'font_name':       self.font_name,
                                            'bold':            True,
                                            'font_color':      '#FFFFFF',
                                            'font_size':       10,
                                            'bg_color':        '#4F81BD',
                                            'bottom':          1,
                                            'top':             1,
                                            'border_color':    '#95B3D7',
                                            })

        sheet.write(0, 0, admin.get_verbose_name_plural(), title_style)
        
        #
        # create some patterns and formats
        #
        date_format = workbook.add_format({'num_format': local_date_format()})
        datetime_format = workbook.add_format({'num_format': local_datetime_format()})
        time_format = workbook.add_format({'num_format': local_time_format()})
        int_format = workbook.add_format({'num_format': '0'})
        decimal_format = workbook.add_format({'num_format': '0.00'})
        numeric_style = []
        for i in range(12):
            style = workbook.add_format({'num_format': '0.' + ('0' * i)})
            numeric_style.append(style)

        #
        # write headers
        #
        sheet.autofilter(1, 0, 1, len(columns) - 1)
        sheet.set_column(0, len(columns) - 1, 20)
        field_names = []
        for i, (name, field_attributes) in enumerate( columns ):
            verbose_name = str( field_attributes.get( 'name', name ) )
            field_names.append( name )
            sheet.write(1, i, verbose_name, header_style)
        
        #
        # write data
        #
        offset = 2
        static_attributes = list(admin.get_static_field_attributes(field_names)) 
        for j, obj in enumerate( model_context.get_collection( yield_per = 100 ) ):
            dynamic_attributes = admin.get_dynamic_field_attributes( obj, 
                                                                     field_names )
            row = offset + j
            if j % 100 == 0:
                yield action_steps.UpdateProgress( j, model_context.collection_count )
            fields = enumerate(zip(field_names, 
                                             static_attributes,
                                             dynamic_attributes))
            for i, (name, attributes, delta_attributes) in fields:
                attributes.update( delta_attributes )
                value = getattr( obj, name )
                style = None
                if value is not None:
                    if isinstance( value, Decimal ):
                        style = decimal_format
                    elif isinstance( value, list ):
                        separator = attributes.get('separator', ', ')
                        value = separator.join([str(el) for el in value])
                    elif isinstance( value, float ):
                        precision = attributes.get('precision')
                        # Set default precision of 2 when precision is undefined, instead of using the default argument of the dictionary's get method,
                        # as that only handles the precision key not being present, not it being explicitly set to None.
                        if precision is None:
                            precision = 2
                        style = numeric_style[precision]
                    elif isinstance( value, int ):
                        style = int_format
                    elif isinstance( value, datetime.date ):
                        style = date_format
                    elif isinstance( value, datetime.datetime ):
                        style = datetime_format
                    elif isinstance( value, datetime.time ):
                        style = time_format
                    elif attributes.get('to_string') is not None:
                        value = str(attributes['to_string'](value))
                    else:
                        value = str(value)
                else:
                    # empty cells should be filled as well, to get the
                    # borders right
                    value = ''
                sheet.write(row, i, value, style)

        yield action_steps.UpdateProgress( text = _('Saving file') )
        workbook.close()
        yield action_steps.UpdateProgress( text = _('Opening file') )
        yield action_steps.OpenFile( filename )

export_spreadsheet = ExportSpreadsheet()
    
class SelectAll( ListContextAction ):
    """Select all rows in a table"""
    
    verbose_name = _('Select &All')
    shortcut = QtGui.QKeySequence.StandardKey.SelectAll
    tooltip = _('Select all rows in the table')
    name = 'select_all'

    def gui_run( self, gui_context ):
        gui_context.item_view.selectAll()

select_all = SelectAll()
        
class ImportFromFile( EditAction ):
    """Import a csv file in the current table"""

    render_hint = RenderHint.TOOL_BUTTON
    verbose_name = _('Import from file')
    icon = Icon('file-import') # 'tango/16x16/mimetypes/text-x-generic.png'
    tooltip = _('Import from file')
    name = 'import'

    def model_run( self, model_context, mode ):
        import os.path
        import chardet
        from camelot.view import action_steps
        from camelot.view.import_utils import ( UnicodeReader, 
                                                RowData, 
                                                RowDataAdmin,
                                                XlsReader,
                                                ColumnMapping,
                                                ColumnMappingAdmin )
        super().model_run(model_context, mode)
        admin = model_context.admin
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
            default_fields = [field for field in admin.get_columns()
                              if admin.get_field_attributes(field).get('editable', True)]
            mappings = []
            # 
            # it should be possible to select not editable fields, to be able to
            # import foreign keys, these are not editable by default, it might
            # be better to explicitly allow foreign keys, but this info is not
            # in the field attributes
            #
            all_fields = [(f,str(entity_fa['name'])) for f,entity_fa in 
                          admin.get_all_fields_and_attributes().items() if entity_fa.get('from_string')]
            all_fields.sort(key=lambda field_tuple:field_tuple[1])
            for i, default_field in itertools.zip_longest(range(len(all_fields)),
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
            yield action_steps.MessageBox( icon = QtWidgets.QMessageBox.Icon.Warning, 
                                           title = _('Proceed with import'), 
                                           text = _('Importing data cannot be undone,\n'
                                                    'are you sure you want to continue') )
            #
            # import the temporary objects into real objects
            #
            with model_context.session.begin():
                for i,row in enumerate(collection):
                    new_entity_instance = admin.entity()
                    for field_name in row_data_admin.get_columns():
                        attributes = row_data_admin.get_field_attributes(field_name)
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
        
import_from_file = ImportFromFile()

class ReplaceFieldContents( EditAction ):
    """Select a field an change the content for a whole selection"""
    
    verbose_name = _('Replace field contents')
    tooltip = _('Replace the content of a field for all rows in a selection')
    icon = Icon('edit') # 'tango/16x16/actions/edit-find-replace.png'
    message = _('Field is not editable')
    resolution = _('Only select editable rows')
    shortcut = QtGui.QKeySequence.StandardKey.Replace
    name = 'replace'

    def gui_run( self, gui_context ):
        #
        # if there is an open editor on a row that will be deleted, there
        # might be an assertion failure in QT, or the data of the editor 
        # might be pushed to the changed row
        #
        if gui_context.item_view is not None:
            gui_context.item_view.close_editor()
        super(ReplaceFieldContents, self ).gui_run(gui_context)

    def model_run( self, model_context, mode ):
        from camelot.view import action_steps
        super().model_run(model_context, mode)
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

replace_field_contents = ReplaceFieldContents()

class FilterValue(object):
    """
    Abstract helper class for the `SetFilters` action to configure the filter values
    for a certain filter strategy and operator.
    The dimension of these filter values (remaining operands) depends on the arity of the operator.
    This class also provides functionality to associate implementations of :class: `camelot.admin.action.list_filter.AbstractFilterStrategy`
    with implementations of this FilterValue interface; either by defining them as an innner Value class, or directly using the :method register: method.
    Using the :method for_strategy: the concrete registered FilterValue class for a certain filter strategy class can be retrieved afterwards.
    """
    filter_strategy = None
    _filter_values = {}

    def __init__(self, strategy, operator, value_1=None, value_2=None):
        assert isinstance(strategy, self.filter_strategy)
        self.strategy = strategy
        self.operator = operator
        self.value_1 = value_1
        self.value_2 = value_2
        self._other_values = []

    @property
    def operator_prefix(self):
        return str(self.operator.prefix)

    @property
    def operator_infix(self):
        if self.operator.infix is not None:
            return str(self.operator.infix)

    def get_operands(self):
        operands = (self.value_1, self.value_2, *self._other_values)
        # Determine appropriate number of operands based on the maximum arity of the operator (-1 because the filtered attribute is an operand as well).
        # The arity's maximum may be undefined (e.g. for multi-ary operators), in which case the operands should not be sliced.
        if self.operator.arity.maximum is not None:
            return operands[0:self.operator.arity.maximum-1]
        return [op for op in operands if op is not None]

    def set_operands(self, *operands):
        for i, operand in enumerate(operands[:2], start=1):
            if i == 1: self.value_1 = operand
            if i == 2: self.value_2 = operand
        self._other_values = operands[2:]

    @classmethod
    def for_strategy(cls, filter_strategy):
        """
        Get the default :class:`FilterValue` class for the given specific filter
        strategy class, return None, if not known.  The FilterValue
        should either be registered through the :meth:`register` method or be
        defined as an inner class with name :keyword:`Value` of the filter strategy.

        :param filter_strategy: a subclass of :class: `camelot.admin.action.list_filter.AbstractFilterStrategy`
        """
        from camelot.admin.action.list_filter import AbstractFilterStrategy
        assert issubclass(filter_strategy, AbstractFilterStrategy)
        try:
            return cls._filter_values[filter_strategy]
        except KeyError:
            for strategy_cls in filter_strategy.__mro__:
                if issubclass(strategy_cls, AbstractFilterStrategy) and strategy_cls.name == filter_strategy.name:
                    value_class = cls._filter_values.get(strategy_cls, None)
                    if value_class is None:
                        if hasattr(strategy_cls, 'Value'):
                            value_class = strategy_cls.Value
                            value_class.filter_strategy = filter_strategy
                            break
                    else:
                        break
            else:
                raise Exception('Could not construct a default filter value class')
            cls._filter_values[filter_strategy] = value_class
            return value_class

    @classmethod
    def register(cls, filter_strategy, value_class):
        """
        Associate a certain FilterValue class with a filter strategy.
        This FilterValue will be used as default.

        :param filter_strategy: :class:`camelot.admin.action.list_filter.AbstractFilterStrategy`
        :param value_class: a subclass of `FilterValue.`
        """
        assert value_class.filter_strategy == filter_strategy
        cls._filter_values[filter_strategy] = value_class

class SetFilters(Action, AbstractModelFilter):
    """
    Apply a set of filters on a list.
    This action differs from those in `list_filter` in the sense that it will
    pop up a dialog to configure a complete filter and wont allow the user
    to apply filters from within its widget.
    """

    render_hint = RenderHint.TOOL_BUTTON
    verbose_name = _('Find')
    tooltip = _('Filter the data')
    icon = Icon('filter')
    name = 'filter'

    def get_filter_strategies(self, model_context, priority_level=None):
        """:return: a list of field strategies the user can select."""
        filter_strategies = list(model_context.admin.get_field_filters(priority_level).items())
        filter_strategies.sort(key=lambda choice:(choice[1].priority_level.value, str(choice[1].get_verbose_name())))
        return filter_strategies

    def model_run( self, model_context, mode ):
        from camelot.view import action_steps

        if mode == '__clear':
            new_filter_values = {}
        elif mode is None:
            new_filter_values = {}
        else:
            from camelot.admin.action.list_filter import Operator, Many2OneFilter, One2ManyFilter
            operator_name, filter_field_name = mode.split('-')
            filter_values = model_context.proxy.get_filter(self) or {}
            filter_strategies = model_context.admin.get_field_filters()
            filter_strategy = filter_strategies.get(filter_field_name)
            filter_field_strategy = filter_strategy.get_field_strategy()
            filter_value_cls = FilterValue.for_strategy(type(filter_field_strategy))
            filter_value_admin = model_context.admin.get_related_admin(filter_value_cls)
            filter_operator = Operator[operator_name]
            filter_value = filter_value_cls(filter_field_strategy, filter_operator)

            # The filter values should only be updated by the user in case of multi-ary filter operators,
            # which requires filter values to be entered as the additional operands.
            # Unary operators can be applied directly, as the filter attribute is the only operand.
            if filter_operator.arity.minimum > 1:
                # The Many2OneFilter needs a selection of Entity objects to filter the foreign key relationship with.
                # So let the user select one, and programmatically set the filter value to the selected entity's id.
                if isinstance(filter_field_strategy, (Many2OneFilter, One2ManyFilter)):
                    admin = filter_field_strategy.admin or model_context.admin.get_related_admin(filter_field_strategy.entity)
                    query = None
                    if filter_field_strategy.where is not None:
                        query = admin.get_query()
                        query = query.filter(filter_field_strategy.where)
                    objects = yield action_steps.SelectObjects(admin, query)
                    filter_value.set_operands(*objects)
                # Other multi-ary operator filter strategies require some filter value(s) from the user to be filled in:
                else:
                    yield action_steps.ChangeObject(filter_value, filter_value_admin, title=ugettext('Filter {}').format(filter_field_strategy.get_verbose_name()))

            operands = [filter_field_strategy.value_to_string(operand, model_context.admin) for operand in filter_value.get_operands()]
            new_filter_values = {k:v for k,v in filter_values.items()}
            new_filter_values[filter_field_name] = (filter_value.operator.name, *operands)

        yield action_steps.SetFilter(self, new_filter_values)
        new_state = self._get_state(model_context, new_filter_values)
        yield action_steps.UpdateActionsState(model_context, {self: new_state})

    def decorate_query(self, query, values):
        from camelot.admin.action.list_filter import Operator
        # Previously, the query was decorated with the the string-based filter value tuples by applying them to the query using filter_by.
        # This created problems though, as the filters are applied to the query's current zero joinpoint, which changes after every applied join to the joined entity.
        # This caused filters in some cases being tried to applied to the wrong entity.
        # Therefore we turn the filter values into entity descriptors condition clauses using the query's entity zero, which should always be the correct one.
        clauses = []
        for name, (operator_name, *operands) in values.items():
            filter_strategy = self.admin.get_field_filters().get(name)
            operator = Operator[operator_name]
            filter_clause = filter_strategy.get_clause(self.admin, query.session, operator, *operands)
            if filter_clause is not None:
                clauses.append(filter_clause)
        return query.filter(*clauses)
    
    def _get_state(self, model_context, filter_value):
        state = super(SetFilters, self).get_state(model_context)
        state.modes = modes = []
        if len(filter_value) is not None:
            state.notification = True
        # Only show clear filter mode if any filters are active
        if len(filter_value):
            modes.extend([Mode('__clear', _('Clear filter'), icon=Icon('minus-circle'))])
        selected_mode_names = [op + '-' + field for field, (op, *_) in filter_value.items()]
        for name, filter_strategy in self.get_filter_strategies(model_context):
            operator_modes = []
            for op in filter_strategy.get_operators():
                mode_name = op.name + '-' + name
                icon = Icon('check-circle') if mode_name in selected_mode_names else None
                operator_modes.append(Mode(mode_name, str(op.verbose_name), icon=icon))
            if operator_modes:
                icon = Icon('check-circle') if name in filter_value else None
                modes.append(Mode(name, str(filter_strategy.get_verbose_name()), icon=icon, modes=operator_modes))
        self.admin = model_context.admin
        return state

    def get_state(self, model_context):
        filter_value = model_context.proxy.get_filter(self) or {}
        return self._get_state(model_context, filter_value)

set_filters = SetFilters()

class AddExistingObject( EditAction ):
    """Add an existing object to a list if it is not yet in the
    list"""
    
    tooltip = _('Add')
    verbose_name = _('Add')
    icon = Icon('plus') # 'tango/16x16/actions/list-add.png'
    name = 'add_object'
    
    def model_run( self, model_context, mode ):
        from sqlalchemy.orm import object_session
        from camelot.view import action_steps
        super().model_run(model_context, mode)
        objs_to_add = yield action_steps.SelectObjects(model_context.admin)
        for obj_to_add in objs_to_add:
            for obj in model_context.get_collection():
                if obj_to_add == obj:
                    return
            model_context.proxy.append(obj_to_add)
        yield action_steps.UpdateObjects(objs_to_add)
        for obj_to_add in objs_to_add:
            yield action_steps.FlushSession(object_session(obj_to_add))
            break

add_existing_object = AddExistingObject()

class AddNewObjectMixin(object):
    
    def create_object(self, model_context, admin, type_=None, session=None):
        """
        Create a new entity instance based on the given model_context as an instance of the given admin's entity.
        This is done in the given session, or the default session if it is not yet attached to a session.
        """
        new_object = admin.entity(_session=session)
        admin.add(new_object)
        # defaults might depend on object being part of a collection
        self.get_proxy(model_context, admin).append(admin.get_subsystem_object(new_object))
        # Give the default fields their value
        admin.set_defaults(new_object)
        return new_object
        yield

    def model_run( self, model_context, mode ):
        from camelot.view import action_steps
        admin = self.get_admin(model_context, mode)
        assert admin is not None # required by vfinance/test/test_facade/test_asset.py
        if not admin.is_editable():
            raise RuntimeError("Action's model_run() called on noneditable entity")
        create_inline = model_context.field_attributes.get('create_inline', False)
        new_object = yield from self.create_object(model_context, admin, mode)
        subsystem_object = admin.get_subsystem_object(new_object)
        # if the object is valid, flush it, but in ancy case inform the gui
        # the object has been created
        yield action_steps.CreateObjects((subsystem_object,))
        if not len(admin.get_validator().validate_object(new_object)):
            session = orm.object_session(subsystem_object)
            yield action_steps.FlushSession(session)
        # Even if the object was not flushed, it's now part of a collection,
        # so it's dependent objects should be updated
        yield action_steps.UpdateObjects(
            tuple(admin.get_depending_objects(new_object))
        )
        if create_inline is False:
            yield action_steps.OpenFormView(new_object, admin.get_proxy([new_object]), admin)

class AddNewObject( AddNewObjectMixin, EditAction ):
    """Add a new object to a collection. Depending on the
    'create_inline' field attribute, a new form is opened or not.

    This action will also set the default values of the new object, add the
    object to the session, and flush the object if it is valid.
    """

    shortcut = QtGui.QKeySequence.StandardKey.New
    icon = Icon('plus-circle') # 'tango/16x16/actions/document-new.png'
    tooltip = _('New')
    verbose_name = _('New')
    name = 'new_object'

    def get_admin(self, model_context, mode):
        """
        Return the admin used for creating and handling the new entity instance with.
        By default, the given model_context's admin is used.
        """
        return model_context.admin

    def get_proxy(self, model_context, admin):
        return model_context.proxy

add_new_object = AddNewObject()

class RemoveSelection(DeleteSelection):
    """Remove the selected objects from a list without deleting them"""
    
    shortcut = None
    tooltip = _('Remove')
    verbose_name = _('Remove')
    icon = Icon('minus') # 'tango/16x16/actions/list-remove.png'
    name = 'remove_selection'
            
    def handle_object( self, model_context, obj ):
        model_context.proxy.remove( obj )
        # no StopIteration, since the supergenerator needs to
        # continue to flush the session
        yield None

remove_selection = RemoveSelection()
