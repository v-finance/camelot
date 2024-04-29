import collections
import logging
from dataclasses import dataclass, field, asdict, InitVar
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

from ..admin.action.base import Action
from ..admin.icon import Icon
from ..admin.action.field_action import FieldActionModelContext
from ..core.cache import ValueCache
from ..core.item_model import (
    ObjectRole, PreviewRole,
    ActionRoutesRole, ActionStatesRole, CompletionsRole,
    ActionModeRole, FocusPolicyRole,
    VisibleRole, NullableRole
)
from ..core.exception import log_programming_error
from ..core.naming import initial_naming_context, NameNotFoundException
from ..core.qt import Qt, QtGui
from camelot.core.serializable import DataclassSerializable


crud_action_context = initial_naming_context.bind_new_context(
    'crud_action', immutable=True
)

def strip_data_from_object( obj, columns ):
    """For every column in columns, get the corresponding value from the
    object.  Getting a value from an object is time consuming, so using
    this function should be minimized.
    :param obj: the object of which to get data
    :param columns: a list of columns for which to get data
    """
    row_data = []

    for _i, col in enumerate( columns ):
        field_value = None
        try:
            field_value = getattr( obj, col )
        except (Exception, RuntimeError, TypeError, NameError) as e:
            message = "could not get field '%s' of object of type %s"%(col, obj.__class__.__name__)
            log_programming_error( logger, 
                                   message,
                                   exc_info = e )
        finally:
            row_data.append( field_value )
    return row_data

@dataclass
class DataCell(DataclassSerializable):

    row: int = -1
    column: int = -1
    flags: int = Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsDropEnabled | Qt.ItemFlag.ItemIsDragEnabled | Qt.ItemFlag.ItemIsEditable | Qt.ItemFlag.ItemIsSelectable

    roles: Dict[int, Any] = field(default_factory=dict)

    # used in camelot tests
    def get_standard_item(self):
        item = QtGui.QStandardItem()
        item.setFlags(self.flags)
        for role, value in self.roles.items():
            item.setData(value, role)
        return item

@dataclass
class DataRowHeader(DataclassSerializable):

    row: int = -1
    tool_tip: Optional[str] = None
    icon_name: Optional[str] = None
    object: int = 0
    verbose_identifier: str = ''
    valid: bool = True
    message: str = ''
    decoration: Optional[Icon] = None
    display: Optional[str] = None

@dataclass
class DataUpdate(DataclassSerializable):

    changed_ranges: InitVar

    header_items: List[DataRowHeader] = field(default_factory=list)
    cells: List[DataCell] = field(default_factory=list)

    def __post_init__(self, changed_ranges):
        for row, header_item, items in changed_ranges:
            self.header_items.append(header_item)
            self.cells.extend(items)


invalid_item = DataCell()
invalid_item.flags = Qt.ItemFlag.NoItemFlags
invalid_item.roles[Qt.ItemDataRole.EditRole] = None
invalid_item.roles[PreviewRole] = None
invalid_item.roles[ObjectRole] = None
invalid_item.roles[CompletionsRole] = None
invalid_item.roles[ActionRoutesRole] = '[]'
invalid_item.roles[ActionStatesRole] = '[]'
invalid_item.roles[ActionModeRole] = None
invalid_item.roles[FocusPolicyRole] = Qt.FocusPolicy.NoFocus
invalid_item.roles[VisibleRole] = True
invalid_item.roles[NullableRole] = True


