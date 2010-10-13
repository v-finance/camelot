"""Test the behaviour of the qt bindings in various circumstances.
"""

import unittest

from PyQt4 import QtGui, QtCore

class ReferenceHoldingBox(QtGui.QGroupBox):
    """A group box holding references to the table
    view and the table model"""

    def __init__(self, model, table):
        QtGui.QGroupBox.__init__(self)
        self.model = model
        self.table = table
                 
class TableView( QtGui.QWidget  ):
    """A widget containg both a table and a groupbox that
    holds a reference to both the table and the model of the
    table"""

    def __init__( self, table_model ):
        super(TableView, self).__init__()
        widget_layout = QtGui.QVBoxLayout()
        table = QtGui.QTableView( self )
        table.setModel( table_model )
        widget_layout.addWidget( table )
        widget_layout.addWidget( ReferenceHoldingBox( table_model, self ) )
        self.setLayout( widget_layout )

class ModelViewRegister(QtCore.QObject):
    
    def __init__(self):
        super(ModelViewRegister, self).__init__()
        self.max_key = 0
        self.model_by_view = dict()
        
    def register_model_view(self, model, view):
        self.max_key += 1
        view.destroyed.connect( self._registered_object_destroyed )
        self.model_by_view[self.max_key] = model
        view.setProperty( 'registered_key', self.max_key )
        
    @QtCore.pyqtSlot(QtCore.QObject)
    def _registered_object_destroyed(self, qobject):
        key, _success = qobject.property('registered_key').toLongLong()
        del self.model_by_view[key]

class TableViewCases(unittest.TestCase):
    """Tests related to table views"""

    def setUp(self):
        from camelot.test import get_application
        self.app = get_application()

    def test_table_view_garbage_collection(self):
        """Create a table view and force its garbage collection, while
        a common reference exists to both the table view and its model.
        
        when doing so without registering the model and the view to the
        ModelViewRegister, this will segfault.
        """            
        register = ModelViewRegister()
        
        import gc
        for _i in range(100):
            
            class TableModelSubclass(QtGui.QStringListModel):
                pass
    
            model = TableModelSubclass()
            widget = TableView( model )
            register.register_model_view(model, widget)
            gc.collect()

class SignalSlotCase( unittest.TestCase ):
    
    def setUp(self):
        from camelot.test import get_application
        self.app = get_application()

    def test_multiple_threads(self):
        """Emit a signal containing a python object and at the
        same time connect to it.
        
        this used to deadlock in pyqt.
        """
        
        class SignalEmitter(QtCore.QObject):
            
            my_signal = QtCore.pyqtSignal(object)
            
            def start_emitting(self):
                for _i in range(1000):
                    o = object()
                    self.my_signal.emit(o)
        
        class SignalReceiver(QtCore.QObject):
            
            @QtCore.pyqtSlot(object)
            def my_slot(self, obj):
                pass
            
        emitter = SignalEmitter()
        
        class ReceivingThread(QtCore.QThread):
            
            def run(self):
                receivers = []
                for _i in range(100):
                    receiver = SignalReceiver()
                    emitter.my_signal.connect( receiver.my_slot )
                    receivers.append(receiver)
                    
        thread = ReceivingThread()
        thread.start()
        emitter.start_emitting()
        thread.wait()