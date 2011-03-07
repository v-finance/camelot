#  ============================================================================
#
#  Copyright (C) 2007-2010 Conceptive Engineering bvba. All rights reserved.
#  www.conceptive.be / project-camelot@conceptive.be
#
#  This file is part of the Camelot Library.
#
#  This file may be used under the terms of the GNU General Public
#  License version 2.0 as published by the Free Software Foundation
#  and appearing in the file license.txt included in the packaging of
#  this file.  Please review this information to ensure GNU
#  General Public Licensing requirements will be met.
#
#  If you are unsure which license is appropriate for your use, please
#  visit www.python-camelot.com or contact project-camelot@conceptive.be
#
#  This file is provided AS IS with NO WARRANTY OF ANY KIND, INCLUDING THE
#  WARRANTY OF DESIGN, MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE.
#
#  For use of this library in commercial applications, please contact
#  project-camelot@conceptive.be
#
#  ============================================================================
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
import logging

from PyQt4 import QtGui, QtCore
from camelot.admin.abstract_action import PrintProgressDialog
from camelot.view.art import Icon
from camelot.view.model_thread import gui_function, model_function, post
from camelot.view.controls.progress_dialog import ProgressDialog

logger = logging.getLogger('camelot.admin.form_action')

class FormAction( object ):
    """Abstract base class to implement form actions
    """

    def __init__( self, name, icon = None ):
        """
        :param name: the name used in the button to trigger the action
        :param icon: Icon to be used in the button to trigger the action
        """
        self._name = name
        self._icon = icon

    def get_name(self):
        """:return: the name to be used in the button to trigger the action"""
        return self._name

    def get_icon(self):
        """:return: the Icon to be used in the button to trigger the
action"""
        return self._icon

    def render( self, parent, entity_getter ):
        """:return: a QWidget the user can use to trigger the action, by default
returns a Button that will trigger the run method when clicked"""
        from camelot.view.controls.action_widget import ActionWidget
        return ActionWidget( self, entity_getter, parent=parent )

    def run( self, entity_getter ):
        """Overwrite this method to create an action that does something, the
        run method will be called within the gui thread.

        :param entity_getter: a function that returns the object displayed

        The entity_getter function should not be called within the gui
        thread, it exists for being able to pass it to the model thread.
        """
        raise NotImplementedError

    def enabled(self, entity):
        """Overwrite this method to have the action only enabled for
certain states of the entity displayed.  This method will be called
within the model thread.

:param entity: the entity currently in the form view
:return: True or False, returns True by default
        """
        if entity:
            return True

class FormActionFromGuiFunction( FormAction ):
    """Convert a function that is supposed to run in the GUI thread to a FormAction,
    or"""

    def __init__( self, name, gui_function, icon = None ):
        FormAction.__init__( self, name, icon )
        self._gui_function = gui_function

    @gui_function
    def run( self, entity_getter ):
        self._gui_function( entity_getter )

class FormActionFromModelFunction( FormAction ):
    """Convert a function that is supposed to run in the model thread to a
FormAction.  This type of action can be used to manipulate the model.
    """

    def __init__( self, name, model_function, icon = None, flush=False, enabled=lambda obj:True ):
        """
:param name: the name of the action
:param model_function: a function that has 1 arguments, the object
currently in the form, this function will be called whenever the
action is triggered.
:param icon: an Icon
:param flush: flush the object to the db and refresh it in the views, set this to true when the
model function changes the object.
:param enabled: a function that has 1 argument, the object on which the action would be applied
        """
        FormAction.__init__( self, name, icon )
        self._model_function = model_function
        self._flush = flush
        self._enabled = enabled

    @model_function
    def enabled(self, entity):
        """This function will be called in the model thread, to evaluate if the
button should be enabled.

:param entity: the object currently in the form
:return: True or False, defaults to True

        """
        return self._enabled( entity )

    @gui_function
    def run( self, entity_getter ):
        """When the run method is called, a progress dialog will apear while
the model function is executed.

:param entity_getter: a function that when called returns the object currently in the form.
        
        """
        progress = ProgressDialog(self._name)

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

class PrintHtmlFormAction(FormActionFromModelFunction):
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

the rendering of the html can be customised using the HtmlDocument attribute :

.. attribute:: HtmlDocument

the class used to render the html, by default this is
a QTextDocument, but a QtWebKit.QWebView can be used as well.

.. attribute:: PageSize

the page size, the default is QPrinter.A4

.. attribute:: PageOrientation

the page orientation, the default QPrinter.Portrait

.. image:: ../_static/simple_report.png
    """

    HtmlDocument = QtGui.QTextDocument
    PageSize = QtGui.QPrinter.A4
    PageOrientation = QtGui.QPrinter.Portrait

    def __init__(self, name, icon=Icon('tango/16x16/actions/document-print.png')):
        FormActionFromModelFunction.__init__(self, name, self.html, icon)

    def html(self, obj):
        """Overwrite this function to generate custom html to be printed