class UpdateMixin(object):

    @classmethod
    def field_action_model_context(cls, model_context, obj, field_attributes):
        field_name = field_attributes['field_name']
        field_action_model_context = FieldActionModelContext(model_context.admin)
        field_action_model_context.field = field_name
        field_action_model_context.value = strip_data_from_object(obj, [field_name])[0]
        field_action_model_context.field_attributes = field_attributes
        field_action_model_context.obj = obj
        return field_action_model_context

    def add_data(self, model_context, row, columns, obj, data):
        """Add data from object o at a row in the cache
        :param row: the row in the cache into which to add data
        :param columns: the columns for which data should be added
        :param obj: the object from which to strip the data
        :param data: fill the data cache, otherwise only fills the header cache
        :return: the changes to the item model
        """
        admin = model_context.admin
        static_field_attributes = model_context.static_field_attributes
        column_names = [model_context.static_field_attributes[column]['field_name'] for column in columns]
        action_state = None
        logger.debug('add data for row {0}'.format(row))
        # @todo static field attributes should be cached ??
        is_object_valid = True
        if (admin.is_readable( obj ) and (data==True) and (obj is not None)):
            row_data = {column:data for column, data in zip(columns, strip_data_from_object(obj, column_names))}
            dynamic_field_attributes ={column:fa for column, fa in zip(columns, admin.get_dynamic_field_attributes(obj, column_names))}
            if admin.list_action:
                model_context.obj = obj
                model_context.current_row = row
                action_state = admin.list_action.get_state(model_context)
        else:
            row_data = {column:None for column in columns}
            dynamic_field_attributes = {column:{'editable':False} for column in columns}
            is_object_valid = False
        # keep track of the columns that changed, to limit the
        # number of editors/cells that need to be updated
        changed_columns = set()
        changed_columns.update(model_context.edit_cache.add_data(row, obj, row_data))
        changed_columns.update(model_context.attributes_cache.add_data(row, obj, dynamic_field_attributes))
        changed_ranges = []
        if row is not None:
            items = []
            locale = model_context.locale
            for column in changed_columns:
                if is_object_valid:
                    # copy to make sure the original dict can be reused in
                    # subsequent calls
                    field_attributes = dict(static_field_attributes[column])
                    # the dynamic attributes might update the static attributes,
                    # if get_dynamic_field_attributes is overwritten, like in
                    # the case of the EntityAdmin setting the onetomany fields
                    # to not editable for objects that are not persistent
                    field_attributes.update(dynamic_field_attributes[column])
                    delegate = field_attributes['delegate']
                    field_action_model_context = self.field_action_model_context(
                        model_context, obj, field_attributes
                    )
                    item = delegate.get_standard_item(locale, field_action_model_context)
                else:
                    item = DataCell(**asdict(invalid_item))
                # remove roles with None values
                item.roles = { role: value for role, value in item.roles.items() if value is not None}
                item.row = row
                item.column = column
                items.append(item)
            try:
                verbose_identifier = admin.get_verbose_identifier(obj)
            except (Exception, RuntimeError, TypeError, NameError) as e:
                message = "could not get verbose identifier of object of type %s"%(obj.__class__.__name__)
                log_programming_error(logger,
                                      message,
                                      exc_info=e)
                verbose_identifier = u''
            valid = False
            message = None
            if is_object_valid:
                for message in model_context.validator.validate_object(obj):
                    break
                else:
                    valid = True
            header_item = DataRowHeader()
            header_item.row = row
            header_item.object = id(obj)
            header_item.verbose_identifier = verbose_identifier
            header_item.valid = valid
            header_item.message = message
            if action_state is not None:
                header_item.tool_tip = action_state.tooltip
                header_item.display = str(action_state.verbose_name)
                # The decoration role contains the icon as a QPixmap which is used in the old table view.
                header_item.decoration = action_state.icon
                if action_state.icon is not None:
                    # The whatsThis role contains the icon name which is used in the QML table view.
                    # (note: user roles can't be used in a QML VerticalHeaderView)
                    header_item.icon_name = action_state.icon.name
            changed_ranges.append((row, header_item, items))
        return changed_ranges


