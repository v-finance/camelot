import logging
import unittest

from camelot.admin.application_admin import ApplicationAdmin
from camelot.admin.action.list_filter import Filter
from camelot.admin.view_register import ViewRegister
from camelot.core.qt import variant_to_py, QtCore, Qt, py_to_variant, delete
from camelot.model.party import Person
from camelot.view.item_model.cache import ValueCache
from camelot.view.proxy.collection_proxy import (
    CollectionProxy, invalid_item)
from camelot.core.item_model import (FieldAttributesRole, ObjectRole,
    VerboseIdentifierRole, ValidRole, ValidMessageRole, AbstractModelProxy,
    CompletionsRole, CompletionPrefixRole
)
from camelot.core.item_model.query_proxy import QueryModelProxy
from camelot.test import RunningThreadCase, RunningProcessCase

from sqlalchemy import event
from sqlalchemy.engine import Engine

from .test_model import ExampleModelMixinCase
from .test_proxy import A, B

LOGGER = logging.getLogger(__name__)


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

    @QtCore.qt_slot(QtCore.QModelIndex, QtCore.QModelIndex, "QVector<int>")
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
        item_model.timeout_slot()
        self.process()
        item_model.rowCount()
        item_model.timeout_slot()
        self.process()
        row_count = item_model.rowCount()
        column_count = item_model.columnCount()
        self.assertTrue(row_count > 0)
        for row in range(row_count):
            for col in range(column_count):
                self._data(row, col, item_model)
        item_model.timeout_slot()
        self.process()

    def _data(self, row, column, item_model, role=Qt.EditRole, validate_index=True):
        """Get data from the QAbstractItemModel"""
        index = item_model.index(row, column)
        if validate_index and not index.isValid():
            raise Exception('Index ({0},{1}) is not valid with {2} rows, {3} columns'.format(index.row(), index.column(), item_model.rowCount(), item_model.columnCount()))
        return variant_to_py(item_model.data( index, role))
    
    def _set_data(self, row, column, value, item_model, role=Qt.EditRole, validate_index=True):
        """Set data to the QAbstractItemModel"""
        index = item_model.index( row, column )
        if validate_index and not index.isValid():
            raise Exception('Index ({0},{1}) is not valid with {2} rows, {3} columns'.format(index.row(), index.column(), item_model.rowCount(), item_model.columnCount()))
        return item_model.setData( index, py_to_variant(value), role )

    def _header_data(self, section, orientation, role, item_model):
        return variant_to_py(item_model.headerData(section, orientation, role))

    def _flags(self, row, column, item_model):
        index = item_model.index( row, column )
        return item_model.flags(index)

    def _row_count(self, item_model):
        """Set data to the proxy"""
        item_model.rowCount()
        item_model.timeout_slot()
        self.process()
        return item_model.rowCount()

class ItemModelTests(object):
    """
    Item model tests to be run both with a thread and with a process
    """

    def test_invalid_item(self):
        self.assertEqual(variant_to_py(invalid_item.data(Qt.EditRole)), None)
        self.assertEqual(variant_to_py(invalid_item.data(FieldAttributesRole)), {'editable': False, 'focus_policy': 0})
        invalid_clone = invalid_item.clone()
        self.assertEqual(variant_to_py(invalid_clone.data(Qt.EditRole)), None)
        self.assertEqual(variant_to_py(invalid_clone.data(FieldAttributesRole)), {'editable': False, 'focus_policy': 0})


class ItemModelProcessCase(RunningProcessCase, ItemModelCaseMixin, ItemModelTests):
    pass


