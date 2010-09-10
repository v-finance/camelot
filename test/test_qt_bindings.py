"""Test the behaviour of the qt bindings
in various circumstances.
"""

from camelot.test import ModelThreadTestCase

import logging
logger = logging.getLogger( 'camelot.view.controls.tableview' )

from PyQt4 import QtGui
from PyQt4 import QtCore
from PyQt4.QtCore import Qt
from PyQt4.QtCore import SIGNAL
from PyQt4.QtGui import QSizePolicy

class QueryTableProxy(QtGui.QStringListModel):

    def get_collection_getter(self): # !!!
        
        def collection_getter():
            if not self._query_getter:
                return []
            return self.get_query_getter()().all()
        
        return collection_getter
                
class TableView( QtGui.QWidget  ):
    TableWidget = QtGui.QTableView

    def __init__( self, admin, search_text = None, parent = None ):
        super(TableView, self).__init__( parent )
        self.admin = admin
        widget_layout = QtGui.QVBoxLayout()
        self.header = None
        widget_layout.setSpacing( 0 )
        widget_layout.setMargin( 0 )
        splitter = QtGui.QSplitter( self )
        splitter.setObjectName('splitter')
        widget_layout.addWidget( splitter )
        table_widget = QtGui.QWidget( self )
        filters_widget = QtGui.QWidget( self )
        self.table_layout = QtGui.QVBoxLayout()
        self.table_layout.setSpacing( 0 )
        self.table_layout.setMargin( 0 )
        self.table = None
        self.filters_layout = QtGui.QVBoxLayout()
        self.filters_layout.setSpacing( 0 )
        self.filters_layout.setMargin( 0 )
        self.actions = None
        self._table_model = None
        table_widget.setLayout( self.table_layout )
        filters_widget.setLayout( self.filters_layout )
        self.set_admin( admin )
        splitter.addWidget( table_widget )
        splitter.addWidget( filters_widget )
        self.setLayout( widget_layout )
        self.search_filter = lambda q: q

    def create_table_model( self, admin ):
        """Create a table model for the given admin interface"""
        return self.table_model()

    def set_admin( self, admin ):
        """Switch to a different subclass, where admin is the admin object of the
        subclass"""
        logger.debug('set_admin called')
        self.admin = admin
        splitter = self.findChild( QtGui.QWidget, 'splitter' )
        self.table = self.TableWidget( splitter )
        self._table_model = self.create_table_model( admin )
        self.table.setModel( self._table_model )
        self.table_layout.insertWidget( 1, self.table )
        
        self.set_filters_and_actions( ( admin.get_filters(), admin.get_list_actions() ))

    def get_selection_getter(self): # !!!
        """:return: a function that returns all the objects corresponging to the selected rows in the
        table """

        def selection_getter():
            selection = []
            for row in set( map( lambda x: x.row(), self.table.selectedIndexes() ) ):
                selection.append( self._table_model._get_object(row) )
            return selection

        return selection_getter

    def set_filters_and_actions( self, filters_and_actions ):
        """sets filters for the tableview"""
        filters, actions = filters_and_actions
        from camelot.view.controls.actionsbox import ActionsBox
        logger.debug( 'setting filters for tableview' )
        if actions:
            selection_getter = self.get_selection_getter()
            self.actions = ActionsBox( self,
                                       self._table_model.get_collection_getter(),
                                       selection_getter )

            self.actions.setActions( actions )
            self.filters_layout.addWidget( self.actions )

class TableViewCases(ModelThreadTestCase):
    """Tests related to table views"""

    def create_select_view(self, admin):
        from PyQt4 import QtCore

        class SelectQueryTableProxy(QueryTableProxy):
            pass

        class SelectView(TableView):
            table_model = SelectQueryTableProxy

        widget = SelectView(admin)
        return widget

    def test_select_view_garbage_collection(self):
        """Create a select view and force its garbage collection"""
        import gc
        
        from camelot.admin.application_admin import ApplicationAdmin
        from camelot.model.i18n import Translation
        
        app_admin = ApplicationAdmin()
        admin = app_admin.get_entity_admin(Translation)

        for i in range(100):
            print i
            self.create_select_view(admin)
            gc.collect()