class ChangeSelection(Action):

    name = 'change_selection'

    def model_run(self, model_context, mode):
        from camelot.view import action_steps
        # validate & set current_row
        model_context.current_row = None
        if mode['current_row'] is not None:
            current_obj = model_context.get_object(mode['current_row'])
            if id(current_obj) == mode['current_row_id']:
                model_context.current_row = mode['current_row']
            else:
                logger.error('Invalid current_row_id used for selection')
        # validate & set selected rows
        model_context.selected_rows = []
        if len(mode['selected_rows']) == len(mode['selected_rows_ids']):
            for i in range(len(mode['selected_rows'])):
                row_range = mode['selected_rows'][i]
                row_range_ids = mode['selected_rows_ids'][i]
                # -1 is a sentinal value which can be used to construct python slice like selections.
                begin_valid = True
                if row_range[0] == -1:
                    row_range[0] = 0
                else:
                    begin_obj = model_context.get_object(row_range[0])
                    begin_valid = id(begin_obj) == row_range_ids[0]
                end_valid = True
                if row_range[1] == -1:
                    row_range[1] = len(model_context.proxy) - 1
                else:
                    end_obj = model_context.get_object(row_range[1])
                    end_valid = id(end_obj) == row_range_ids[1]
                if begin_valid and end_valid:
                    model_context.selected_rows.append(row_range)
                else:
                    logger.error('Invalid selected_rows_ids used for selection')

        model_context.current_column = mode['current_column']
        model_context.current_field_name = mode['current_field_name']
        model_context.collection_count = len(model_context.proxy)
        model_context.selection_count = 0
        for row_range in model_context.selected_rows:
            model_context.selection_count += (row_range[1] - row_range[0]) + 1
        action_states = []
        for action_route in mode['action_routes']:
            action = initial_naming_context.resolve(tuple(action_route))
            state = action.get_state(model_context)
            action_states.append((action_route, state))
        yield action_steps.ChangeSelection(action_states)

changeselection_name = crud_action_context.bind(ChangeSelection.name, ChangeSelection(), True)

class Completion(Action):

    name = 'completion'

    def model_run(self, model_context, mode):
        from camelot.view import action_steps
        row = mode['row']
        column = mode['column']
        prefix = mode['prefix']
        field_name = model_context.static_field_attributes[column]['field_name']
        admin = model_context.static_field_attributes[column]['admin']
        object_slice = list(model_context.proxy[row:row+1])
        if not len(object_slice):
            logger.error('Cannot generate completions : no object in row {0}'.format(row))
            return
        obj = object_slice[0]
        completions = model_context.admin.get_completions(
            obj,
            field_name,
            prefix,
        )

        # Empty if the field does not support autocompletions
        completions = [
            action_steps.CompletionValue(
                value=initial_naming_context._bind_object(obj),
                verbose_name=admin.get_verbose_search_identifier(obj),
                tooltip='id: %s' % (admin.primary_key(obj)))
            for obj in completions] if completions is not None else []
        yield action_steps.Completion(row, column, prefix, completions)

    def __repr__(self):
        return '{0.__class__.__name__}'.format(self)

completion_name = crud_action_context.bind(Completion.name, Completion(), True)


class RowCount(Action):

    name = 'row_count'

    def model_run(self, model_context, mode):
        from camelot.view import action_steps
        rows = len(model_context.proxy)
        # clear the whole cache, there might be more efficient means to 
        # do this
        model_context.edit_cache = ValueCache(model_context.edit_cache.max_entries)
        model_context.attributes_cache = ValueCache(model_context.attributes_cache.max_entries)
        yield action_steps.RowCount(rows)

rowcount_name = crud_action_context.bind(RowCount.name, RowCount(), True)


class Update(Action, UpdateMixin):

    name = 'update'

    def model_run(self, model_context, mode):
        changed_ranges = []
        from camelot.view import action_steps
        objects_name = tuple(mode['objects'])
        try:
            objects = initial_naming_context.resolve(objects_name)
        except NameNotFoundException:
            logger.warn('received update request for non existing objects : {}'.format(objects_name))
            yield action_steps.UpdateProgress(text='Updating view failed')
            return
        for obj in objects:
            try:
                row = model_context.proxy.index(obj)
            except ValueError:
                continue
            #
            # Because the entity is updated, it might no longer be in our
            # collection, therefore, make sure we don't access the collection
            # to strip data of the entity
            #
            columns = tuple(model_context.edit_cache.get_data(row).keys())
            if len(columns):
                logger.debug('evaluate changes in row {0}, column {1} to {2}'.format(row, min(columns), max(columns)))
            else:
                logger.debug('evaluate changes in row {0}'.format(row))
            changed_ranges.extend(self.add_data(model_context, row, columns, obj, True))
        yield action_steps.Update(changed_ranges)

    def __repr__(self):
        return '{0.__class__.__name__}'.format(self)

