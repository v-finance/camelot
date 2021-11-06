import collections
import logging

logger = logging.getLogger(__name__)

from ..admin.action.base import Action
from ..admin.action.field_action import FieldActionModelContext
from ..admin.admin_route import AdminRoute
from ..core.qt import Qt, QtGui, py_to_variant, variant_to_py
from ..core.item_model import VerboseIdentifierRole, ValidRole, ValidMessageRole, ObjectRole
from ..core.exception import log_programming_error
from .item_model.cache import ValueCache


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


class UpdateMixin(object):

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
        changed_ranges = []
        logger.debug('add data for row {0}'.format(row))
        # @todo static field attributes should be cached ??
        if (not admin.is_deleted( obj ) and (data==True) and (obj is not None)):
            row_data = {column:data for column, data in zip(columns, strip_data_from_object(obj, column_names))}
            dynamic_field_attributes ={column:fa for column, fa in zip(columns, admin.get_dynamic_field_attributes(obj, column_names))}
            if admin.list_action:
                model_context.obj = obj
                model_context.current_row = row
                action_state = admin.list_action.get_state(model_context)
        else:
            row_data = {column:None for column in columns}
            dynamic_field_attributes = {column:{'editable':False} for column in columns}
        # keep track of the columns that changed, to limit the
        # number of editors/cells that need to be updated
        changed_columns = set()
        changed_columns.update(model_context.edit_cache.add_data(row, obj, row_data))
        changed_columns.update(model_context.attributes_cache.add_data(row, obj, dynamic_field_attributes))
        if row is not None:
            items = []
            locale = model_context.locale
            for column in changed_columns:
                # copy to make sure the original dict can be reused in
                # subsequent calls
                field_attributes = dict(static_field_attributes[column])
                # the dynamic attributes might update the static attributes,
                # if get_dynamic_field_attributes is overwritten, like in 
                # the case of the EntityAdmin setting the onetomany fields
                # to not editable for objects that are not persistent
                field_attributes.update(dynamic_field_attributes[column])
                delegate = field_attributes['delegate']
                value = row_data[column]
                field_action_model_context = FieldActionModelContext()
                field_action_model_context.field = field_attributes['field_name']
                field_action_model_context.value = value
                field_action_model_context.field_attributes = field_attributes
                item = delegate.get_standard_item(locale, field_action_model_context)
                items.append((column, item))
            try:
                verbose_identifier = admin.get_verbose_identifier(obj)
            except (Exception, RuntimeError, TypeError, NameError) as e:
                message = "could not get verbose identifier of object of type %s"%(obj.__class__.__name__)
                log_programming_error(logger,
                                      message,
                                      exc_info=e)
                verbose_identifier = u''
            valid = False
            for message in model_context.validator.validate_object(obj):
                break
            else:
                valid = True
                message = None
            header_item = QtGui.QStandardItem()
            header_item.setData(py_to_variant(id(obj)), ObjectRole)
            header_item.setData(py_to_variant(verbose_identifier), VerboseIdentifierRole)
            header_item.setData(py_to_variant(valid), ValidRole)
            header_item.setData(py_to_variant(message), ValidMessageRole)
            if action_state is not None:
                header_item.setData(py_to_variant(action_state.tooltip), Qt.ItemDataRole.ToolTipRole)
                header_item.setData(py_to_variant(str(action_state.verbose_name)), Qt.ItemDataRole.DisplayRole)
                header_item.setData(py_to_variant(action_state.icon), Qt.ItemDataRole.DecorationRole)
            changed_ranges.append((row, header_item, items))
        return changed_ranges


class ChangeSelection(Action):

    name = 'change_selection'

    def __init__(self, action_routes, model_context):
        self.action_routes = action_routes
        self.model_context = model_context

    def model_run(self, model_context, mode):
        from camelot.view import action_steps
        action_states = []
        for action_route in self.action_routes:
            action = AdminRoute.action_for(action_route)
            state = action.get_state(self.model_context)
            action_states.append(state)
        yield action_steps.ChangeSelection(self.action_routes, action_states)
        
        
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
        completions = [admin.get_search_identifiers(e) for e in completions] if completions is not None else [] 
        yield action_steps.Completion(row, column, prefix, completions)

    def __repr__(self):
        return '{0.__class__.__name__}'.format(self)
    
    
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
        
   
class Update(Action, UpdateMixin):

    name = 'update'

    def __init__(self, objects):
        self.objects = objects

    def model_run(self, model_context, mode):
        changed_ranges = []
        from camelot.view import action_steps
        for obj_id in self.objects:
            try:
                obj = model_context.proxy.indexed_ids[obj_id]
            except KeyError:
                continue
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
        return '{0.__class__.__name__}({1} objects)'.format(self, len(self.objects))


