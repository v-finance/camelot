import itertools
import json
import logging
import unittest

from sqlalchemy import event
from sqlalchemy.engine import Engine

from camelot_example.fixtures import load_movie_fixtures
from .test_model import ExampleModelMixinCase, setup_session_name
from .test_proxy import A, C
from . import app_admin

from camelot.admin.action import Action
from camelot.admin.action.field_action import ClearObject, SelectObject
from camelot.admin.action.list_filter import Filter
from camelot.admin.application_admin import ApplicationAdmin
from camelot.admin.model_context import ObjectsModelContext
from camelot.core.item_model import (
    ActionRoutesRole, ActionStatesRole, CompletionPrefixRole,
    CompletionsRole, ObjectRole, ValidMessageRole, ValidRole,
    VerboseIdentifierRole, FocusPolicyRole, PrefixRole
)
from camelot.core.item_model.query_proxy import QueryModelProxy
from camelot.core.naming import initial_naming_context
from camelot.core.orm import Session
from camelot.core.qt import Qt, QtCore, delete, variant_to_py, is_deleted
from camelot.view.model_process import ModelProcess
from camelot.view.utils import get_settings_group
from camelot.model.party import Person
from camelot.test import RunningProcessCase, test_context
from camelot.core.cache import ValueCache
from camelot.view import action_steps
from camelot.core.backend import get_root_backend

LOGGER = logging.getLogger(__name__)
context_counter = itertools.count()


class ItemModelSignalRegister(QtCore.QObject):
    """Helper class to register the signals an QAbstractItemModel emits and
    analyze them"""
    
    def __init__(self, item_model):
        super(ItemModelSignalRegister, self).__init__()
        self.clear()
        item_model.headerDataChanged.connect(self.register_header_change)
        item_model.dataChanged.connect(self.register_data_change)
        item_model.layoutChanged.connect(self.register_layout_change)
        
    def clear( self ):
        self.data_changes = []
        self.header_changes = []
        self.layout_changes = 0

    #commented to solve an error: decorated slot has no signature compatible with dataChanged(QModelIndex,QModelIndex,QVector<int>)
    #@QtCore.qt_slot(QtCore.QModelIndex, QtCore.QModelIndex, "QVector<int>")
    def register_data_change(self, from_index, thru_index, vector):
        LOGGER.debug('dataChanged(row={0}, column={1})'.format(from_index.row(), from_index.column()))
        self.data_changes.append( ((from_index.row(), from_index.column()),
                                   (thru_index.row(), thru_index.column())) )

    @QtCore.qt_slot(Qt.Orientation, int, int)
    def register_header_change(self, orientation, first, last):
        self.header_changes.append((orientation, first, last))

    @QtCore.qt_slot()
    def register_layout_change(self):
        self.layout_changes += 1


class ValueCacheCase(unittest.TestCase):

    def test_changed_columns(self):
        cache = ValueCache(10)
        self.assertEqual(len(cache), 0)
        
        a = object()
        changed = cache.add_data(4, a, {1: 1, 2: 2, 3: 3})
        self.assertEqual(len(cache), 1)
        self.assertEqual(len(changed), 3)
        self.assertEqual(changed, {1, 2, 3})
        data = cache.get_data(4)
        self.assertEqual(len(data), 3)

        b = object()
        changed = cache.add_data(5, b, {1: 1, 2: 2, 3: 3, 4:4})
        self.assertEqual(len(cache), 2)
        self.assertEqual(len(changed), 4)
        data = cache.get_data(5)
        self.assertEqual(len(data), 4)

        changed = cache.add_data(4, a,  {1: 1, 2: 3, 3: 4})
        self.assertEqual(len(cache), 2)
        self.assertEqual(len(changed), 2)
        self.assertEqual(changed, {2, 3})
        data = cache.get_data(4)
        self.assertEqual(len(data), 3)

        changed = cache.add_data(4, a,  {4: 4,})
        self.assertEqual(len(cache), 2)
        self.assertEqual(len(changed), 1)
        self.assertEqual(changed, {4,})
        data = cache.get_data(4)
        self.assertEqual(len(data), 4)

    def test_limited_length(self):
        cache = ValueCache(10)
        self.assertEqual(len(cache), 0)
        for i in range(10):
            o = object()
            cache.add_data(i, o, {1: 1, 2: 2, 3: 3})
        self.assertEqual(len(cache), 10)
        cache.add_data(12, object(), {1: 1, 2: 3, 3: 4})
        self.assertEqual(len(cache), 10)