update_name = crud_action_context.bind(Update.name, Update(), True)


class Created(Action, UpdateMixin):
    """
    Does not subclass RowCount, because row count will reset the whole edit
    cache.

    When a created object is detected simply update the row of this object,
    assuming other objects have not been changed position.
    """

    name = 'created'

    def model_run(self, model_context, mode):
        from camelot.view import action_steps
        # the proxy cannot return it's length including the new object before
        # the new object has been indexed
        objects = initial_naming_context.resolve(tuple(mode['objects']))
        changed_ranges = []
        for obj in objects:
            try:
                row = model_context.proxy.index(obj)
            except ValueError:
                continue
            columns = tuple(range(len(model_context.static_field_attributes)))
            changed_ranges.extend(self.add_data(model_context, row, columns, obj, True))
        yield action_steps.Created(changed_ranges) 

    def __repr__(self):
        return '{0.__class__.__name__}'.format(self)

created_name = crud_action_context.bind(Created.name, Created(), True)


class Deleted(RowCount, UpdateMixin):

    name = 'deleted'

    def model_run(self, model_context, mode):
        from camelot.view import action_steps
        row = None
        objects_to_remove = set()
        changed_ranges = []
        #
        # the object might or might not be in the proxy when the
        # deletion is handled
        #
        objects = initial_naming_context.resolve(tuple(mode['objects']))
        for obj in objects:
            try:
                row = model_context.proxy.index(obj)
            except ValueError:
                continue
            objects_to_remove.add(obj)
            #
            # If the object was valid, the header item should be updated
            # make sure all views know the validity of the row has changed
            #
            header_item = DataRowHeader()
            header_item.row = row
            header_item.object = None
            header_item.verbose_identifier = u''
            header_item.valid = True
            changed_ranges.append((row, header_item, tuple()))
        #
        # if the object that is going to be deleted is in the proxy, the
        # proxy might be unaware of the deleting, so remove the object from
        # the proxy
        for obj in objects_to_remove:
            model_context.proxy.remove(obj)
        # update before changing the rowcount, otherwise the update might
        # modify the rowcount again
        yield action_steps.Update(changed_ranges)
        #
        # when it's no longer in the proxy, the len of the proxy will be
        # different from the one of the view
        #
        rows = len(model_context.proxy)
        if (row is not None) or (rows != mode['rows']):
            # but updating the view is only needed if the rows changed
            yield from super(Deleted, self).model_run(model_context, mode)

deleted_name = crud_action_context.bind(Deleted.name, Deleted(), True)


class RowData(Update):

    name = 'row_data'

    def offset_and_limit_rows_to_get(self, rows):
        """From the current set of rows to get, find the first
        continuous range of rows that should be fetched.
        :return: (offset, limit)
        """
        offset, limit, i = 0, 0, 0
        rows_to_get = list(rows)
        #
        # see if there is anything left to do
        #
        try:
            if len(rows_to_get):
                rows_to_get.sort()
                offset = rows_to_get[0]
                #
                # find first discontinuity
                #
                for i in range(offset, rows_to_get[-1]+1):
                    if rows_to_get[i-offset] != i:
                        break
                limit = i - offset + 1
        except IndexError as e:
            logger.error('index error with rows_to_get %s'%str(rows_to_get), exc_info=e)
            raise e
        return (offset, limit)

    def model_run(self, model_context, mode):
        from camelot.view import action_steps
        rows = mode["rows"]
        columns = mode["columns"]
        offset, limit = self.offset_and_limit_rows_to_get(rows)
        changed_ranges = []
        for obj in list(model_context.proxy[offset:offset+limit]):
            row = model_context.proxy.index(obj)
            changed_ranges.extend(self.add_data(model_context, row, columns, obj, True))
        yield action_steps.Update(changed_ranges)

    def __repr__(self):
        return '{0.__class__.__name__}'.format(self)

