#  ============================================================================
#
#  Copyright (C) 2007-2011 Conceptive Engineering bvba. All rights reserved.
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
import functools
import logging

from PyQt4 import QtGui

from camelot.view.art import Icon
from camelot.view.model_thread import post
from camelot.view.controls.progress_dialog import ProgressDialog
from camelot.admin.abstract_action import AbstractAction, \
    AbstractOpenFileAction, PrintProgressDialog, AbstractPrintHtmlAction

logger = logging.getLogger('camelot.admin.list_action')

class ListAction( AbstractAction ):
    """Abstract base class to implement list actions
    
.. attribute:: Options

    Use the class attribute Options, to let the user enter some options for the action.  Where
    options is a class with and admin definition.  The admin definition will be used to pop up
    an interface screen for an object of type Options.  Defaults to None.
    """

    Options = None
    
    def __init__( self, name, icon = None ):
        self._name = name
        self._icon = icon
        self.options = None

    def render( self, 
                parent, 
                collection_getter_getter, 
                selection_getter_getter ):
        """Returns a QWidget the user can use to trigger the action"""

        def clicked( action,
                     collection_getter_getter,
                     selection_getter_getter,
                     *args ):
            action.run( collection_getter_getter(), 
                        selection_getter_getter() )

        button = QtGui.QPushButton( unicode(self._name) )
        if self._icon:
            button.setIcon( self._icon.getQIcon() )
        button.clicked.connect( functools.partial( clicked,
                                                   self,
                                                   collection_getter_getter,
                                                   selection_getter_getter ) )
        return button

    def run( self, collection_getter, selection_getter ):
        """Overwrite this method to create an action that does something.  If the Options attribute
is specified, the default implementation of run will pop up a dialog requesting the user to
complete the options before executing the action.

:param collection_getter: a method that returns an iterator over all objects in the list
:param selection_getter: a method that returns an iterator over all selected objects in a list
:return: None if there was no Options class attribute or if Cancel was pressed, otherwise an object of of type Options

        """
        return self.get_options()

class ListActionFromGuiFunction( ListAction ):
    """Convert a function that is supposed to run in the GUI thread to a ListAction"""

    def __init__( self, name, gui_function, icon = None ):
        ListAction.__init__( self, name, icon )
        self._gui_function = gui_function

    def run( self, collection_getter, selection_getter ):
        self._gui_function( collection_getter, selection_getter )

class ListActionFromModelFunction( ListAction ):
    """Convert a function that is supposed to run in the model thread to a ListAction"""

    def __init__( self, 
                  name, 
                  model_function = None, 
                  icon = Icon( 'tango/22x22/categories/applications-system.png' ), 
                  collection_flush=False, 
                  selection_flush=False ):
        """List Action for a function that runs in the model thread
:param model_function: a function that has 3 arguments, the collection in the list view and the selection in the list view and the options.
:param collection_flush: flush all objects in the collection to the db and refresh them in the views
:param selection_flush: flush all objects in the selection to the db and refresh them in the views

Either give a model function as argument or overwrite the model_run method in a subclass.
        """
        ListAction.__init__( self, name, icon )
        self._model_function = model_function
        self._collection_flush = collection_flush
        self._selection_flush = selection_flush
        self.options = None

    def model_run(self, collection, selection, options):
        """This method will be called in the Model thread when the user initiates the
        action, this is the place to do all kind of model manipulation or querying things"""
        if self._model_function:
            self._model_function( collection, selection, options )
    
    def run( self, collection_getter, selection_getter ):
        """This method will be called in the GUI thread, when the user initiates the action"""
        self.options = super(ListActionFromModelFunction, self).run( collection_getter, selection_getter )
        progress = ProgressDialog( unicode(self._name) )
        
        if not self.options and self.Options:
            return self.options

        def create_request( collection_getter, selection_getter, options ):

            def request():
                from sqlalchemy.orm.session import Session
                from camelot.view.remote_signals import get_signal_handler
                sh = get_signal_handler()
                c = list(collection_getter())
                s = list(selection_getter())
                self.model_run( c, s, options )
                to_flush = []
                if self._selection_flush:
                    to_flush = s
                if self._collection_flush:
                    to_flush = c
                for o in to_flush:
                    Session.object_session( o ).flush( [o] )
                    sh.sendEntityUpdate( self, o )

            return request

        post( create_request( collection_getter, selection_getter, self.options ), 
              progress.finished,
              exception = progress.exception )
        progress.exec_()

class PrintHtmlListAction( AbstractPrintHtmlAction, ListActionFromModelFunction ):
    """List action that pops-up a print preview page, displaying html
    generated for a list or a a selection.  This class should be subclassed
    with a custom html function to create a custom report.
    """

    def __init__( self, 
                    name, 
                    icon = Icon( 'tango/22x22/actions/document-print.png' ) ):
        """        
        :param name: the label to be used on the action button
        :param icon: a camelot.view.art.Icon object, to be used as an icon on the
        action button

        """
        super(PrintHtmlListAction, self).__init__( name, icon)

    def run( self, collection_getter, selection_getter ):
        self.options = ListAction.run( self, collection_getter, selection_getter )
        progress = PrintProgressDialog( unicode(self._name) )
        progress.html_document = self.HtmlDocument
        progress.page_size = self.PageSize
        progress.page_orientation = self.PageOrientation
        
        if not self.options and self.Options:
            return self.options

        def create_request( collection_getter, selection_getter, options ):

            def request():
                html = self.html( collection_getter(),
                                  selection_getter(),
                                  options )
                return html

            return request

        post( create_request( collection_getter, selection_getter, self.options ), 
              progress.print_result, 
              exception = progress.exception )
        progress.exec_()

    def html( self, collection, selection, options ):
        """Overwrite this function to generate custom html to be printed

:param collection: the collection of objects displayed in the list
:param selection: the collection of selected objects in the list
:param options: an instance of the Options class attribute, if provided.
                the options allow the user to further specify how the html 
                should look like
                
        """
        return '<br/>'.join( list( unicode( o ) for o in collection ) )
    
class OpenFileListAction( ListActionFromModelFunction, AbstractOpenFileAction ):
    """List action used to open a file in the prefered application of the user.
    To be used for example to generate pdfs with reportlab and open them in
    the default pdf viewer.
    
    Set the suffix class attribute to the suffix the file should have
    eg: .txt or .pdf
    
    Overwrite the write file method to write the file wanted.
    """
    
    def __init__( self, name, icon = Icon( 'tango/22x22/actions/document-print.png' ) ):
        """
        """

        def model_function( collection, selection, options ):
            file_name = self.create_temp_file( options )
            self.write_file(file_name, collection, selection, options )
            self.open_file(file_name)

        ListActionFromModelFunction.__init__( self, name, model_function, icon )

    def write_file( self, file_name, collection, selection, options ):
        """Overwrite this function to generate the file to be opened
    :param file_name: the name of the file to which should be written
    :param collection: the collection of objects displayed in the list
    :param selection: the collection of selected objects in the list
    :param options: the options, if an Options class attribute was specified
        """
        file = open(file_name, 'w')
        for o in collection:
            file.write(unicode(o))
            file.write('\n')

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
