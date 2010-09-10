"""Test the behaviour of the qt bindings in various circumstances.
"""

import unittest
import logging
logger = logging.getLogger( 'test_qt_bindings' )

from PyQt4 import QtGui
#from PySide import QtGui

class ReferenceHoldingBox(QtGui.QGroupBox):
    """A group box implicitely holding references to the table
    view and the table model"""

    def __init__(self, model_name_getter, table_name_getter):
        QtGui.QGroupBox.__init__(self)
        self.model_name_getter = model_name_getter
        self.table_name_getter = table_name_getter
                 
class TableView( QtGui.QWidget  ):
    """A widget containg both a table and a groupbox that
    holds a reference to both the table and the model of the
    table"""

    def __init__( self, parent = None ):
        super(TableView, self).__init__( parent )
        widget_layout = QtGui.QVBoxLayout()
        self.table = QtGui.QTableView( self )
        table_model = self.table_model()
        self.table.setModel( table_model )
        widget_layout.addWidget( self.table )        
        widget_layout.addWidget( ReferenceHoldingBox( table_model.objectName, self.objectName ) )
        self.setLayout( widget_layout )

class TableViewCases(unittest.TestCase):
    """Tests related to table views"""

    def setUp(self):
        self.application = QtGui.QApplication([])

    def test_select_view_garbage_collection(self):
        """Create a select view and force its garbage collection"""
        import gc
        for i in range(100):
            print i
            
            class TableModelSubclass(QtGui.QStringListModel):
                pass
    
            class TableViewSubclass(TableView):
                table_model = TableModelSubclass
    
            widget = TableViewSubclass()
            gc.collect()