class ItemModelCaseMixin(object):
    """
    Helper methods to test a QAbstractItemModel
    """

    def _load_data(self, item_model):
        """Trigger the loading of data by the QAbstractItemModel"""
        item_model.submit()
        self.process()
        item_model.rowCount()
        item_model.submit()
        self.process()
        row_count = item_model.rowCount()
        column_count = item_model.columnCount()
        self.assertTrue(row_count > 0)
        for row in range(row_count):
            for col in range(column_count):
                self._data(row, col, item_model)
        item_model.submit()
        self.process()

    def _data(self, row, column, item_model, role=Qt.ItemDataRole.EditRole, validate_index=True):
        """Get data from the QAbstractItemModel"""
        index = item_model.index(row, column)
        if validate_index and not index.isValid():
            raise Exception('Index ({0},{1}) is not valid with {2} rows, {3} columns'.format(index.row(), index.column(), item_model.rowCount(), item_model.columnCount()))
        return item_model.data( index, role)
    
    def _set_data(self, row, column, value, item_model, role=Qt.ItemDataRole.EditRole, validate_index=True):
        """Set data to the QAbstractItemModel"""
        index = item_model.index( row, column )
        if validate_index and not index.isValid():
            raise Exception('Index ({0},{1}) is not valid with {2} rows, {3} columns'.format(index.row(), index.column(), item_model.rowCount(), item_model.columnCount()))
        result = item_model.setData( index, value, role )
        item_model.submit()
        self.process()
        item_model.submit()
        self.process()
        return result

    def _header_data(self, section, orientation, role, item_model):
        return item_model.headerData(section, orientation, role)

    def _flags(self, row, column, item_model):
        index = item_model.index( row, column )
        return item_model.flags(index)

    def _row_count(self, item_model):
        """Set data to the proxy"""
        item_model.rowCount()
        item_model.submit()
        self.process()
        return item_model.rowCount()

    def tear_down_item_model(self):
        if not is_deleted(self.qt_parent):
            delete(self.qt_parent)


class SetupProxy(Action):

    def model_run(self, model_context, mode):
        admin = app_admin.get_related_admin(A)
        proxy = admin.get_proxy([A(0), A(1), A(2)])
        model_context = ObjectsModelContext(admin, proxy, QtCore.QLocale())
        initial_naming_context.rebind(tuple(mode), model_context)
        id_collection = [id(a) for a in proxy.get_model()]
        created_collection = [a.created.second for a in proxy.get_model()]
        yield action_steps.UpdateProgress(
            text='Proxy setup', detail={
                'id_collection': id_collection,
                'created_collection': created_collection,
            }
        )

setup_proxy_name = test_context.bind(('setup_proxy',), SetupProxy())

class GetData(Action):

    def model_run(self, model_context, mode):
        index_in_collection, attribute, data_is_collection = mode
        collection = model_context.proxy.get_model()
        data = getattr(collection[index_in_collection], attribute)
        if data_is_collection:
            data = [e.value for e in data]
        yield action_steps.UpdateProgress(
            text='Got data', detail=data
        )

get_data_name = test_context.bind(('get_data',), GetData())

class SetData(Action):

    def model_run(self, model_context, mode):
        row, attribute, value = mode
        element = model_context.proxy.get_model()[row]
        setattr(element, attribute, value)
        yield action_steps.UpdateObjects((element,))
        yield action_steps.UpdateProgress(text='Data set')

set_data_name = test_context.bind(('set_data',), SetData())

class AddZ(Action):

    def model_run(self, model_context, mode):
        new_c = C(1)
        collection = model_context.proxy.get_model()
        collection[0].z.append(new_c)
        yield action_steps.CreateObjects((new_c,))

add_z_name = test_context.bind(('add_z',), AddZ())

class RemoveZ(Action):

    def model_run(self, model_context, mode):
        collection = model_context.proxy.get_model()
        old_c = collection[0].z.pop()
        yield action_steps.DeleteObjects((old_c,))

remove_z_name = test_context.bind(('remove_z',), RemoveZ())

class SwapElements(Action):

    def model_run(self, model_context, mode):
        collection = model_context.proxy.get_model()
        collection[0:2] = [collection[1], collection[0]]
        yield action_steps.UpdateProgress(text='Elements swapped')

swap_elements_name = test_context.bind(('swap_elements',), SwapElements())

class AddElement(Action):

    def model_run(self, model_context, mode):
        new_a = A(mode)
        collection = model_context.proxy.get_model()
        collection.append(new_a)
        yield action_steps.CreateObjects((new_a,))

add_element_name = test_context.bind(('add_element',), AddElement())

class RemoveElement(Action):

    def model_run(self, model_context, mode):
        collection = model_context.proxy.get_model()
        last_element = collection[-1]
        # emitting the deleted signal happens before the object is
        # deleted        
        yield action_steps.DeleteObjects((last_element,))
        # but removing an object should go through the item_model or there is no
        # way the item_model can be aware.        
        model_context.proxy.remove(last_element)
        yield action_steps.UpdateProgress(text='Element removed')

remove_element_name = test_context.bind(('remove_element',), RemoveElement())

class GetCollection(Action):

    def model_run(self, model_context, mode):
        name = initial_naming_context._bind_object((object(),))
        yield action_steps.UpdateProgress(
            text='Got data', detail=name
        )

get_collection_name = test_context.bind(('get_collection',), GetCollection())


class SetupQueryProxy(Action):

    def __init__(self, admin_cls):
        self.admin_cls = admin_cls

    def model_run(self, model_context, mode):
        session = Session()
        admin = self.admin_cls(app_admin, Person)
        proxy = QueryModelProxy(session.query(Person))
        model_context = ObjectsModelContext(admin, proxy, QtCore.QLocale())
        initial_naming_context.rebind(tuple(mode), model_context)
        yield action_steps.UpdateProgress(detail='Proxy setup')

