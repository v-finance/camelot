from PyQt4 import QtGui, QtCore
from camelot.view.art import Icon
from camelot.view.model_thread import post

class ListAction( object ):
    """Abstract base class to implement list actions"""

    def __init__( self, name, icon = None ):
        self._name = name
        self._icon = icon

    def render( self, parent, collection_getter, selection_getter ):
        """Returns a QWidget the user can use to trigger the action"""

        def create_clicked_function( self, collection_getter, selection_getter ):

            def clicked( *args ):
                self.run( collection_getter, selection_getter )

            return clicked

        button = QtGui.QPushButton( unicode(self._name) )
        if self._icon:
            button.setIcon( self._icon.getQIcon() )
        button.connect( button, QtCore.SIGNAL( 'clicked()' ), create_clicked_function( self, collection_getter, selection_getter ) )
        return button

    def run( self, collection_getter, selection_getter ):
        """Overwrite this method to create an action that does something"""
        raise NotImplementedError

class ListActionFromGuiFunction( ListAction ):
    """Convert a function that is supposed to run in the GUI thread to a ListAction"""

    def __init__( self, name, gui_function, icon = None ):
        ListAction.__init__( self, name, icon )
        self._gui_function = gui_function

    def run( self, collection_getter, selection_getter ):
        self._gui_function( collection_getter, selection_getter )

class ListActionFromModelFunction( ListAction ):
    """Convert a function that is supposed to run in the model thread to a FormAction"""

    def __init__( self, name, model_function, icon = None ):
        ListAction.__init__( self, name, icon )
        self._model_function = model_function

    def run( self, collection_getter, selection_getter ):
        progress = QtGui.QProgressDialog( 'Please wait', QtCore.QString(), 0, 0 )
        progress.setWindowTitle( unicode(self._name) )
        progress.show()

        def create_request( collection_getter ):

            def request():
                c = collection_getter()
                s = selection_getter()
                self._model_function( c, s )

            return request

        post( create_request( collection_getter ), progress.close, exception = progress.close )

class PrintHtmlListAction( ListActionFromModelFunction ):

    def __init__( self, name, icon = Icon( 'tango/22x22/actions/document-print.png' ) ):

        def model_function( collection, selection ):
            from camelot.view.export.printer import open_html_in_print_preview
            html = self.html( collection, selection )
            open_html_in_print_preview( html )

        ListActionFromModelFunction.__init__( self, name, model_function, icon )

    def html( self, collection, selection ):
        """Overwrite this function to generate custom html to be printed
    :arg collection: the collection of objects displayed in the list
    :arg selection: the collection of selected objects in the list
        """
        return '<br/>'.join( list( unicode( o ) for o in collection ) )

def structure_to_list_actions( structure ):
    """Convert a list of python objects to a list of list actions.  If the python
    object is a tuple, a ListActionFromGuiFunction is constructed with this tuple as arguments.  If
    the python object is an instance of a ListAction, it is kept as is.
    """

    def object_to_action( o ):
        if isinstance( o, ListAction ):
            return o
        return ListActionFromGuiFunction( o[0], o[1] )

    return [object_to_action( o ) for o in structure]