class ItemModelThreadCase(RunningThreadCase, ItemModelCaseMixin, ItemModelTests):

    def setUp( self ):
        super(ItemModelThreadCase, self).setUp()
        self.A = A
        self.collection = [A(0), A(1), A(2)]
        self.app_admin = ApplicationAdmin()
        self.admin = self.app_admin.get_related_admin(A)
        self.admin_route = ViewRegister.register_admin_route(self.admin)
        self.item_model = CollectionProxy(self.admin_route, self.admin.get_name())
        self.item_model.set_value(self.admin.get_proxy(self.collection))
        self.columns = self.admin.list_display
        list(self.item_model.add_columns(self.columns))
        self.item_model.timeout_slot()
        self.process()
        self.signal_register = ItemModelSignalRegister(self.item_model)

    def tearDown(self):
        super().tearDown()
        ViewRegister.unregister_view(self.admin_route)

    def test_rowcount(self):
        # the rowcount remains 0 while no timeout has passed
        self.assertEqual(self.item_model.rowCount(), 0)
        self.process()
        self.assertEqual(self.item_model.rowCount(), 0)
        self.item_model.timeout_slot()
        self.process()
        self.assertEqual(self.item_model.rowCount(), 3)

    def test_data(self):
        # the data remains None and not editable while no timeout has passed
        self.assertTrue(self._row_count(self.item_model) > 1)
        self.assertEqual(self._data(1, 0, self.item_model, role=Qt.EditRole), None)
        self.assertEqual(self._data(1, 0, self.item_model, role=Qt.DisplayRole), None)
        self.assertEqual(self._data(1, 0, self.item_model, role=ObjectRole), None)
        self.assertEqual(self._data(1, 0, self.item_model, role=FieldAttributesRole).get('editable'), False)
        # why would there be a need to get static fa before the timout has passed ?
        #self.assertEqual(self._data(1, 0, role=FieldAttributesRole)['static'], 'static')
        self.assertEqual(self._data(1, 0, self.item_model, role=FieldAttributesRole).get('prefix'), None)
        self._data(1, 2, self.item_model)
        self._data(1, 3, self.item_model)
        self.item_model.timeout_slot()
        self.process()
        self.assertEqual(self._data(1, 0, self.item_model, role=Qt.EditRole), 1)
        # the prefix is prepended to the display role
        self.assertEqual(self._data(1, 0, self.item_model, role=Qt.DisplayRole), 'pre 1')
        self.assertEqual(self._data(1, 0, self.item_model, role=ObjectRole), self.collection[1])
        self.assertEqual(self._data(1, 0, self.item_model, role=FieldAttributesRole)['editable'], True)
        self.assertEqual(self._data(1, 0, self.item_model, role=FieldAttributesRole)['static'], 'static')
        self.assertEqual(self._data(1, 0, self.item_model, role=FieldAttributesRole)['prefix'], 'pre')
        self.assertEqual(self._data(1, 0, self.item_model, role=Qt.ToolTipRole), 'Hint')
        self.assertEqual(self._data(1, 0, self.item_model, role=Qt.BackgroundRole), 'red')
        self.assertTrue(isinstance(self._data(1, 2, self.item_model), AbstractModelProxy))
        self.assertEqual(self._data(1, 3, self.item_model), self.collection[1].created)
        
        self.assertEqual(self._data(-1, -1, self.item_model, role=ObjectRole, validate_index=False), None)
        self.assertEqual(self._data(100, 100, self.item_model, role=ObjectRole, validate_index=False), None)
        self.assertEqual(self._data(-1, -1, self.item_model, role=FieldAttributesRole, validate_index=False), {'editable': False, 'focus_policy': 0})
        self.assertEqual(self._data(100, 100, self.item_model, role=FieldAttributesRole, validate_index=False), {'editable': False, 'focus_policy': 0})

    def test_first_columns(self):
        # when data is loaded for column 0, it remains loading for column 1
        self.assertTrue(self._row_count(self.item_model) > 1)
        self.assertEqual(self._data(1, 0, self.item_model, role=Qt.EditRole), None)  
        self.item_model.timeout_slot()
        self.process()
        self.assertEqual(self._data(1, 0, self.item_model, role=Qt.EditRole), 1)
        self.assertEqual(self._data(1, 1, self.item_model, role=Qt.EditRole), None)
        self.item_model.timeout_slot()
        self.process()
        self.assertEqual(self._data(1, 0, self.item_model, role=Qt.EditRole), 1)
        self.assertEqual(self._data(1, 1, self.item_model, role=Qt.EditRole), 0)

    def test_last_columns(self):
        # when data is loaded for column 1, it remains loading for column 0
        self.assertTrue(self._row_count(self.item_model) > 1)
        self.assertEqual(self._data(1, 1, self.item_model, role=Qt.EditRole), None)  
        self.item_model.timeout_slot()
        self.process()
        self.assertEqual(self._data(1, 1, self.item_model, role=Qt.EditRole), 0)
        self.assertEqual(self._data(1, 0, self.item_model, role=Qt.EditRole), None)
        self.item_model.timeout_slot()
        self.process()
        self.assertEqual(self._data(1, 1, self.item_model, role=Qt.EditRole), 0)
        self.assertEqual(self._data(1, 0, self.item_model, role=Qt.EditRole), 1)

    def test_flags(self):
        self._load_data(self.item_model)
        flags = self._flags(1, 1, self.item_model)
        self.assertTrue(flags & Qt.ItemIsEditable)
        self.assertTrue(flags & Qt.ItemIsEnabled)
        self.assertTrue(flags & Qt.ItemIsSelectable)

    def test_sort( self ):
        self.item_model.sort( 0, Qt.AscendingOrder )
        # check the sorting
        self._load_data(self.item_model)
        row_0 = self._data( 0, 0, self.item_model )
        row_1 = self._data( 1, 0, self.item_model )
        LOGGER.debug('row 0 : {0}, row 1 : {1}'.format(row_0, row_1))
        self.assertTrue( row_1 > row_0 )
        self.item_model.sort( 0, Qt.DescendingOrder )
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
            self.assertEqual(self._header_data(row, Qt.Vertical, Qt.ToolTipRole, self.item_model), None)
            self.assertEqual(self._header_data(row, Qt.Vertical, ObjectRole, self.item_model), None)
            self.assertEqual(self._header_data(row, Qt.Vertical, Qt.DisplayRole, self.item_model), None)
            self.assertEqual(self._header_data(row, Qt.Vertical, Qt.DecorationRole, self.item_model), None)
            self.assertEqual(self._header_data(row, Qt.Vertical, VerboseIdentifierRole, self.item_model), None)
            self.assertEqual(self._header_data(row, Qt.Vertical, Qt.SizeHintRole, self.item_model), self.item_model.vertical_header_size)
            self.assertEqual(self._header_data(row, Qt.Vertical, ValidRole, self.item_model), None)
            self.assertEqual(self._header_data(row, Qt.Vertical, ValidMessageRole, self.item_model), None)
        self.item_model.timeout_slot()
        self.process()
        # after the timeout, the data is available
        for row in range(row_count):
            self.assertIn('Open', self._header_data(row, Qt.Vertical, Qt.ToolTipRole, self.item_model))
            # dont display any data if there is a decoration, otherwise
            # both are displayed mixed
            self.assertEqual(self._header_data(row, Qt.Vertical, Qt.DisplayRole, self.item_model), '')
            self.assertTrue(self._header_data(row, Qt.Vertical, Qt.DecorationRole, self.item_model))
            self.assertEqual(self._header_data(row, Qt.Vertical, ObjectRole, self.item_model), self.collection[row])
            self.assertEqual(self._header_data(row, Qt.Vertical, VerboseIdentifierRole, self.item_model), 'A : {0}'.format(row))
            self.assertEqual(self._header_data(row, Qt.Vertical, Qt.SizeHintRole, self.item_model), self.item_model.vertical_header_size)
            self.assertEqual(self._header_data(row, Qt.Vertical, ValidRole, self.item_model), True)
            self.assertEqual(self._header_data(row, Qt.Vertical, ValidMessageRole, self.item_model), None)
        # when changing an object, it might become invalid after a timeout
        self.signal_register.clear()
        a1 = self.collection[1]
        a1.y = None
        self.item_model.objects_updated(None, (a1,))
        self.item_model.timeout_slot()
        self.process()
        self.assertEqual(self._header_data(1, Qt.Vertical, ValidRole, self.item_model), False)
        self.assertEqual(self._header_data(1, Qt.Vertical, ValidMessageRole, self.item_model), 'Y is a required field')
        self.assertEqual(len(self.signal_register.header_changes), 1)

    def test_set_data(self):
        # the set data is done after the timeout has passed
        # and happens in the requested order
        self._load_data(self.item_model)
        self._set_data(0, 0, 20, self.item_model)
        self._set_data(0, 1, 10, self.item_model)
        self.item_model.timeout_slot()
        self.process()
        # x is set first, so y becomes not
        # editable and remains at its value
        self.assertEqual(self._data(0, 0, self.item_model), 20)
        self.assertEqual(self._data(0, 1, self.item_model),  0)
        self._set_data(0, 0, 5, self.item_model)
        self._set_data(0, 1, 10, self.item_model)
        self.item_model.timeout_slot()
        self.process()
        # x is set first, so y becomes
        # editable and its value is changed
        self.assertEqual(self._data(0, 0, self.item_model), 5)
        self.assertEqual(self._data(0, 1, self.item_model), 10)
        self._set_data(0, 1, 15, self.item_model)
        self._set_data(0, 0, 20, self.item_model)
        self.item_model.timeout_slot()
        self.process()
        # x is set last, so y stays
        # editable and its value is changed
        self.assertEqual(self._data(0, 0, self.item_model), 20)
        self.assertEqual(self._data(0, 1, self.item_model), 15)

    def test_change_column_width(self):
        self.item_model.timeout_slot()
        self.item_model.setHeaderData(1, Qt.Horizontal, QtCore.QSize(140,10), 
                                 Qt.SizeHintRole)
        size_hint = variant_to_py(self.item_model.headerData(1, Qt.Horizontal, Qt.SizeHintRole))
        self.assertEqual(size_hint.width(), 140)
        
    def test_modify_list_while_editing( self ):
        a0 = self.collection[0]
        a1 = self.collection[1]
        self._load_data(self.item_model)
        self.assertEqual( a0.x, self._data( 0, 0, self.item_model) )
        # switch first and second person in collection without informing
        # the item_model
        self.collection[0:2] = [a1, a0]
        self._set_data(0, 0, 7, self.item_model)
        self.item_model.timeout_slot()
        self.process()
        self.assertEqual( a0.x, 7 )

    def test_delete_after_set_data( self ):
        # the item  model is deleted after data has been set,
        # like in closing a form immediately after changing a field
        a0 = self.collection[0]
        self._load_data(self.item_model)
        self.assertEqual( a0.x, 0 )
        self._set_data(0, 0, 10, self.item_model)
        delete(self.item_model)
        self.process()
        self.assertEqual( a0.x, 10 )
        
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
        self.item_model.timeout_slot()
        self.process()
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
        a0 = self.collection[0]
        a0.y = 10
        self.item_model.objects_updated(None, (a0,))
        self.item_model.timeout_slot()
        self.process()
        self.assertEqual( len(self.signal_register.data_changes), 1 )
        self.assertEqual( self.signal_register.data_changes[0],
                          ((0, 1), (0, 1)) )

    def test_unloaded_objects_updated(self):
        # only load data for a single column
        self.assertTrue(self._row_count(self.item_model) > 1)
        self._data(0, 1, self.item_model)
        self.item_model.timeout_slot()
        self.process()
        self.assertEqual(self._data(0, 1, self.item_model, role=Qt.EditRole), 0)
        # modify two columns to test if only a change for the loaded
        # column is emitted
        self.signal_register.clear()
        a0 = self.collection[0]
        a0.x = 9
        a0.y = 10
        self.item_model.objects_updated(None, (a0,))
        self.item_model.timeout_slot()
        self.process()
        self.assertEqual( len(self.signal_register.data_changes), 1 )
        self.assertEqual( self.signal_register.data_changes[0],
                          ((0, 1), (0, 1)) )

    def test_no_objects_updated(self):
        self._load_data(self.item_model)
        self.signal_register.clear()
        self.item_model.objects_updated(None, (object(),))
        self.item_model.timeout_slot()
        self.process()
        self.assertEqual( len(self.signal_register.data_changes), 0 )
        self.assertEqual( len(self.signal_register.header_changes), 0 )
        self.assertEqual( self.signal_register.layout_changes, 0 )

    def test_objects_created(self):
        self._load_data(self.item_model)
        row_count = self.item_model.rowCount()
        self.signal_register.clear()
        a5 = self.A(5)
        self.collection.append(a5)
        self.item_model.objects_created(None, (a5,))
        self.item_model.timeout_slot()
        self.process()
        self.assertEqual(len(self.signal_register.header_changes), 1)
        new_row_count = self.item_model.rowCount()
        self.assertEqual(new_row_count, row_count+1)

    def test_no_objects_created(self):
        self._load_data(self.item_model)
        self.signal_register.clear()
        self.item_model.objects_created(None, (object(),))
        self.item_model.timeout_slot()
        self.process()
        self.assertEqual( len(self.signal_register.data_changes), 0 )
        self.assertEqual( len(self.signal_register.header_changes), 0 )
        self.assertEqual( self.signal_register.layout_changes, 0 )

    def test_objects_deleted(self):
        self._load_data(self.item_model)
        row_count = self.item_model.rowCount()
        a0 = self.collection[0]
        a = self.collection[-1]
        self.assertEqual(self._data(0, 0, self.item_model), a0.x)
        self.signal_register.clear()
        # emitting the deleted signal happens before the object is
        # deleted
        self.item_model.objects_deleted(None, (a,))
        # but removing an object should go through the item_model or there is no
        # way the item_model can be aware.
        self.item_model.get_value().remove(a)
        # but the timeout might be after the object was deleted
        self.item_model.timeout_slot()
        self.process()
        self.assertEqual(self.signal_register.layout_changes, 1)
        new_row_count = self.item_model.rowCount()
        self.assertEqual(new_row_count, row_count-1)
        # after the delete, all data is cleared
        self.assertEqual(self._data(0, 0, self.item_model), None)
        self.item_model.timeout_slot()
        self.process()
        self.assertEqual(self._data(0, 0, self.item_model), a0.x)

    def test_no_objects_deleted(self):
        self._load_data(self.item_model)
        self.signal_register.clear()
        self.item_model.objects_deleted(None, (object(),))
        self.item_model.timeout_slot()
        self.process()
        self.assertEqual( len(self.signal_register.data_changes), 0 )
        self.assertEqual( len(self.signal_register.header_changes), 0 )
        self.assertEqual( self.signal_register.layout_changes, 0 )

    def test_dynamic_editable(self):
        # If the editable field attribute of one field depends on the value
        # of another field, 'editable' should be reevaluated after the
        # other field is set
        a0 = self.collection[0]
        # get the data once, to fill the cached values of the field attributes
        # so changes get passed the first check
        self._load_data(self.item_model)
        self.assertEqual(a0.y, 0)
        self.assertEqual(self._data(0, 1, self.item_model), 0)
        # initialy, field is editable
        self._set_data(0, 1, 1, self.item_model)
        self.item_model.timeout_slot()
        self.process()
        self.assertEqual(a0.y, 1)
        a0.x = 11
        self._set_data(0, 1, 0, self.item_model)
        self.item_model.timeout_slot()
        self.process()
        self.assertEqual(a0.y, 1)

    def test_list_attribute(self):
        # when the data method of a CollectionProxy returns a list, manipulations
        # on this list should be reflected in the original list
        a0 = self.collection[0]
        # get the data once, to fill the cached values
        self._load_data(self.item_model)
        returned_list = self._data(0, 2, self.item_model)
        self.assertEqual(len(returned_list), len(a0.z))
        # manipulate the returned list, and see if the original is manipulated
        # as well
        new_z = object()
        self.assertFalse(new_z in a0.z )
        returned_list.append(new_z)
        self.assertTrue( new_z in a0.z )
        z0 = a0.z[0]
        self.assertTrue( z0 in a0.z )
        returned_list.remove(z0)
        self.assertFalse( z0 in a0.z )

    def test_completion(self):
        self._load_data(self.item_model)
        self.assertIsInstance(self._data(0, 4, self.item_model, role=Qt.EditRole), B)
        self.assertIsNone(self._data(0, 4, self.item_model, role=CompletionsRole))
        self._set_data(0, 4, 'v', self.item_model, role=CompletionPrefixRole)
        self.item_model.timeout_slot()
        self.process()
        self.assertIsNotNone(self._data(0, 4, self.item_model, role=CompletionsRole))