rowdata_name = crud_action_context.bind(RowData.name, RowData(), True)


class SetColumns(Action):

    name = 'set_columns'

    def __repr__(self):
        return '{0.__class__.__name__}'.format(self)

    def model_run(self, model_context, mode):
        from camelot.view import action_steps
        columns = list(mode)
        model_context.static_field_attributes = list(
            model_context.admin.get_static_field_attributes(columns)
        )
        # creating the header items should be done here instead of in the gui
        # run
        #static_field_attributes = list()
        #future code
        #for fa in model_context.static_field_attributes:
            #included_attrs = ['name', 'field_name', 'editable', 'nullable', 'colmn_width']
            #static_field_attributes.append({attr: fa[attr] for attr in included_attrs})
        yield action_steps.SetColumns(model_context.admin, model_context.static_field_attributes)

setcolumns_name = crud_action_context.bind(SetColumns.name, SetColumns(), True)


class ChangedObjectMixin(object):

    def add_changed_object(
        self, model_context, depending_objects_before_change,
        obj,
        created_objects, updated_objects, deleted_objects):
        """
        Add the changed object and row to the changed_ranges, created_objects etc.
        """
        from sqlalchemy.exc import DatabaseError
        admin = model_context.admin
        subsystem_obj = admin.get_subsystem_object(obj)
        for message in model_context.validator.validate_object(obj):
            break
        else:
            # save the state before the update
            was_persistent = admin.is_persistent(obj)
            try:
                admin.flush(obj)
            except DatabaseError as e:
                #@todo: when flushing fails ??
                logger.error( 'Programming Error, could not flush object', exc_info = e )
            if was_persistent is False:
                created_objects.add(subsystem_obj)
        updated_objects.add(subsystem_obj)
        updated_objects.add(obj)
        depending_objects = depending_objects_before_change.union(set(admin.get_depending_objects(obj)))
        for depending_object in depending_objects:
            related_admin = admin.get_related_admin(type(depending_object))
            if related_admin.is_deleted(depending_object):
                deleted_objects.update({depending_object})
            else:
                updated_objects.update({depending_object})


class SetData(Update, ChangedObjectMixin):

    name = 'set_data'

    def model_run(self, model_context, mode):
        from camelot.view import action_steps
        grouped_requests = collections.defaultdict( list )
        updated_objects, created_objects, deleted_objects = set(), set(), set()
        for row, obj_id, column, value in mode:
            grouped_requests[(row, obj_id)].append((column, value))
        admin = model_context.admin
        for (row, obj_id), request_group in grouped_requests.items():
            object_slice = list(model_context.proxy[row:row+1])
            if not len(object_slice):
                logger.error('Cannot set data : no object in row {0}'.format(row))
                continue
            obj = object_slice[0]
            if not (id(obj)==obj_id):
                logger.warn('Cannot set data : object in row {0} is inconsistent with view, {1} vs {2}'.format(row, id(obj), obj_id))
                continue
            #
            # the object might have been deleted while an editor was open
            # 
            if admin.is_deleted(obj):
                continue
            changed = False
            for column, value in request_group:

                static_field_attributes = model_context.static_field_attributes[column]
                field_name = static_field_attributes['field_name']

                logger.debug( 'set data for row %s;col %s' % ( row, column ) )

                new_value = initial_naming_context.resolve(tuple(value))
                old_value = getattr(obj, field_name)
                depending_objects_before_set = set(admin.get_depending_objects(obj))
                value_changed = ( new_value != old_value )
                #
                # In case the field is a key in a storage, it cannot be changed.
                # through the editor. VFIN-2494
                #
                if static_field_attributes.get('storage', False):
                    value_changed = False
                #
                # In case the attribute is a OneToMany or ManyToMany, we cannot simply compare the
                # old and new value to know if the object was changed, so we'll
                # consider it changed anyway
                #
                direction = static_field_attributes.get( 'direction', None )
                if direction in ( 'manytomany', 'onetomany' ):
                    value_changed = True
                if value_changed is not True:
                    continue
                #
                # now check if this column is editable, since editable might be
                # dynamic and change after every change of the object
                #
                fields = [field_name]
                for fa in admin.get_dynamic_field_attributes(obj, fields):
                    # if editable is not in the field_attributes dict, it wasn't
                    # dynamic but static, so earlier checks should have 
                    # intercepted this change
                    if fa.get('editable', True) == True:
                        # interrupt inner loop, so outer loop can be continued
                        break
                else:
                    continue
                # update the model
                try:
                    admin.set_field_value(obj, field_name, new_value)
                    #
                    # setting this attribute, might trigger a default function 
                    # to return a value, that was not returned before
                    #
                    admin.set_defaults(obj)
                except AttributeError as e:
                    logger.error( u"Can't set attribute %s to %s" % ( field_name, str( new_value ) ), exc_info = e )
                except TypeError:
                    # type error can be raised in case we try to set to a collection
                    pass
                changed = value_changed or changed
            if changed:
                self.add_changed_object(
                    model_context, depending_objects_before_set, obj,
                    created_objects, updated_objects, deleted_objects
                )
        created_objects = tuple(created_objects)
        updated_objects = tuple(updated_objects)
        deleted_objects = tuple(deleted_objects)
        yield action_steps.CreateUpdateDelete(
            objects_created=created_objects,
            objects_updated=updated_objects,
            objects_deleted=deleted_objects,
        )

