"""
Form actions are objects that can be put in the form_actions list of the
object admin interfaces.  Those actions then appear on the form and can
be executed by the end users.  The most convenient method to create custom actions
is to subclass FormAction and implement a custom run method ::

  class MyAction(FormAction):

    def run(self, entity_getter):
      print 'Hello World'

  class Movie(Entity):
    title = Field(Unicode(60), required=True)

    Admin(EntityAdmin):
      list_display = ['title']
      form_actions = [MyAction('Hello')]

Several subclasses of FormAction exist to provide common use cases such as executing
a function in the model thread or printing a report.

To customize the look of the action button on the form, the render method should be
overwritten.
"""

from PyQt4 import QtGui, QtCore
from camelot.view.art import Icon
from camelot.view.model_thread import gui_function, post
from camelot.view.controls.progress_dialog import ProgressDialog

class FormAction( object ):
    """Abstract base class to implement form actions"""

    def __init__( self, name, icon = None ):
        """
        :param name: the name used in the button to trigger the action
        :param icon: Icon to be used in the button to trigger the action
        """
        self._name = name
        self._icon = icon

    @gui_function
    def render( self, parent, entity_getter ):
        """Returns a QWidget the user can use to trigger the action"""

        def create_clicked_function( self, entity_getter ):

            def clicked( *args ):
                self.run( entity_getter )

            return clicked

        button = QtGui.QPushButton( unicode(self._name) )
        if self._icon:
            button.setIcon( self._icon.getQIcon() )
        button.connect( button, QtCore.SIGNAL( 'clicked()' ), create_clicked_function( self, entity_getter ) )
        return button

    @gui_function
    def run( self, entity_getter ):
        """Overwrite this method to create an action that does something"""
        raise NotImplementedError

class FormActionFromGuiFunction( FormAction ):
    """Convert a function that is supposed to run in the GUI thread to a FormAction"""

    def __init__( self, name, gui_function, icon = None ):
        FormAction.__init__( self, name, icon )
        self._gui_function = gui_function

    @gui_function
    def run( self, entity_getter ):
        self._gui_function( entity_getter )

class FormActionProgressDialog(ProgressDialog):

    def print_result(self, html):
        from camelot.view.export.printer import open_html_in_print_preview_from_gui_thread
        self.close()
        open_html_in_print_preview_from_gui_thread(html)

class FormActionFromModelFunction( FormAction ):
    """Convert a function that is supposed to run in the model thread to a FormAction"""

    def __init__( self, name, model_function, icon = None, flush=False ):
        """
        :param name: the name of the action
        :param model_function: a function that has 1 arguments : the object on which to apply the action
        :param icon: an Icon
        :param flush: flush the object to the db and refresh it in the views
        """        
        FormAction.__init__( self, name, icon )
        self._model_function = model_function
        self._flush = flush

    @gui_function
    def run( self, entity_getter ):
        progress = FormActionProgressDialog(self._name)

        def create_request( entity_getter ):

            def request():
                from sqlalchemy.orm.session import Session
                from camelot.view.remote_signals import get_signal_handler                
                o = entity_getter()
                self._model_function( o )
                if self._flush:
                    sh = get_signal_handler()
                    Session.object_session( o ).flush( [o] )
                    sh.sendEntityUpdate( self, o )                    
                return True

            return request

        post( create_request( entity_getter ), progress.finished, exception = progress.exception )
        progress.exec_()

class PrintHtmlFormAction( FormActionFromModelFunction ):
    """Create an action for a form that pops up a print preview for generated html.
  Overwrite the html function to customize the html that should be shown::

    class PrintMovieAction(PrintHtmlFormAction):

      def html(self, movie):
        html = '<h1>' + movie.title + '</h1>'
        html += movie.description
      return html

    class Movie(Entity):
      title = Field(Unicode(60), required=True)
      description = Field(camelot.types.RichText)

      class Admin(EntityAdmin):
        list_display = ['title', 'description']
        form_actions = [PrintMovieAction('summary')]

  will put a print button on the form :

  .. image:: ../_static/formaction/print_html_form_action.png

    """

    def __init__( self, name, icon = Icon( 'tango/16x16/actions/document-print.png' ) ):
        FormActionFromModelFunction.__init__( self, name, self.html, icon )

    def html( self, o ):
        """Overwrite this function to generate custom html to be printed
        :arg o: the object that is displayed in the form"""
        return '<h1>' + unicode( o ) + '<h1>'

    @gui_function
    def run( self, entity_getter ):
        progress = FormActionProgressDialog(self._name)

        def create_request( entity_getter ):

            def request():
                o = entity_getter()
                return self.html( o )

            return request

        post( create_request( entity_getter ), progress.print_result, exception = progress.exception )
        progress.exec_()

def structure_to_form_actions( structure ):
    """Convert a list of python objects to a list of form actions.  If the python
    object is a tuple, a FormActionFromGuiFunction is constructed with this tuple as arguments.  If
    the python object is an instance of a FormAction, it is kept as is.
    """

    def object_to_action( o ):
        if isinstance( o, FormAction ):
            return o
        return FormActionFromGuiFunction( o[0], o[1] )

    return [object_to_action( o ) for o in structure]
