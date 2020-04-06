import datetime
import logging
import unittest

import six

from sqlalchemy import event
from sqlalchemy.engine import Engine

from camelot.core.item_model import (
    AbstractModelFilter,ListModelProxy, QueryModelProxy
)

from camelot.model.party import Person, Party
from camelot.view.proxy.collection_proxy import (
    CollectionProxy, invalid_item)
from camelot.core.item_model import (FieldAttributesRole, ObjectRole,
    VerboseIdentifierRole, ValidRole, ValidMessageRole, AbstractModelProxy,
)
from camelot.view.proxy.queryproxy import QueryTableProxy
from camelot.view.controls import delegates
from camelot.admin.application_admin import ApplicationAdmin
from camelot.admin.object_admin import ObjectAdmin
from camelot.core.conf import settings
from camelot.core.orm import Session
from camelot.core.qt import variant_to_py, QtCore, Qt, py_to_variant, delete
from camelot.test import ModelThreadTestCase

LOGGER = logging.getLogger(__name__)

from .test_model import ExampleModelCase


class ProxySignalRegister( QtCore.QObject ):
    """Helper class to register the signals the proxy emits and analyze
    them"""
    
    def __init__( self, proxy ):
        super( ProxySignalRegister, self ).__init__()
        self.clear()
        proxy.headerDataChanged.connect(self.register_header_change)
        proxy.dataChanged.connect(self.register_data_change)
        proxy.layoutChanged.connect(self.register_layout_change)
        
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

class ProxyCase( ModelThreadTestCase ):

    def setUp( self ):
        super( ProxyCase, self ).setUp()
        settings.setup_model()
        self.app_admin = ApplicationAdmin()
        self.person_admin = self.app_admin.get_related_admin( Person )
        
    def _load_data( self, proxy = None ):
        """Trigger the loading of data by the proxy"""
        if proxy == None:
            proxy = self.proxy
        proxy.timeout_slot()
        proxy.rowCount()
        proxy.timeout_slot()
        self.process()
        row_count = proxy.rowCount()
        column_count = proxy.columnCount()
        self.assertTrue(row_count > 0)
        for row in range(row_count):
            for col in range(column_count):
                self._data( row, col, proxy )
        proxy.timeout_slot()
        self.process()

    def _data( self, row, column, proxy = None, role=Qt.EditRole, validate_index=True):
        """Get data from the proxy"""
        if proxy is None:
            proxy = self.proxy
        index = proxy.index( row, column )
        if validate_index and not index.isValid():
            raise Exception('Index ({0},{1}) is not valid with {2} rows, {3} columns'.format(index.row(), index.column(), proxy.rowCount(), proxy.columnCount()))
        return variant_to_py( proxy.data( index, role ) )
    
    def _set_data( self, row, column, value, proxy = None, validate_index=True):
        """Set data to the proxy"""
        if proxy is None:
            proxy = self.proxy
        index = proxy.index( row, column )
        if validate_index and not index.isValid():
            raise Exception('Index ({0},{1}) is not valid with {2} rows, {3} columns'.format(index.row(), index.column(), proxy.rowCount(), proxy.columnCount()))
        return proxy.setData( index, py_to_variant(value) )

    def _header_data( self, section, orientation, role):
        return variant_to_py( self.proxy.headerData(section, orientation, role))

    def _flags(self, row, column):
        index = self.proxy.index( row, column )
        return self.proxy.flags(index)

    def _row_count( self, proxy = None ):
        """Set data to the proxy"""
        if proxy is None:
            proxy = self.proxy
        proxy.rowCount()
        proxy.timeout_slot()
        self.process()
        return proxy.rowCount()

class A(object):

    def __init__(self, x):
        self.x = x
        self.y = 0
        self.z = [object(), object()]
        self.created = datetime.datetime.now()

    class Admin(ObjectAdmin):
        list_display = ['x', 'y', 'z', 'created']
        field_attributes = {
            'x': {'editable': True,
                  'static':'static',
                  'prefix':lambda o:'pre',
                  'tooltip': 'Hint',
                  'background_color': 'red',
                  'delegate': delegates.IntegerDelegate,
                  },
            'y': {'editable': lambda o: o.x < 10,
                  'delegate': delegates.IntegerDelegate,
                  'nullable': False,
                  },
            'z': {'editable': True,
                  'delegate': delegates.One2ManyDelegate,
                  'target': int,
                  },
        }

        def get_verbose_identifier(self, obj):
            return 'A : {0}'.format(obj.x)