setup_query_proxy_name = test_context.bind(('setup_query_proxy',), SetupQueryProxy(admin_cls=Person.Admin))

class EqualColumnAdmin(Person.Admin):
    list_display = ['first_name', 'suffix']
    # begin column width
    field_attributes = {
        'first_name':{'column_width':8},
        'suffix':{'column_width':8},
    }
    # end column width

setup_query_proxy_equal_columns_name = test_context.bind(('setup_query_proxy_equal_columns',), SetupQueryProxy(admin_cls=EqualColumnAdmin))

class SmallColumnsAdmin( Person.Admin ):
    list_display = ['first_name', 'suffix']

setup_query_proxy_small_columns_name = test_context.bind(('setup_query_proxy_small_columns',), SetupQueryProxy(admin_cls=SmallColumnsAdmin))

class ApplyFilter(Action):

    def model_run(self, model_context, mode):

        class SingleItemFilter(Filter):
        
            def decorate_query(self, query, values):
                return query.filter_by(id=values)

        model_context.proxy.filter(SingleItemFilter(Person.id), 1)
        yield action_steps.UpdateProgress(detail='Filter applied')

apply_filter_name = test_context.bind(('apply_filter',), ApplyFilter())

class InsertObject(Action):


    def model_run(self, model_context, persons_name):
        person = Person()
        count = len(model_context.proxy)
        model_context.proxy.append(person)
        assert model_context.proxy.index(person)==count
        yield action_steps.CreateObjects((person,))
        yield action_steps.UpdateProgress(text='Object inserted', detail=id(person))

insert_object_name = test_context.bind(('insert_object',), InsertObject())

class GetEntityData(Action):

    def model_run(self, model_context, mode):
        primary_key, attribute = mode
        entity = model_context.session.query(Person).get(primary_key)
        data = getattr(entity, attribute)
        yield action_steps.UpdateProgress(
            text='Got enity data', detail=data
        )

get_entity_data_name = test_context.bind(('get_entity_data',), GetEntityData())

class StartQueryCounter(Action):

    @staticmethod
    def increase_query_counter(conn, cursor, statement, parameters, context, executemany):
        current_count = test_context.resolve(('current_query_count',))
        current_count = current_count + 1
        LOGGER.debug('Counted query {} : {}'.format(
            current_count, str(statement)
        ))
        test_context.rebind(('current_query_count',), current_count)

    def model_run(self, model_context, mode):
        test_context.rebind(('current_query_count',), 0)
        event.listen(Engine, 'after_cursor_execute', self.increase_query_counter)
        yield action_steps.UpdateProgress(text='Started query counter')

test_context.bind(('current_query_count',), 0)
start_query_counter_name = test_context.bind(('start_query_counter',), StartQueryCounter())

class StopQueryCounter(Action):

    def model_run(self, model_context, mode):
        current_count = test_context.resolve(('current_query_count',))
        event.remove(Engine, 'after_cursor_execute', StartQueryCounter.increase_query_counter)
        yield action_steps.UpdateProgress(
            text='Stopped query counter', detail=current_count
        )

stop_query_counter_name = test_context.bind(('stop_query_counter',), StopQueryCounter())


class ExampleItemModelProcess(ModelProcess):

    def initialize(self):
        initial_naming_context.bind('test', test_context)
        engine = ExampleModelMixinCase.setup_sample_model()
        load_movie_fixtures(engine)


