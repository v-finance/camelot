"""Test the behaviour of the qt bindings
in various circumstances.
"""

import unittest
import logging
logger = logging.getLogger( 'test_qt_bindings' )

from PyQt4 import QtGui
#from PySide import QtGui

class ActionsBox(QtGui.QGroupBox):
    """A box containing actions to be applied to a view"""

    def __init__(self, parent, *args, **kwargs):
        QtGui.QGroupBox.__init__(self, 'Actions', parent)
        logger.debug('create actions box')
        self.args = args
        self.kwargs = kwargs

    def setActions(self, actions):
        action_widgets = []
        logger.debug('setting actions')
        # keep action object alive to allow them to receive signals
        self.actions = actions
        layout = QtGui.QVBoxLayout()
        for action in actions:
            action_widget = action.render(self, *self.args)
            layout.addWidget(action_widget)
            action_widgets.append(action_widget)
        self.setLayout(layout)
        return action_widgets
    
class ListAction( object ):
    
    def __init__( self, name, icon = None ):
        self._name = name
        self._icon = icon
        self.options = None

    def render( self, parent, collection_getter, selection_getter ):
        """Returns a QWidget the user can use to trigger the action"""

        def create_clicked_function( self, collection_getter, selection_getter ):

            def clicked( *args ):
                self.run( collection_getter, selection_getter )

            return clicked

        button = QtGui.QPushButton( unicode(self._name) )
        if self._icon:
            button.setIcon( self._icon.getQIcon() )
        button.clicked.connect( create_clicked_function( self, collection_getter, selection_getter ) )
        return button
    
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

    def set_admin( self, admin ):
        """Switch to a different subclass, where admin is the admin object of the
        subclass"""
        logger.debug('set_admin called')
        self.admin = admin
        splitter = self.findChild( QtGui.QWidget, 'splitter' )
        self.table = self.TableWidget( splitter )
        self._table_model = self.table_model()
        self.table.setModel( self._table_model )
        self.table_layout.insertWidget( 1, self.table )
        
        self.set_filters_and_actions( [ListAction('test')] )

    def get_selection_getter(self): # !!!
        """:return: a function that returns all the objects corresponging to the selected rows in the
        table """

        def selection_getter():
            selection = []
            for row in set( map( lambda x: x.row(), self.table.selectedIndexes() ) ):
                selection.append( self._table_model._get_object(row) )
            return selection

        return selection_getter

    def set_filters_and_actions( self, actions ):
        """sets filters for the tableview"""
        selection_getter = self.get_selection_getter()
        self.actions = ActionsBox( self,
                                   self._table_model.get_collection_getter(),
                                   selection_getter )

        self.actions.setActions( actions )
        self.filters_layout.addWidget( self.actions )

class TableViewCases(unittest.TestCase):
    """Tests related to table views"""

    def setUp(self):
        self.application = QtGui.QApplication([])
        
    def create_select_view(self, admin):

        class SelectQueryTableProxy(QueryTableProxy):
            pass

        class SelectView(TableView):
            table_model = SelectQueryTableProxy

        widget = SelectView(admin)
        return widget

    def test_select_view_garbage_collection(self):
        """Create a select view and force its garbage collection"""
        import gc
        for i in range(100):
            print i
            self.create_select_view(None)
            gc.collect()