class CollectionProxyCase( ProxyCase ):

    def setUp( self ):
        super( CollectionProxyCase, self ).setUp()
        self.A = A
        self.collection = [A(0), A(1), A(2)]
        self.admin = self.app_admin.get_related_admin(A)
        self.proxy = CollectionProxy(self.admin)
        self.proxy.set_value(self.admin.get_proxy(self.collection))
        self.columns = self.admin.list_display
        list(self.proxy.add_columns(self.columns))
        self.proxy.timeout_slot()
        self.process()
        self.signal_register = ProxySignalRegister( self.proxy )

    def test_invalid_item(self):
        self.assertEqual(variant_to_py(invalid_item.data(Qt.EditRole)), None)
        self.assertEqual(variant_to_py(invalid_item.data(FieldAttributesRole)), {'editable': False, 'focus_policy': 0})
        invalid_clone = invalid_item.clone()
        self.assertEqual(variant_to_py(invalid_clone.data(Qt.EditRole)), None)
        self.assertEqual(variant_to_py(invalid_clone.data(FieldAttributesRole)), {'editable': False, 'focus_policy': 0})
        
    def test_rowcount(self):
        # the rowcount remains 0 while no timeout has passed
        self.assertEqual(self.proxy.rowCount(), 0)
        self.process()
        self.assertEqual(self.proxy.rowCount(), 0)
        self.proxy.timeout_slot()
        self.process()
        self.assertEqual(self.proxy.rowCount(), 3)

    def test_data(self):
        # the data remains None and not editable while no timeout has passed
        self.assertTrue(self._row_count() > 1)
        self.assertEqual(self._data(1, 0, role=Qt.EditRole), None)
        self.assertEqual(self._data(1, 0, role=Qt.DisplayRole), None)
        self.assertEqual(self._data(1, 0, role=ObjectRole), None)
        self.assertEqual(self._data(1, 0, role=FieldAttributesRole).get('editable'), False)
        # why would there be a need to get static fa before the timout has passed ?
        #self.assertEqual(self._data(1, 0, role=FieldAttributesRole)['static'], 'static')
        self.assertEqual(self._data(1, 0, role=FieldAttributesRole).get('prefix'), None)
        self._data(1, 2)
        self._data(1, 3)
        self.proxy.timeout_slot()
        self.process()
        self.assertEqual(self._data(1, 0, role=Qt.EditRole), 1)
        # the prefix is prepended to the display role
        self.assertEqual(self._data(1, 0, role=Qt.DisplayRole), 'pre 1')
        self.assertEqual(self._data(1, 0, role=ObjectRole), self.collection[1])
        self.assertEqual(self._data(1, 0, role=FieldAttributesRole)['editable'], True)
        self.assertEqual(self._data(1, 0, role=FieldAttributesRole)['static'], 'static')
        self.assertEqual(self._data(1, 0, role=FieldAttributesRole)['prefix'], 'pre')
        self.assertEqual(self._data(1, 0, role=Qt.ToolTipRole), 'Hint')
        self.assertEqual(self._data(1, 0, role=Qt.BackgroundRole), 'red')
        self.assertTrue(isinstance(self._data(1, 2), AbstractModelProxy))
        self.assertEqual(self._data(1, 3), self.collection[1].created)
        
        self.assertEqual(self._data(-1, -1, role=ObjectRole, validate_index=False), None)
        self.assertEqual(self._data(100, 100, role=ObjectRole, validate_index=False), None)
        self.assertEqual(self._data(-1, -1, role=FieldAttributesRole, validate_index=False), {'editable': False, 'focus_policy': 0})
        self.assertEqual(self._data(100, 100, role=FieldAttributesRole, validate_index=False), {'editable': False, 'focus_policy': 0})

    def test_first_columns(self):
        # when data is loaded for column 0, it remains loading for column 1
        self.assertTrue(self._row_count() > 1)
        self.assertEqual(self._data(1, 0, role=Qt.EditRole), None)  
        self.proxy.timeout_slot()
        self.process()
        self.assertEqual(self._data(1, 0, role=Qt.EditRole), 1)
        self.assertEqual(self._data(1, 1, role=Qt.EditRole), None)
        self.proxy.timeout_slot()
        self.process()
        self.assertEqual(self._data(1, 0, role=Qt.EditRole), 1)
        self.assertEqual(self._data(1, 1, role=Qt.EditRole), 0)

    def test_last_columns(self):
        # when data is loaded for column 1, it remains loading for column 0
        self.assertTrue(self._row_count() > 1)
        self.assertEqual(self._data(1, 1, role=Qt.EditRole), None)  
        self.proxy.timeout_slot()
        self.process()
        self.assertEqual(self._data(1, 1, role=Qt.EditRole), 0)
        self.assertEqual(self._data(1, 0, role=Qt.EditRole), None)
        self.proxy.timeout_slot()
        self.process()
        self.assertEqual(self._data(1, 1, role=Qt.EditRole), 0)
        self.assertEqual(self._data(1, 0, role=Qt.EditRole), 1)

    def test_flags(self):
        self._load_data()
        flags = self._flags(1, 1)
        self.assertTrue(flags & Qt.ItemIsEditable)
        self.assertTrue(flags & Qt.ItemIsEnabled)
        self.assertTrue(flags & Qt.ItemIsSelectable)

    def test_sort( self ):
        self.proxy.sort( 0, Qt.AscendingOrder )
        # check the sorting
        self._load_data()
        row_0 = self._data( 0, 0 )
        row_1 = self._data( 1, 0 )
        LOGGER.debug('row 0 : {0}, row 1 : {1}'.format(row_0, row_1))
        self.assertTrue( row_1 > row_0 )
        self.proxy.sort( 0, Qt.DescendingOrder )
        # check the sorting
        self._load_data()
        row_0 = self._data( 0, 0 )
        row_1 = self._data( 1, 0 )
        LOGGER.debug('row 0 : {0}, row 1 : {1}'.format(row_0, row_1))
        self.assertTrue( row_1 < row_0 )

    def test_vertical_header_data(self):
        row_count = self._row_count()
        # before the data is loaded, nothing is available, except the sizehint
        self.assertTrue(row_count)
        for row in range(row_count):
            self.assertEqual(self._header_data(row, Qt.Vertical, Qt.ToolTipRole), None)
            self.assertEqual(self._header_data(row, Qt.Vertical, ObjectRole), None)
            self.assertEqual(self._header_data(row, Qt.Vertical, Qt.DisplayRole), None)
            self.assertEqual(self._header_data(row, Qt.Vertical, Qt.DecorationRole), None)
            self.assertEqual(self._header_data(row, Qt.Vertical, VerboseIdentifierRole), None)
            self.assertEqual(self._header_data(row, Qt.Vertical, Qt.SizeHintRole), self.proxy.vertical_header_size)
            self.assertEqual(self._header_data(row, Qt.Vertical, ValidRole), None)
            self.assertEqual(self._header_data(row, Qt.Vertical, ValidMessageRole), None)
        self.proxy.timeout_slot()
        # after the timeout, the data is available
        for row in range(row_count):
            self.assertIn('Open', self._header_data(row, Qt.Vertical, Qt.ToolTipRole))
            self.assertEqual(self._header_data(row, Qt.Vertical, Qt.DisplayRole), six.text_type(row+1))
            self.assertTrue(self._header_data(row, Qt.Vertical, Qt.DecorationRole))
            self.assertEqual(self._header_data(row, Qt.Vertical, ObjectRole), self.collection[row])
            self.assertEqual(self._header_data(row, Qt.Vertical, VerboseIdentifierRole), 'A : {0}'.format(row))
            self.assertEqual(self._header_data(row, Qt.Vertical, Qt.SizeHintRole), self.proxy.vertical_header_size)
            self.assertEqual(self._header_data(row, Qt.Vertical, ValidRole), True)
            self.assertEqual(self._header_data(row, Qt.Vertical, ValidMessageRole), None)
        # when changing an object, it might become invalid after a timeout
        self.signal_register.clear()
        a1 = self.collection[1]
        a1.y = None
        self.proxy.objects_updated(None, (a1,))
        self.proxy.timeout_slot()
        self.assertEqual(self._header_data(1, Qt.Vertical, ValidRole), False)
        self.assertEqual(self._header_data(1, Qt.Vertical, ValidMessageRole), 'Y is a required field')
        self.assertEqual(len(self.signal_register.header_changes), 1)

    def test_set_data(self):
        # the set data is done after the timeout has passed
        # and happens in the requested order
        self._load_data()
        self._set_data(0, 0, 20)
        self._set_data(0, 1, 10)
        self.proxy.timeout_slot()
        # x is set first, so y becomes not
        # editable and remains at its value
        self.assertEqual(self._data(0, 0), 20)
        self.assertEqual(self._data(0, 1),  0)
        self._set_data(0, 0, 5)
        self._set_data(0, 1, 10)
        self.proxy.timeout_slot()
        # x is set first, so y becomes
        # editable and its value is changed
        self.assertEqual(self._data(0, 0), 5)
        self.assertEqual(self._data(0, 1), 10)
        self._set_data(0, 1, 15)
        self._set_data(0, 0, 20)
        self.proxy.timeout_slot()
        # x is set last, so y stays
        # editable and its value is changed
        self.assertEqual(self._data(0, 0), 20)
        self.assertEqual(self._data(0, 1), 15)

    def test_change_column_width(self):
        self.proxy.timeout_slot()
        self.proxy.setHeaderData(1, Qt.Horizontal, QtCore.QSize(140,10), 
                                 Qt.SizeHintRole)
        size_hint = variant_to_py(self.proxy.headerData(1, Qt.Horizontal, Qt.SizeHintRole))
        self.assertEqual(size_hint.width(), 140)
        
    def test_modify_list_while_editing( self ):
        a0 = self.collection[0]
        a1 = self.collection[1]
        self._load_data()
        self.assertEqual( a0.x, self._data( 0, 0 ) )
        # switch first and second person in collection without informing
        # the proxy
        self.collection[0:2] = [a1, a0]
        self._set_data( 0, 0, 7 )
        self.proxy.timeout_slot()
        self.assertEqual( a0.x, 7 )

    def test_delete_after_set_data( self ):
        # the item  model is deleted after data has been set,
        # like in closing a form immediately after changing a field
        a0 = self.collection[0]
        self._load_data()
        self.assertEqual( a0.x, 0 )
        self._set_data(0, 0, 10)
        delete(self.proxy)
        self.assertEqual( a0.x, 10 )
        
    def test_data_changed( self ):
        # verify the data changed signal is only received for changed
        # index ranges
        self._load_data()
        self.assertEqual(self.proxy.rowCount(), 3)
        self.assertEqual(self._data(0, 0), 0)
        self.assertEqual(self._data(1, 0), 1)
        self.assertEqual(self._data(2, 0), 2)
        self.signal_register.clear()
        self._set_data( 0, 0, 8 )
        self.proxy.timeout_slot()
        self.assertEqual( len(self.signal_register.data_changes), 1 )
        for changed_range in self.signal_register.data_changes:
            for index in changed_range:
                row, col = index
                self.assertEqual( row, 0 )
                self.assertEqual( col, 0 )

    def test_objects_updated(self):
        # modify only one column to test if only one change is emitted
        self._load_data()
        self.signal_register.clear()
        a0 = self.collection[0]
        a0.y = 10
        self.proxy.objects_updated(None, (a0,))
        self.proxy.timeout_slot()
        self.assertEqual( len(self.signal_register.data_changes), 1 )
        self.assertEqual( self.signal_register.data_changes[0],
                          ((0, 1), (0, 1)) )

    def test_unloaded_objects_updated(self):
        # only load data for a single column
        self.assertTrue(self._row_count() > 1)
        self._data(0, 1)
        self.proxy.timeout_slot()
        self.process()
        self.assertEqual(self._data(0, 1, role=Qt.EditRole), 0)
        # modify two columns to test if only a change for the loaded
        # column is emitted
        self.signal_register.clear()
        a0 = self.collection[0]
        a0.x = 9
        a0.y = 10
        self.proxy.objects_updated(None, (a0,))
        self.proxy.timeout_slot()
        self.assertEqual( len(self.signal_register.data_changes), 1 )
        self.assertEqual( self.signal_register.data_changes[0],
                          ((0, 1), (0, 1)) )

    def test_no_objects_updated(self):
        self._load_data()
        self.signal_register.clear()
        self.proxy.objects_updated(None, (object(),))
        self.proxy.timeout_slot()
        self.assertEqual( len(self.signal_register.data_changes), 0 )
        self.assertEqual( len(self.signal_register.header_changes), 0 )
        self.assertEqual( self.signal_register.layout_changes, 0 )

    def test_objects_created(self):
        self._load_data()
        row_count = self.proxy.rowCount()
        self.signal_register.clear()
        a5 = self.A(5)
        self.collection.append(a5)
        self.proxy.objects_created(None, (a5,))
        self.proxy.timeout_slot()
        self.assertEqual(len(self.signal_register.header_changes), 1)
        new_row_count = self.proxy.rowCount()
        self.assertEqual(new_row_count, row_count+1)

    def test_no_objects_created(self):
        self._load_data()
        self.signal_register.clear()
        self.proxy.objects_created(None, (object(),))
        self.proxy.timeout_slot()
        self.assertEqual( len(self.signal_register.data_changes), 0 )
        self.assertEqual( len(self.signal_register.header_changes), 0 )
        self.assertEqual( self.signal_register.layout_changes, 0 )

    def test_objects_deleted(self):
        self._load_data()
        row_count = self.proxy.rowCount()
        a0 = self.collection[0]
        a = self.collection[-1]
        self.assertEqual(self._data(0, 0), a0.x)
        self.signal_register.clear()
        # emitting the deleted signal happens before the object is
        # deleted
        self.proxy.objects_deleted(None, (a,))
        # but removing an object should go through the proxy or there is no
        # way the proxy can be aware.
        self.proxy.get_value().remove(a)
        # but the timeout might be after the object was deleted
        self.proxy.timeout_slot()
        self.assertEqual(self.signal_register.layout_changes, 1)
        new_row_count = self.proxy.rowCount()
        self.assertEqual(new_row_count, row_count-1)
        # after the delete, all data is cleared
        self.assertEqual(self._data(0, 0), None)
        self.proxy.timeout_slot()
        self.assertEqual(self._data(0, 0), a0.x)

    def test_no_objects_deleted(self):
        self._load_data()
        self.signal_register.clear()
        self.proxy.objects_deleted(None, (object(),))
        self.proxy.timeout_slot()
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
        self._load_data()
        self.assertEqual(a0.y, 0)
        self.assertEqual(self._data(0, 1), 0)
        # initialy, field is editable
        self._set_data(0, 1, 1)
        self.proxy.timeout_slot()
        self.assertEqual(a0.y, 1)
        a0.x = 11
        self._set_data(0, 1, 0)
        self.proxy.timeout_slot()
        self.assertEqual(a0.y, 1)

    def test_list_attribute(self):
        # when the data method of a CollectionProxy returns a list, manipulations
        # on this list should be reflected in the original list
        a0 = self.collection[0]
        # get the data once, to fill the cached values
        self._load_data()
        returned_list = self._data(0, 2)
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
        