:param obj: the object that is displayed in the form
:return: a string with the html that should be displayed in a print preview window"""
        return '<h1>' + unicode( obj ) + '<h1>'

    @gui_function
    def run(self, entity_getter):
        progress = PrintProgressDialog(self._name)
        progress.html_document = self.HtmlDocument
        # the progress dialog can easily pass these parameters for us
        progress.page_size = self.PageSize
        progress.page_orientation = self.PageOrientation

        def create_request(entity_getter):

            def request():
                o = entity_getter()
                return self.html(o)

            return request

        post(create_request(entity_getter), progress.print_result, exception=progress.exception)
        progress.exec_()

class OpenFileFormAction( FormActionFromModelFunction ):
    """Form action used to open a file in the prefered application of the user.
To be used for example to generate pdfs with reportlab and open them in
the default pdf viewer.

.. attribute:: suffix

Set the suffix class attribute to the suffix the file should have
eg: .txt or .pdf, defaults to .txt
    """

    suffix = '.txt'

    def __init__( self, name, icon = Icon( 'tango/22x22/actions/document-print.png' ) ):

        def model_function( obj ):
            import os
            import tempfile
            file_descriptor, file_name = tempfile.mkstemp(suffix=self.suffix)
            os.close(file_descriptor)
            self.write_file(file_name, obj )
            url = QtCore.QUrl.fromLocalFile(file_name)
            logger.debug(u'open url : %s'%unicode(url))
            QtGui.QDesktopServices.openUrl(url)

        FormActionFromModelFunction.__init__( self, name, model_function, icon )

    def write_file( self, file_name, obj ):
        """
:param file_name: the name of the file to which should be written
:param obj: the object displayed in the form
:return: None

Overwrite this function to generate the file to be opened, this function will be
called when the user triggers the action.  It should write the requested file to the file_name.
This file will then be opened with the system default application for this type of file.
"""
        pass

class ChartFormAction( FormAction ):
    """Action that displays a chart, overwrite its chart
    method.
    """

    def run( self, entity_getter, options=None ):

        def create_request( entity_getter, options ):

            def request():
                o = entity_getter()
                return self.chart( o, options )

            return request

        dialog = ProgressDialog('Rendering Chart')
        post( create_request( entity_getter, options ), dialog.display_chart, dialog.exception )
        dialog.exec_()

    def chart(self, obj, options=None):
        """
        :obj: the object in the form when the user triggered the action
        :options: the options if applicable
        :return: a camelot.container.chartcontainer FigureContainer or AxesContainer object
        """
        from camelot.container.chartcontainer import PlotContainer
        return PlotContainer( [0,1,2,3] [0,2,4,9] )

class PixmapFormAction( FormAction ):
    """Action that displays an image, overwrite its image
    method.
    """

    def run( self, entity_getter, options=None ):

        def create_request( entity_getter, options ):

            def request():
                o = entity_getter()
                return self.pixmap( o, options )

            return request

        dialog = ProgressDialog('Rendering Image')
        post( create_request( entity_getter, options ), 
              dialog.display_pixmap, 
              dialog.exception )
        dialog.exec_()

    def pixmap(self, obj, options=None):
        """
        :obj: the object in the form when the user triggered the action
        :options: the options if applicable
        :return: a camelot.view.art.Pixmap object
        """
        return None
    
class DocxFormAction( FormActionFromModelFunction ):
    """Action that generates a .docx file and opens it using Word.  It does so by generating an xml document
with jinja templates that is a valid word document.  Implement at least its get_template method in a subclass
to make this action functional.
    """

    def __init__( self, name, icon = Icon( 'tango/16x16/mimetypes/x-office-document.png' ) ):
        FormActionFromModelFunction.__init__( self, name, self.open_xml, icon )

    def get_context(self, obj):
        """
:param obj: the object displayed in the form
:return: a dictionary with objects to be used as context when jinja fills up the xml document,
by default returns a context that contains obj"""
        return {'obj':obj}

    def get_environment(self, obj):
        """
:param obj: the object displayed in the form
:return: the jinja environment to be used to render the xml document, by default returns an
empty environment"""
        from jinja2 import Environment
        e = Environment()
        return e

    def get_template(self, obj):
        """
:param obj: the object displayed in the form
:return: the name of the jinja template for xml document.  A template can be constructed by
creating a document in MS Word and saving it as an xml file.  This file can then be manipulated by hand
to include jinja constructs."""
        raise NotImplemented

    def document(self, obj):
        """
:param obj: the object displayed in the form
:return: the xml content of the generated document. This method calls get_environment,
get_template and get_context to create the final document."""
        e = self.get_environment(obj)
        context = self.get_context(obj)
        t = e.get_template(self.get_template(obj))
        document_xml = t.render(context)
        return document_xml

    def open_xml(self, obj):
        from camelot.view.export.word import open_document_in_word
        import tempfile
        import os
        fd, fn = tempfile.mkstemp(suffix='.xml')
        docx_file = os.fdopen(fd, 'wb')
        docx_file.write(self.document(obj).encode('utf-8'))
        docx_file.close()
        open_document_in_word(fn)

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