setdata_name = crud_action_context.bind(SetData.name, SetData(), True)


class Sort(RowCount):

    name = 'sort'

    def model_run(self, model_context, mode):
        column, order = mode
        field_name = model_context.static_field_attributes[column]['field_name']
        model_context.proxy.sort(field_name, order!=Qt.SortOrder.AscendingOrder.value)
        yield from super(Sort, self).model_run(model_context, mode)

    def __repr__(self):
        return '{0.__class__.__name__}'.format(self)

sort_name = crud_action_context.bind(Sort.name, Sort(), True)


class RunFieldAction(Action, ChangedObjectMixin, UpdateMixin):

    name = 'field_action'

    def model_run(self, model_context, mode):
        from camelot.view import action_steps
        row = mode['row']
        column = mode['column']
        obj_id = mode['object']
        action_route = mode['action_route']
        action_mode = mode['action_mode']
        object_slice = list(model_context.proxy[row:row+1])
        if not len(object_slice):
            logger.error('Cannot run field action : no object in row {0}'.format(row))
            return
        obj = object_slice[0]
        if not (id(obj)==obj_id):
            logger.warn('Cannot run field action : object in row {0} is inconsistent with view, {1} vs {2}'.format(row, id(obj), obj_id))
            return
        depending_objects_before_change = set(model_context.admin.get_depending_objects(obj))
        static_field_attributes = model_context.static_field_attributes[column]
        action = initial_naming_context.resolve(tuple(action_route))
        # @todo : should include dynamic field attributes, but those are not
        # yet used in any of the field actions
        field_action_model_context = self.field_action_model_context(
            model_context, obj, static_field_attributes
        )
        field_action_model_context.field_attributes = static_field_attributes
        yield from action.model_run(field_action_model_context, action_mode)
        new_value = getattr(obj, static_field_attributes['field_name'])
        if field_action_model_context.value != new_value:
            updated_objects, created_objects, deleted_objects = set(), set(), set()
            self.add_changed_object(
                model_context, depending_objects_before_change, obj,
                created_objects, updated_objects, deleted_objects
            )
            created_objects = tuple(created_objects)
            updated_objects = tuple(updated_objects)
            deleted_objects = tuple(deleted_objects)
            yield action_steps.CreateUpdateDelete(
                objects_created=created_objects,
                objects_updated=updated_objects,
                objects_deleted=deleted_objects,
            )

runfieldaction_name = crud_action_context.bind(RunFieldAction.name, RunFieldAction(), True)