class QueryProxyCase( ProxyCase ):
    """Test the functionality of the QueryProxy to perform CRUD operations on 
    stand alone data"""
  
    def setUp(self, admin = None):
        super( QueryProxyCase, self ).setUp()
        if admin is None:
            admin = self.person_admin
        self.proxy = QueryTableProxy(admin)
        self.proxy.set_value(admin.get_proxy(admin.get_query()))
        self.columns = ('first_name', 'last_name')
        list(self.proxy.add_columns(self.columns))
        self.proxy.timeout_slot()
        self.process()
        self.query_counter = 0
        event.listen(Engine, 'after_cursor_execute', self.increase_query_counter)
        
    def increase_query_counter(self, conn, cursor, statement, parameters, context, executemany):
        self.query_counter += 1

    def test_insert_after_sort( self ):
        from camelot.view.proxy.queryproxy import QueryTableProxy
        from camelot.model.party import Person
        self.proxy.timeout_slot()
        self.assertTrue( self.proxy.columnCount() > 0 )
        self.proxy.sort( 1, Qt.AscendingOrder )
        # check the query
        self.assertTrue( self.proxy.columnCount() > 0 )
        rowcount = self._row_count()
        self.assertTrue( rowcount > 0 )
        # check the sorting
        self._load_data()
        data0 = self._data( 0, 1 )
        data1 = self._data( 1, 1 )
        self.assertTrue( data1 > data0 )
        self.proxy.sort( 1, Qt.DescendingOrder )
        self._load_data()
        data0 = self._data( 0, 1 )
        data1 = self._data( 1, 1 )
        self.assertTrue( data0 > data1 )
        # insert a new object
        person = Person()
        self.proxy.get_value().append(person)
        self.assertEqual(self.proxy.get_value().index(person), rowcount)
        self.proxy.objects_created(None, (person,))
        self.proxy.timeout_slot()
        new_rowcount = self.proxy.rowCount()
        self.assertEqual(new_rowcount, rowcount + 1)
        new_row = new_rowcount - 1
        self.assertEqual([person], list(self.proxy.get_value()[new_row:new_rowcount]))
        # fill in the required fields
        self.assertFalse( self.person_admin.is_persistent( person ) )
        self.assertEqual( self._data( new_row, 0 ), None )
        self.assertEqual( self._data( new_row, 1 ), None )
        self._set_data( new_row, 0, 'Foo' )
        self._set_data( new_row, 1, 'Bar' )
        self.proxy.timeout_slot()
        self.assertEqual( person.first_name, 'Foo' )
        self.assertEqual( person.last_name, 'Bar' )
        self._load_data()
        self.assertEqual( self._data( new_row, 0 ), 'Foo' )
        self.assertEqual( self._data( new_row, 1 ), 'Bar' )
        self.assertTrue( self.person_admin.is_persistent( person ) )
        # get the object at the new row (eg, to display a form view)
        self.assertEqual( self._header_data(new_row, Qt.Vertical, ObjectRole), person)

    def test_single_query(self):
        # after constructing a queryproxy, 2 queries are issued
        # before data is returned (count query + get data query)
        first_person = self.person_admin.get_query().first()
        start = self.query_counter
        proxy = QueryTableProxy(self.person_admin)
        proxy.set_value(self.person_admin.get_proxy(self.person_admin.get_query().filter_by(id=first_person.id)))
        list(proxy.add_columns(self.columns))
        self._load_data(proxy)
        self.assertEqual(self.query_counter, start+2)
        self.assertEqual(proxy.rowCount(), 1)