class ItemModelCase(RunningProcessCase, ItemModelCaseMixin):
    """
    Item model tests to be run both with a thread and with a process
    """

    process_cls = ExampleItemModelProcess

    def setUp(self):
        super().setUp()
        self.model_context_name = ('test_item_model_thread_model_context_{0}'.format(next(context_counter)),)
        for step in self.gui_run(setup_proxy_name, mode=self.model_context_name):
            if step[0] == action_steps.UpdateProgress.__name__:
                detail = step[1]['detail']
                self.id_collection = detail['id_collection']
                self.created_collection = detail['created_collection']
        self.app_admin = ApplicationAdmin()
        self.admin = self.app_admin.get_related_admin(A)
        self.admin_route = self.admin.get_admin_route()
        self.qt_parent = QtCore.QObject()
        self.item_model = get_root_backend().create_model(get_settings_group(self.admin_route), self.qt_parent)
        self.item_model.setValue(self.model_context_name)
        self.columns = self.admin.list_display
        self.item_model.setColumns(self.columns)
        self.process()
        self.signal_register = ItemModelSignalRegister(self.item_model)

    def tearDown(self):
        self.tear_down_item_model()
        super().tearDown()

    def get_data(self, index_in_collection, attribute, data_is_collection):
        """
        Get the data from the collection without going through the item model
        """
        for step in self.gui_run(
            get_data_name,
            mode=(index_in_collection, attribute, data_is_collection),
            model_context_name=self.model_context_name):
            if step[0] == action_steps.UpdateProgress.__name__:
                return step[1]['detail']

    def get_collection(self):
        """
        Create a collection in the remote process and return the bound
        name of that collection.
        """
        for step in self.gui_run(
            get_collection_name,
            model_context_name=self.model_context_name):
            if step[0] == action_steps.UpdateProgress.__name__:
                return tuple(step[1]['detail'])

    def test_invalid_item(self):
        invalid_item = self.item_model.invalidItem()
        self.assertEqual(invalid_item.data(Qt.ItemDataRole.EditRole), None)
        self.assertEqual(bool(invalid_item.flags() & Qt.ItemFlag.ItemIsEditable), False)
        self.assertEqual(Qt.FocusPolicy(invalid_item.data(FocusPolicyRole)), Qt.FocusPolicy.NoFocus)
        invalid_clone = invalid_item.clone()
        self.assertEqual(invalid_clone.data(Qt.ItemDataRole.EditRole), None)
        self.assertEqual(bool(invalid_clone.flags() & Qt.ItemFlag.ItemIsEditable), False)
        self.assertEqual(Qt.FocusPolicy(invalid_clone.data(FocusPolicyRole)), Qt.FocusPolicy.NoFocus)

    def test_change_column_width(self):
        self.process()
        self.item_model.setHeaderData(1, Qt.Orientation.Horizontal, QtCore.QSize(140,10),
                                 Qt.ItemDataRole.SizeHintRole)
        size_hint = self.item_model.headerData(1, Qt.Orientation.Horizontal, Qt.ItemDataRole.SizeHintRole)
        self.assertEqual(size_hint.width(), 140)

    def test_rowcount(self):
        # the rowcount remains 0 while no timeout has passed
        # self.assertEqual(self.item_model.rowCount(), 0)
        self.process()
        self.assertEqual(self.item_model.rowCount(), 3)

    def test_first_columns(self):
        # when data is loaded for column 0, it remains loading for column 1
        self.assertTrue(self._row_count(self.item_model) > 1)
        self.assertEqual(self._data(1, 0, self.item_model, role=Qt.ItemDataRole.EditRole), None)
        self.process()
        self.assertEqual(self._data(1, 0, self.item_model, role=Qt.ItemDataRole.EditRole), 1)
        self.assertEqual(self._data(1, 1, self.item_model, role=Qt.ItemDataRole.EditRole), None)
        self.process()
        self.assertEqual(self._data(1, 0, self.item_model, role=Qt.ItemDataRole.EditRole), 1)
        self.assertEqual(self._data(1, 1, self.item_model, role=Qt.ItemDataRole.EditRole), 0)

    def test_last_columns(self):
        # when data is loaded for column 1, it remains loading for column 0
        self.assertTrue(self._row_count(self.item_model) > 1)
        self.assertEqual(self._data(1, 1, self.item_model, role=Qt.ItemDataRole.EditRole), None)
        self.process()
        self.assertEqual(self._data(1, 1, self.item_model, role=Qt.ItemDataRole.EditRole), 0)
        self.assertEqual(self._data(1, 0, self.item_model, role=Qt.ItemDataRole.EditRole), None)
        self.process()
        self.assertEqual(self._data(1, 1, self.item_model, role=Qt.ItemDataRole.EditRole), 0)
        self.assertEqual(self._data(1, 0, self.item_model, role=Qt.ItemDataRole.EditRole), 1)

    def test_flags(self):
        self._load_data(self.item_model)
        flags = self._flags(1, 1, self.item_model)
        self.assertTrue(flags & Qt.ItemFlag.ItemIsEditable)
        self.assertTrue(flags & Qt.ItemFlag.ItemIsEnabled)
        self.assertTrue(flags & Qt.ItemFlag.ItemIsSelectable)

    def test_sort( self ):
        self.item_model.sort( 0, Qt.SortOrder.AscendingOrder )
        # check the sorting
        self._load_data(self.item_model)
        row_0 = self._data( 0, 0, self.item_model )
        row_1 = self._data( 1, 0, self.item_model )
        LOGGER.debug('row 0 : {0}, row 1 : {1}'.format(row_0, row_1))
        self.assertTrue( row_1 > row_0 )
        self.item_model.sort( 0, Qt.SortOrder.DescendingOrder )
        # check the sorting
        self._load_data(self.item_model)
        row_0 = self._data( 0, 0, self.item_model )
        row_1 = self._data( 1, 0, self.item_model )
        LOGGER.debug('row 0 : {0}, row 1 : {1}'.format(row_0, row_1))
        self.assertTrue( row_1 < row_0 )

    def test_vertical_header_data(self):
        row_count = self._row_count(self.item_model)
        # before the data is loaded, nothing is available, except the sizehint
        self.assertTrue(row_count)
        for row in range(row_count):
            self.assertEqual(self._header_data(row, Qt.Orientation.Vertical, Qt.ItemDataRole.ToolTipRole, self.item_model), None)
            self.assertEqual(self._header_data(row, Qt.Orientation.Vertical, ObjectRole, self.item_model), None)
            self.assertEqual(self._header_data(row, Qt.Orientation.Vertical, Qt.ItemDataRole.DisplayRole, self.item_model), None)
            self.assertEqual(self._header_data(row, Qt.Orientation.Vertical, Qt.ItemDataRole.DecorationRole, self.item_model), None)
            self.assertEqual(self._header_data(row, Qt.Orientation.Vertical, VerboseIdentifierRole, self.item_model), None)
            self.assertEqual(self._header_data(row, Qt.Orientation.Vertical, Qt.ItemDataRole.SizeHintRole, self.item_model), self.item_model.verticalHeaderSize())
            self.assertEqual(self._header_data(row, Qt.Orientation.Vertical, ValidRole, self.item_model), None)
            self.assertEqual(self._header_data(row, Qt.Orientation.Vertical, ValidMessageRole, self.item_model), None)
            # Make sure to also request at least one column
            self._data(row, 0, self.item_model)
        self.process()
        # after the timeout, the data is available
        for row in range(row_count):
            self.assertIn('Open', self._header_data(row, Qt.Orientation.Vertical, Qt.ItemDataRole.ToolTipRole, self.item_model))
            # dont display any data if there is a decoration, otherwise
            # both are displayed mixed
            self.assertEqual(self._header_data(row, Qt.Orientation.Vertical, Qt.ItemDataRole.DisplayRole, self.item_model), '')
            self.assertTrue(self._header_data(row, Qt.Orientation.Vertical, Qt.ItemDataRole.DecorationRole, self.item_model))
            self.assertEqual(self._header_data(row, Qt.Orientation.Vertical, ObjectRole, self.item_model), self.id_collection[row])
            self.assertEqual(self._header_data(row, Qt.Orientation.Vertical, VerboseIdentifierRole, self.item_model), 'A : {0}'.format(row))
            self.assertEqual(self._header_data(row, Qt.Orientation.Vertical, Qt.ItemDataRole.SizeHintRole, self.item_model), self.item_model.verticalHeaderSize())
            self.assertEqual(self._header_data(row, Qt.Orientation.Vertical, ValidRole, self.item_model), True)
            self.assertEqual(self._header_data(row, Qt.Orientation.Vertical, ValidMessageRole, self.item_model), None)
        # when changing an object, it might become invalid after a timeout
        self.signal_register.clear()
        self.gui_run(
            set_data_name, mode=(1, 'y', None),
            model_context_name=self.model_context_name
        )
        self.process()
        self.assertEqual(self._header_data(1, Qt.Orientation.Vertical, ValidRole, self.item_model), False)
        self.assertEqual(self._header_data(1, Qt.Orientation.Vertical, ValidMessageRole, self.item_model), 'Y is a required field')
        self.assertEqual(len(self.signal_register.header_changes), 1)

    def test_data(self):
        # the data remains None and not editable while no timeout has passed
        self.assertTrue(self._row_count(self.item_model) > 1)
        self.assertEqual(self._data(1, 0, self.item_model, role=Qt.ItemDataRole.EditRole), None)
        self.assertEqual(self._data(1, 0, self.item_model, role=Qt.ItemDataRole.DisplayRole), None)
        self.assertEqual(self._data(1, 0, self.item_model, role=ObjectRole), None)
        self.assertEqual(bool(self._flags(1, 0, self.item_model) & Qt.ItemFlag.ItemIsEditable), False)
        # why would there be a need to get static fa before the timout has passed ?
        #self.assertEqual(self._data(1, 0, role=FieldAttributesRole)['static'], 'static')
        self.assertEqual(self._data(1, 0, self.item_model, role=PrefixRole), None)
        self.assertEqual(self._data(1, 4, self.item_model, role=ActionStatesRole), "[]")
        self._data(1, 2, self.item_model)
        self._data(1, 3, self.item_model)
        self._data(1, 4, self.item_model)
        self.process()
        self.assertEqual(self._data(1, 0, self.item_model, role=Qt.ItemDataRole.EditRole), 1)
        # the prefix is prepended to the display role
        self.assertEqual(self._data(1, 0, self.item_model, role=Qt.ItemDataRole.DisplayRole), 'pre 1')
        self.assertEqual(self._data(1, 0, self.item_model, role=ObjectRole), self.id_collection[1])
        self.assertEqual(bool(self._flags(1, 0, self.item_model) & Qt.ItemFlag.ItemIsEditable), True)
        #self.assertEqual(self._data(1, 0, self.item_model, role=FieldAttributesRole)['static'], 'static')
        self.assertEqual(self._data(1, 0, self.item_model, role=PrefixRole), 'pre')
        self.assertEqual(self._data(1, 0, self.item_model, role=Qt.ItemDataRole.ToolTipRole), 'Hint')
        self.assertEqual(self._data(1, 0, self.item_model, role=Qt.ItemDataRole.BackgroundRole).name(), '#ff0000')
        self.assertEqual(len(json.loads(self._data(1, 4, self.item_model, role=ActionStatesRole))), 2)
        self._data(1, 4, self.item_model, role=ActionRoutesRole)
        self.assertEqual(json.loads(self._data(1, 4, self.item_model, role=ActionStatesRole))[0]['tooltip'], SelectObject.tooltip)
        self.assertEqual(json.loads(self._data(1, 4, self.item_model, role=ActionStatesRole))[0]['icon']['name'], SelectObject.icon.name)
        self.assertEqual(json.loads(self._data(1, 4, self.item_model, role=ActionStatesRole))[1]['tooltip'], ClearObject.tooltip)
        self.assertEqual(json.loads(self._data(1, 4, self.item_model, role=ActionStatesRole))[1]['icon']['name'], ClearObject.icon.name)
        self.assertTrue(isinstance(self._data(1, 2, self.item_model), list))
        self.assertEqual(self._data(1, 2, self.item_model)[0], 'model_context')
        self.assertEqual(variant_to_py(self._data(1, 3, self.item_model)).second, self.created_collection[1])
        
        self.assertEqual(self._data(-1, -1, self.item_model, role=ObjectRole, validate_index=False), None)
        self.assertEqual(self._data(100, 100, self.item_model, role=ObjectRole, validate_index=False), None)
        self.assertEqual(bool(self._flags(-1, -1, self.item_model) & Qt.ItemFlag.ItemIsEditable), False)
        self.assertEqual(bool(self._flags(100, 100, self.item_model) & Qt.ItemFlag.ItemIsEditable), False)
        self.assertEqual(Qt.FocusPolicy(self._data(-1, -1, self.item_model, role=FocusPolicyRole, validate_index=False)), Qt.FocusPolicy.NoFocus)
        self.assertEqual(Qt.FocusPolicy(self._data(100, 100, self.item_model, role=FocusPolicyRole, validate_index=False)), Qt.FocusPolicy.NoFocus)

    def test_list_attribute(self):
        # when the data method of a CrudItemModel returns a list, manipulations
        # on this list should be reflected in the original list
        self._load_data(self.item_model)
        attribute_model_context_name = self._data(0, 2, self.item_model)
        attribute_item_model = get_root_backend().create_model(get_settings_group(self.admin_route), self.qt_parent)
        attribute_item_model.setValue(attribute_model_context_name)
        attribute_item_model.setColumns(['value'])
        self._load_data(attribute_item_model)
        self.assertEqual(attribute_item_model.rowCount(), 2)
        self.assertNotIn(1, self.get_data(0, 'z', True))
        # manipulate the returned list, and see if the original is manipulated
        # as well
        self.gui_run(add_z_name, model_context_name=self.model_context_name)
        self.process()
        self.assertEqual(attribute_item_model.rowCount(), 3)
        self._load_data(attribute_item_model)
        self.assertIn(1, self.get_data(0, 'z', True))
        self.gui_run(remove_z_name, model_context_name=self.model_context_name)
        self.assertNotIn(1, self.get_data(0, 'z', True))
        # @todo : this only works when a load data has happend after the
        #         rowCount increased, which seems not really the desired effect
        self.assertEqual(attribute_item_model.rowCount(), 3)

    def test_set_data(self):
        # the set data is done after the timeout has passed
        # and happens in the requested order
        self._load_data(self.item_model)
        self._set_data(0, 0, 20, self.item_model)
        self._set_data(0, 1, 10, self.item_model)
        # x is set first, so y becomes not
        # editable and remains at its value
        self.assertEqual(self._data(0, 0, self.item_model), 20)
        self.assertEqual(self._data(0, 1, self.item_model),  0)
        self._set_data(0, 0, 5, self.item_model)
        self._set_data(0, 1, 10, self.item_model)
        # x is set first, so y becomes
        # editable and its value is changed
        self.assertEqual(self._data(0, 0, self.item_model), 5)
        self.assertEqual(self._data(0, 1, self.item_model), 10)
        self._set_data(0, 1, 15, self.item_model)
        self._set_data(0, 0, 20, self.item_model)
        # x is set last, so y stays
        # editable and its value is changed
        self.assertEqual(self._data(0, 0, self.item_model), 20)
        self.assertEqual(self._data(0, 1, self.item_model), 15)

    def test_dynamic_editable(self):
        # If the editable field attribute of one field depends on the value
        # of another field, 'editable' should be reevaluated after the
        # other field is set
        # get the data once, to fill the cached values of the field attributes
        # so changes get passed the first check
        self._load_data(self.item_model)
        self.assertEqual(self.get_data(0, 'y', False), 0)
        self.assertEqual(self._data(0, 1, self.item_model), 0)
        # initialy, field is editable
        self._set_data(0, 1, 1, self.item_model)
        self.assertEqual(self.get_data(0, 'y', False), 1)
        self._set_data(0, 0, 11, self.item_model)
        self._set_data(0, 1, 0, self.item_model)
        self.process()
        self.assertEqual(self.get_data(0, 'y', False), 1)

    def test_modify_list_while_editing( self ):
        self._load_data(self.item_model)
        self.assertEqual(self.get_data(0, 'x', False), 0)
        self.assertEqual(self._data( 0, 0, self.item_model), 0)
        # switch first and second person in collection without informing
        # the item_model
        self.gui_run(swap_elements_name, model_context_name=self.model_context_name)
        self.assertEqual(self.get_data(0, 'x', False), 1)
        self.assertEqual(self.get_data(1, 'x', False), 0)
        self.assertEqual(self._data( 0, 0, self.item_model), 0)
        self.assertEqual(self._data( 1, 0, self.item_model), 1)
        # now change the data
        self._set_data(0, 0, 7, self.item_model)
        self.assertEqual(self._data(0, 0, self.item_model), 7)
        self.assertEqual(self.get_data(1, 'x', False), 7)

    def test_delete_after_set_data( self ):
        # the item  model is deleted after data has been set,
        # like in closing a form immediately after changing a field
        self.assertEqual(self.get_data(0, 'x', False), 0)
        self._load_data(self.item_model)
        self.assertEqual(self._data(0, 0, self.item_model), 0)
        self._set_data(0, 0, 10, self.item_model)
        delete(self.qt_parent)
        self.assertEqual(self.get_data(0, 'x', False), 10)

    def test_data_changed( self ):
        # verify the data changed signal is only received for changed
        # index ranges
        self._load_data(self.item_model)
        self.assertEqual(self.item_model.rowCount(), 3)
        self.assertEqual(self._data(0, 0, self.item_model), 0)
        self.assertEqual(self._data(1, 0, self.item_model), 1)
        self.assertEqual(self._data(2, 0, self.item_model), 2)
        self.signal_register.clear()
        self._set_data( 0, 0, 8, self.item_model )
        self.assertEqual( len(self.signal_register.data_changes), 1 )
        for changed_range in self.signal_register.data_changes:
            for index in changed_range:
                row, col = index
                self.assertEqual( row, 0 )
                self.assertEqual( col, 0 )

    def test_objects_updated(self):
        # modify only one column to test if only one change is emitted
        self._load_data(self.item_model)
        self.signal_register.clear()
        self.gui_run(
            set_data_name, mode=(0, 'y', 10),
            model_context_name=self.model_context_name
        )
        self.process()
        self.assertEqual( len(self.signal_register.data_changes), 1 )
        self.assertEqual( self.signal_register.data_changes[0],
                          ((0, 1), (0, 1)) )

    def test_unloaded_objects_updated(self):
        # only load data for a single column
        self.assertTrue(self._row_count(self.item_model) > 1)
        self._data(0, 1, self.item_model)
        self.process()
        self.assertEqual(self._data(0, 1, self.item_model, role=Qt.ItemDataRole.EditRole), 0)
        # modify two columns to test if only a change for the loaded
        # column is emitted
        self.signal_register.clear()
        self.gui_run(
            set_data_name, mode=(0, 'x', 9),
            model_context_name=self.model_context_name
        )
        self.gui_run(
            set_data_name, mode=(0, 'y', 10),
            model_context_name=self.model_context_name
        )
        self.process()
        self.assertEqual( len(self.signal_register.data_changes), 1 )
        self.assertEqual( self.signal_register.data_changes[0],
                          ((0, 1), (0, 1)) )

    def test_objects_created(self):
        self._load_data(self.item_model)
        row_count = self.item_model.rowCount()
        self.signal_register.clear()
        self.gui_run(add_element_name, model_context_name=self.model_context_name, mode=43)
        self.process()
        self.assertEqual(len(self.signal_register.header_changes), 1)
        new_row_count = self.item_model.rowCount()
        self.assertEqual(new_row_count, row_count+1)

    def test_objects_deleted(self):
        self._load_data(self.item_model)
        row_count = self.item_model.rowCount()
        self.assertEqual(self._data(0, 0, self.item_model), 0)
        self.signal_register.clear()
        self.gui_run(remove_element_name, model_context_name=self.model_context_name)
        # but the timeout might be after the object was deleted
        self.process()
        self.assertEqual(self.signal_register.layout_changes, 1)
        new_row_count = self.item_model.rowCount()
        self.assertEqual(new_row_count, row_count-1)
        # after the delete, all data is cleared
        self.assertEqual(self._data(0, 0, self.item_model), None)
        self.process()
        self.assertEqual(self._data(0, 0, self.item_model), 0)

    def test_no_objects_updated(self):
        self._load_data(self.item_model)
        self.signal_register.clear()
        self.item_model.objectsUpdated(list(self.get_collection()))
        self.process()
        self.assertEqual( len(self.signal_register.data_changes), 0 )
        self.assertEqual( len(self.signal_register.header_changes), 0 )
        self.assertEqual( self.signal_register.layout_changes, 0 )

    def test_no_objects_created(self):
        self._load_data(self.item_model)
        self.signal_register.clear()
        self.item_model.objectsCreated(list(self.get_collection()))
        self.process()
        self.assertEqual( len(self.signal_register.data_changes), 0 )
        self.assertEqual( len(self.signal_register.header_changes), 0 )
        self.assertEqual( self.signal_register.layout_changes, 0 )

    def test_no_objects_deleted(self):
        self._load_data(self.item_model)
        self.signal_register.clear()
        self.item_model.objectsDeleted(list(self.get_collection()))
        self.process()
        self.assertEqual( len(self.signal_register.data_changes), 0 )
        self.assertEqual( len(self.signal_register.header_changes), 0 )
        self.assertEqual( self.signal_register.layout_changes, 0 )

    def test_completion(self):
        self._load_data(self.item_model)
        name = self._data(0, 4, self.item_model, role=Qt.ItemDataRole.EditRole)
        # the edit role should be a name
        self.assertIsInstance(name, list)
        self.assertTrue(len(name) > 1)
        self.assertIsNone(self._data(0, 4, self.item_model, role=CompletionsRole))
        self._set_data(0, 4, 'v', self.item_model, role=CompletionPrefixRole)
        self.assertIsNotNone(self._data(0, 4, self.item_model, role=CompletionsRole))


