"""Test the behaviour of the qt bindings in various circumstances.
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

    def __init__( self, parent = None ):
        super(TableView, self).__init__( parent )
        widget_layout = QtGui.QVBoxLayout()
        self.table = QtGui.QTableView( self )
        self._table_model = self.table_model()
        self.table.setModel( self._table_model )
        widget_layout.addWidget( self.table )
        selection_getter = self.get_selection_getter()
        actions = [ListAction('test')]
        self.actions = ActionsBox( self,
                                   self._table_model.get_collection_getter(),
                                   selection_getter )

        self.actions.setActions( actions )
        widget_layout.addWidget( self.actions )
        self.setLayout( widget_layout )

    def get_selection_getter(self): # !!!
        """:return: a function that returns all the objects corresponging to the selected rows in the
        table """

        def selection_getter():
            selection = []
            for row in set( map( lambda x: x.row(), self.table.selectedIndexes() ) ):
                selection.append( self._table_model._get_object(row) )
            return selection

        return selection_getter

class TableViewCases(unittest.TestCase):
    """Tests related to table views"""

    def setUp(self):
        self.application = QtGui.QApplication([])

    def test_select_view_garbage_collection(self):
        """Create a select view and force its garbage collection"""
        import gc
        for i in range(100):
            print i
            
            class SelectQueryTableProxy(QueryTableProxy):
                pass
    
            class SelectView(TableView):
                table_model = SelectQueryTableProxy
    
            widget = SelectView()
            gc.collect()