class ListModelProxyCase(ExampleModelCase):

    def setUp(self):
        super(ListModelProxyCase, self).setUp()
        self.list_model = [A(1), A(2), A(3), A(0)]
        self.proxy = ListModelProxy(self.list_model)
        self.attribute_name = 'x'

        class XLessThanFilter(AbstractModelFilter):
        
            def filter(self, it, value):
                for obj in it:
                    if obj.x < value:
                        yield obj
        
        self.list_model_filter = XLessThanFilter()

    def create_object(self):
        return A(7)
    
    def delete_object(self, obj):
        pass

    def append_object_to_collection(self, obj):
        self.list_model.append(obj)

    def test_index_new_object(self):
        initial_length = len(self.proxy)
        self.assertTrue(initial_length)
        # a new object is created, and the proxy is unaware
        obj = self.create_object()
        self.assertEqual(len(self.proxy), initial_length)
        # append the new object to the collection without going
        # through the proxy
        self.append_object_to_collection(obj)
        # the proxy is still unaware
        self.assertEqual(len(self.proxy), initial_length)
        # try to find the new object through the proxy
        try:
            i = self.proxy.index(obj)
        except ValueError:
            # if the proxy is a queryproxy, the object will not be found
            i = None
        # if the object was found, so the length of the proxy has changed
        if i is not None:
            self.assertEqual(len(self.proxy), initial_length+1)

    def test_length(self):
        self.assertTrue(len(self.proxy))

    def test_slice(self):
        rows = len(self.proxy)
        self.assertTrue(list(self.proxy[0:1]))
        self.assertTrue(list(self.proxy[rows - 1:rows]))

    def test_append(self):
        # append a new object twice
        size = len(self.proxy)
        obj = self.create_object()
        self.proxy.append(obj)
        self.proxy.append(obj)
        self.assertEqual(len(self.proxy), size+1)
        # append an existing object
        first_obj = list(self.proxy[0:1])[0]
        self.proxy.append(first_obj)
        self.assertEqual(len(self.proxy), size+1)

    def test_remove(self):
        # remove an existing object
        size = len(self.proxy)
        first_obj, second_obj, third_obj = list(self.proxy[0:3])
        self.proxy.remove(second_obj)
        self.delete_object(second_obj)
        self.assertEqual(len(self.proxy), size-1)
        new_first_obj, new_second_obj = list(self.proxy[0:2])
        self.assertEqual(first_obj, new_first_obj)
        self.assertEqual(third_obj, new_second_obj)
        # remove a new twice
        obj = self.create_object()
        self.proxy.append(obj)
        self.proxy.remove(obj)
        self.assertEqual(len(self.proxy), size-1)

    def test_copy_after_sort(self):
        self.proxy.sort(self.attribute_name)
        length = len(self.proxy)
        new_proxy = self.proxy.copy()
        self.assertEqual(len(new_proxy), length)
        for o1, o2 in zip(self.proxy[0:length], new_proxy[0:length]):
            self.assertEqual(o1, o2)

    def test_copy_before_index(self):
        # take a copy before the indexing has been done, to make
        # sure the internal state is initialized correct
        new_proxy = self.proxy.copy()
        self.assertEqual(len(new_proxy), len(self.proxy))

    def test_filter(self):
        self.assertEqual(len(self.proxy), 4)
        self.proxy.filter(self.list_model_filter, 3)
        self.assertEqual(len(self.proxy), 3)