class Created(Action, UpdateMixin):
    """
    Does not subclass RowCount, because row count will reset the whole edit
    cache.

    When a created object is detected simply update the row of this object,
    assuming other objects have not been changed position.
    """

    name = 'created'

    def __init__(self, objects):
        self.objects = objects

    def __repr__(self):
        return '{0.__class__.__name__}({1} objects)'.format(
            self, len(self.objects)
        )

    def model_run(self, model_context, mode):
        from camelot.view import action_steps
        # the proxy cannot return it's length including the new object before
        # the new object has been indexed
        changed_ranges = []
        for obj_id in self.objects:
            try:
                obj = model_context.proxy.indexed_ids[obj_id]
            except KeyError:
                continue
            try:
                row = model_context.proxy.index(obj)
            except ValueError:
                continue
            columns = tuple(range(len(model_context.static_field_attributes)))
            changed_ranges.extend(self.add_data(model_context, row, columns, obj, True))
        yield action_steps.Created(changed_ranges) 
        
        
class Deleted(RowCount, UpdateMixin):

    name = 'deleted'

    def __init__(self, objects, rows_in_view):
        """
        
        """
        super(Deleted, self).__init__()
        self.objects = objects
        self.rows_in_view = rows_in_view

    def model_run(self, model_context, mode):
        from camelot.view import action_steps
        row = None
        objects_to_remove = set()
        changed_ranges = []
        #
        # the object might or might not be in the proxy when the
        # deletion is handled
        #
        for obj_id in self.objects:
            try:
                obj = model_context.proxy.indexed_ids[obj_id]
            except KeyError:
                continue
            try:
                row = model_context.proxy.index(obj)
            except ValueError:
                continue
            objects_to_remove.add(obj)
            #
            # If the object was valid, the header item should be updated
            # make sure all views know the validity of the row has changed
            #
            header_item = QtGui.QStandardItem()
            header_item.setData(py_to_variant(None), ObjectRole)
            header_item.setData(py_to_variant(u''), VerboseIdentifierRole)
            header_item.setData(py_to_variant(True), ValidRole)
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
        if (row is not None) or (rows != self.rows_in_view):
            # but updating the view is only needed if the rows changed
            yield from super(Deleted, self).model_run(model_context, mode)


class Filter(RowCount):

    name = 'filter'

    def __init__(self, action, old_value, new_value):
        super(Filter, self).__init__()
        self.action = action
        self.old_value = old_value
        self.new_value = new_value

    def model_run(self, model_context, mode):
        # comparison of old and new value can only happen in the model thread
        if self.old_value != self.new_value:
            model_context.proxy.filter(self.action, self.new_value)
        yield from super(Filter, self).model_run(model_context, mode)

    def __repr__(self):
        return '{0.__class__.__name__}(action={1})'.format(
            self,
            type(self.action).__name__
        )
    
    
class RowData(Update):

    name = 'row_data'

    def __init__(self):
        super(RowData, self).__init__(None)

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
        changed_ranges = []
        offset, limit = self.offset_and_limit_rows_to_get(rows)
        for obj in list(model_context.proxy[offset:offset+limit]):
            row = model_context.proxy.index(obj)
            changed_ranges.extend(self.add_data(model_context, row, columns, obj, True))
        yield action_steps.Update(changed_ranges)

            
    def __repr__(self):
        return '{0.__class__.__name__}'.format(self)

    
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
        yield action_steps.SetColumns(model_context.static_field_attributes)
        
        
class SetData(Update):

    name = 'set_data'

    def __init__(self, updates):
        super(SetData, self).__init__(None)
        # Copy the update requests and clear the list of requests
        self.updates = [u for u in updates]

    def __repr__(self):
        return '{0.__class__.__name__}([{1}])'.format(
            self,
            ', '.join(['(row={0}, column={1})'.format(row, column) for row, _o, column, _v in self.updates])
        )

    def model_run(self, model_context, mode):
        from camelot.view import action_steps
        created_objects = None
        updated_objects = None  
        changed_ranges = []
        grouped_requests = collections.defaultdict( list )
        updated_objects, created_objects, deleted_objects = set(), set(), set()
        for row, obj_id, column, value in self.updates:
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

                from sqlalchemy.exc import DatabaseError
                new_value = variant_to_py(value)
                logger.debug( 'set data for row %s;col %s' % ( row, column ) )

                old_value = getattr(obj, field_name )
                depending_objects_before_set = set(admin.get_depending_objects(obj))
                value_changed = ( new_value != old_value )
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
                # update the cache
                columns = tuple(range(len(model_context.static_field_attributes)))
                changed_ranges.extend(self.add_data(model_context, row, columns, obj, True))
                updated_objects.add(subsystem_obj)
                depending_objects = depending_objects_before_set.union(set(admin.get_depending_objects(obj)))
                for depending_object in depending_objects:
                    related_admin = admin.get_related_admin(type(depending_object))
                    if related_admin.is_deleted(depending_object):
                        deleted_objects.update({depending_object})
                    else:
                        updated_objects.update({depending_object})
        created_objects = tuple(created_objects)
        updated_objects = tuple(updated_objects)
        deleted_objects = tuple(deleted_objects)
        yield action_steps.SetData(changed_ranges, created_objects, updated_objects, deleted_objects)


class Sort(RowCount):

    name = 'sort'

    def model_run(self, model_context, mode):
        column, order = mode
        field_name = model_context.static_field_attributes[column]['field_name']
        model_context.proxy.sort(field_name, order!=Qt.SortOrder.AscendingOrder.value)
        yield from super(Sort, self).model_run(model_context, mode)

    def __repr__(self):
        return '{0.__class__.__name__}'.format(self)