class QueryQStandardItemModelMixinCase(ItemModelCaseMixin):
    """
    methods to setup a QStandardItemModel representing a query
    """

    def setup_item_model(self, admin_route, admin_name):
        self.qt_parent = QtCore.QObject()
        self.item_model = get_root_backend().create_model(get_settings_group(admin_route), self.qt_parent)
        self.item_model.setValue(self.model_context_name)
        self.columns = ('first_name', 'last_name', 'id',)
        self.item_model.setColumns(self.columns)
        self.item_model.submit()


class QueryQStandardItemModelCase(
    RunningProcessCase,
    QueryQStandardItemModelMixinCase, ExampleModelMixinCase):
    """Test the functionality of A QStandardItemModel
    representing a query
    """

    process_cls = ExampleItemModelProcess

    def setUp(self):
        super().setUp()
        self.model_context_name = ('test_query_item_model_model_context_{0}'.format(next(context_counter)),)
        self.gui_run(setup_session_name, mode=True)
        self.gui_run(setup_query_proxy_name, mode=self.model_context_name)
        self.app_admin = ApplicationAdmin()
        self.person_admin = self.app_admin.get_related_admin(Person)
        self.process()
        self.admin_route = self.person_admin.get_admin_route()
        self.setup_item_model(self.admin_route, self.person_admin.get_name())
        self.process()

    def get_data(self, primary_key, attribute):
        """
        Get the data from the collection without going through the item model
        """
        for step in self.gui_run(
            get_entity_data_name,
            mode=(primary_key, attribute),
            model_context_name=self.model_context_name):
            if step[0] == action_steps.UpdateProgress.__name__:
                return step[1]['detail']

    def test_insert_after_sort(self):
        self.item_model.submit()
        self.assertTrue( self.item_model.columnCount() > 0 )
        self.item_model.sort( 1, Qt.SortOrder.AscendingOrder )
        # check the query
        self.assertTrue( self.item_model.columnCount() > 0 )
        rowcount = self._row_count(self.item_model)
        self.assertGreater(rowcount, 1)
        # check the sorting
        self._load_data(self.item_model)
        self.item_model.submit()
        self.process()
        data0 = self._data( 0, 1, self.item_model )
        data1 = self._data( 1, 1, self.item_model )
        self.assertGreater(data1, data0)
        self.item_model.sort( 1, Qt.SortOrder.DescendingOrder )
        self._load_data(self.item_model)
        data0 = self._data( 0, 1, self.item_model )
        data1 = self._data( 1, 1, self.item_model )
        self.assertGreater(data0, data1)
        # insert a new object
        person_id = None
        for step in self.gui_run(insert_object_name, model_context_name=self.model_context_name):
            if step[0] == action_steps.UpdateProgress.__name__:
                person_id = step[1]['detail']
        self.assertTrue(person_id)
        self.item_model.submit()
        self.process()
        new_rowcount = self.item_model.rowCount()
        self.assertEqual(new_rowcount, rowcount + 1)
        new_row = new_rowcount - 1
        # fill in the required fields
        self.assertEqual( self._data( new_row, 0, self.item_model ), None )
        self.assertEqual( self._data( new_row, 1, self.item_model ), None )
        self.assertFalse( self._data( new_row, 2, self.item_model ) )
        self._set_data( new_row, 0, 'Foo', self.item_model )
        self.assertFalse( self._data( new_row, 2, self.item_model ) )
        self._set_data( new_row, 1, 'Bar', self.item_model )
        self.assertTrue( self._data( new_row, 2, self.item_model ) )
        primary_key =  self._data( new_row, 2, self.item_model )
        self.assertEqual( self.get_data(primary_key, 'first_name'), 'Foo')
        self.assertEqual( self.get_data(primary_key, 'last_name'), 'Bar')
        self._load_data(self.item_model)
        self.assertEqual( self._data( new_row, 0, self.item_model ), 'Foo' )
        self.assertEqual( self._data( new_row, 1, self.item_model ), 'Bar' )
        # get the object at the new row (eg, to display a form view)
        self.assertEqual(self._header_data(new_row, Qt.Orientation.Vertical, ObjectRole, self.item_model), person_id)

    def test_single_query(self):
        # after constructing a queryproxy, 4 queries are issued
        # before data is returned : 
        # - count query
        # - person query
        # - contact mechanism select in load
        # - address select in load
        # those last 2 are needed for the validation of the compounding objects
        self.gui_run(apply_filter_name, model_context_name=self.model_context_name)
        self.gui_run(start_query_counter_name)
        item_model = get_root_backend().create_model(get_settings_group(self.admin_route), self.qt_parent)
        item_model.setValue(self.model_context_name)
        item_model.setColumns(self.columns)
        self._load_data(item_model)
        self.assertEqual(item_model.columnCount(), 3)
        self.assertEqual(item_model.rowCount(), 1)
        for step in self.gui_run(stop_query_counter_name):
            if step[0] == action_steps.UpdateProgress.__name__:
                query_count = step[1]['detail']
        self.assertEqual(query_count, 4)