class QueryModelProxyCase(ListModelProxyCase):

    def setUp(self):
        super(QueryModelProxyCase, self).setUp()
        self.query = self.session.query(Person)
        self.proxy = QueryModelProxy(self.query)
        self.attribute_name = 'first_name'

    def create_object(self):
        return Person()

    def delete_object(self, obj):
        self.session.delete(obj)
        self.session.flush()

    def test_index_expunged_object(self):
        # a new object is created, and the proxy is aware
        obj = self.create_object()
        self.proxy.append(obj)
        initial_length = len(self.proxy)
        self.assertTrue(initial_length)
        # the new object is expunged, and the proxy is unaware
        self.session.expunge(obj)
        self.assertEqual(len(self.proxy), initial_length)
        # try to find the new object through the proxy
        i = self.proxy.index(obj)
        self.assertTrue(i)
        # inform the proxy about the object being removed
        self.proxy.remove(obj)
        self.assertEqual(len(self.proxy), initial_length-1)

    def test_append_and_flush(self):
        size = len(self.proxy)
        obj = self.create_object()
        self.proxy.append(obj)
        self.assertEqual(len(self.proxy), size+1)
        obj.first_name = 'Foo'
        obj.last_name = 'Fighter'
        self.session.flush()
        self.assertEqual(len(self.proxy), size+1)
        last_obj = list(self.proxy[0:size+1])[0]

    def test_unique_primary_key(self):
        # A query returns multiple objects with the same primary key
        query = self.session.query(Party)
        proxy = QueryModelProxy(query)
        union_all_query = query.union_all(self.session.query(Party)).order_by(Party.id)
        self.assertEqual(union_all_query.count(), query.count()*2)
        # Validate the second and the first element of the union query
        # refer to the same object
        first_query_element = union_all_query.offset(0).first()
        second_query_element = union_all_query.offset(1).first()
        self.assertEqual(first_query_element, second_query_element)
        # However, the proxy will only report unique primary keys
        union_all_proxy = QueryModelProxy(union_all_query)
        self.assertEqual(len(union_all_proxy), len(proxy))
        first_proxy_element = list(union_all_proxy[0:1])[0]
        second_proxy_element = list(union_all_proxy[1:2])[0]
        self.assertNotEqual(first_proxy_element, second_proxy_element)
        ## And the objects will be at the same index as if there were
        ## no duplicates
        #objects = list(self.proxy[0:len(self.proxy)])
        #union_all_objects = list(union_all_proxy[0:len(union_all_proxy)])
        #for i in range(len(self.proxy)):
            #self.assertEqual(union_all_objects[i], objects[i])

    def test_filter(self):
        pass