class QueryQStandardItemModelMixinCase(ItemModelCaseMixin):
    """
    methods to setup a QStandardItemModel representing a query
    """

    @classmethod
    def setup_proxy(cls):
        cls.proxy = QueryModelProxy(cls.session.query(Person))

    @classmethod
    def setup_item_model(cls, admin_route, admin_name):
        cls.item_model = CollectionProxy(admin_route, admin_name)
        cls.item_model.set_value(cls.proxy)
        cls.columns = ('first_name', 'last_name')
        list(cls.item_model.add_columns(cls.columns))
        cls.item_model.timeout_slot()

class QueryQStandardItemModelCase(
    RunningThreadCase,
    QueryQStandardItemModelMixinCase, ExampleModelMixinCase):
    """Test the functionality of A QStandardItemModel
    representing a query
    """

    @classmethod
    def setUpClass(cls):
        super(QueryQStandardItemModelCase, cls).setUpClass()
        cls.first_person_id = None
        cls.thread.post(cls.setup_sample_model)
        cls.thread.post(cls.load_example_data)
        cls.process()

    def setUp(self):
        super(QueryQStandardItemModelCase, self).setUp()
        self.app_admin = ApplicationAdmin()
        self.person_admin = self.app_admin.get_related_admin(Person)
        self.thread.post(self.setup_proxy)
        self.process()
        self.admin_route = ViewRegister.register_admin_route(self.person_admin)
        self.setup_item_model(self.admin_route, self.person_admin.get_name())
        self.process()
        self.query_counter = 0
        event.listen(Engine, 'after_cursor_execute', self.increase_query_counter)

    def tearDown(self):
        event.remove(Engine, 'after_cursor_execute', self.increase_query_counter)
        ViewRegister.unregister_view(self.admin_route)
        #self.tear_down_sample_model()

    def increase_query_counter(self, conn, cursor, statement, parameters, context, executemany):
        self.query_counter += 1
        LOGGER.debug('Counted query {} : {}'.format(
            self.query_counter, str(statement)
        ))

    def insert_object(self):
        person = Person()
        count = len(self.proxy)
        self.proxy.append(person)
        self.assertEqual(self.proxy.index(person), count)
        self.person = person

    def test_insert_after_sort(self):
        self.item_model.timeout_slot()
        self.assertTrue( self.item_model.columnCount() > 0 )
        self.item_model.sort( 1, Qt.AscendingOrder )
        # check the query
        self.assertTrue( self.item_model.columnCount() > 0 )
        rowcount = self._row_count(self.item_model)
        self.assertTrue( rowcount > 0 )
        # check the sorting
        self._load_data(self.item_model)
        data0 = self._data( 0, 1, self.item_model )
        data1 = self._data( 1, 1, self.item_model )
        self.assertTrue( data1 > data0 )
        self.item_model.sort( 1, Qt.DescendingOrder )
        self._load_data(self.item_model)
        data0 = self._data( 0, 1, self.item_model )
        data1 = self._data( 1, 1, self.item_model )
        self.assertTrue( data0 > data1 )
        # insert a new object
        self.thread.post(self.insert_object)
        self.process()
        person = self.person
        self.item_model.objects_created(None, (person,))
        self.item_model.timeout_slot()
        self.process()
        new_rowcount = self.item_model.rowCount()
        self.assertEqual(new_rowcount, rowcount + 1)
        new_row = new_rowcount - 1
        self.assertEqual([person], list(self.item_model.get_value()[new_row:new_rowcount]))
        # fill in the required fields
        self.assertFalse( self.person_admin.is_persistent( person ) )
        self.assertEqual( self._data( new_row, 0, self.item_model ), None )
        self.assertEqual( self._data( new_row, 1, self.item_model ), None )
        self._set_data( new_row, 0, 'Foo', self.item_model )
        self._set_data( new_row, 1, 'Bar', self.item_model )
        self.item_model.timeout_slot()
        self.process()
        self.assertEqual( person.first_name, 'Foo', self.item_model )
        self.assertEqual( person.last_name, 'Bar', self.item_model )
        self._load_data(self.item_model)
        self.assertEqual( self._data( new_row, 0, self.item_model ), 'Foo' )
        self.assertEqual( self._data( new_row, 1, self.item_model ), 'Bar' )
        self.assertTrue( self.person_admin.is_persistent( person ) )
        # get the object at the new row (eg, to display a form view)
        self.assertEqual(self._header_data(new_row, Qt.Vertical, ObjectRole, self.item_model), person)

    def test_single_query(self):
        # after constructing a queryproxy, 4 queries are issued
        # before data is returned : 
        # - count query
        # - person query
        # - contact mechanism select in load
        # - address select in load
        # those last 2 are needed for the validation of the compounding objects

        class SingleItemFilter(Filter):

            def decorate_query(self, query, values):
                return query.filter_by(id=values)

        start = self.query_counter
        item_model = CollectionProxy(self.admin_route, self.person_admin.get_name())
        item_model.set_value(self.proxy)
        item_model.set_filter(SingleItemFilter('id'), self.first_person_id)
        list(item_model.add_columns(self.columns))
        self._load_data(item_model)
        self.assertEqual(item_model.columnCount(), 2)
        self.assertEqual(item_model.rowCount(), 1)
        self.assertEqual(self.query_counter, start+4)
