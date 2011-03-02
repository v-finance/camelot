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

from camelot.core.utils import ugettext as _
from camelot.view.art import Icon
from camelot.admin.abstract_action import AbstractAction, AbstractOpenFileAction
from camelot.view.controls.progress_dialog import ProgressDialog

class ApplicationAction(AbstractAction):
    """
    An action that can be triggered by the user at the application level.
    
    .. attribute:: Options

    Use the class attribute Options, to let the user enter some options
    for the action.  Where options is a class with and admin definition.
    The admin definition will be used to pop up an interface screen for 
    an object of type Options. Defaults to None.
    """

    Options = None
    
    def run(self, parent):
        """Overwrite this method to create an action that does something.  If the Options attribute
        is specified, the default implementation of run will pop up a dialog requesting the user to
        complete the options before executing the action.
        
        :param parent: a QWidget that can be used as a parent for a widget opened by this action
        :return: None if there was no Options class attribute or if Cancel was pressed, otherwise
        an object of of type Options
        """
        return self.get_options()
    
    def get_verbose_name(self):
        """:return: the name of the action, as it can be shown to the user"""
        raise NotImplemented
    
    def get_icon(self):
        """:return: a camelot.view.art.Icon object"""
        raise NotImplemented

    def is_notification(self):
        """:return: False, subclasses should reimplement this."""
        return False
        
class ApplicationActionFromGuiFunction( ApplicationAction ):
    """Create an application action object from a function that is supposed to run
    in the GUI thread"""
    
    def __init__(self, name, gui_function, icon=None, verbose_name=None):
        """
        :param name: a unicode string naming this action
        :param gui_function: the function that will be called when the action
        is triggered, this function takes a its single argument a parent QObject
        :param icon: a camelot.view.art.Icon object
        :param verbose_name: the name used to display the action, if not given,
        the capitalized name will be used
        """

        self._name = name
        self._verbose_name = verbose_name or _(name.capitalize())
        self._icon = icon
        self._gui_function = gui_function
        
    def run(self, parent):
        self._gui_function(parent)
        
    def get_icon(self):
        return self._icon
    
    def get_verbose_name(self):
        return self._verbose_name

class ApplicationActionFromModelFunction( ApplicationActionFromGuiFunction ):
    """Convert a function that is supposed to run in the model thread to an ApplicationAction"""

    def __init__( self, name, model_function, icon = None, session_flush=False ):
        """
        :param model_function: a function that has one argument, the options requested by the user
        :param session_flush: flush all objects in the session and refresh them in the views
        """
        ApplicationActionFromGuiFunction.__init__( self, name, None, icon=icon )
        self._model_function = model_function
        self._session_flush = session_flush

    def run( self, parent = None ):
        from camelot.view.model_thread import post
        options = ApplicationAction.run( self, parent )
        progress = ProgressDialog( unicode(self._name) )
        
        if not options and self.Options:
            return options

        def create_request( options ):

            def request():
                self._model_function( options )

            return request

        post( create_request( self.options ), progress.finished, exception = progress.exception )
        progress.exec_()
        
class EntityAction(ApplicationAction):
    """Generic ApplicationAction that acts upon an Entity class"""

    def __init__(self, 
                 entity, 
                 admin=None, 
                 verbose_name=None, 
                 parent_admin=None,
                 icon=None,
                 notification = False):
        """
        :param notification: if set to True, this action will be visually 
        animated to attract the users attention. Defaults to False.
        """
        super(EntityAction, self).__init__()
        
        from camelot.admin.application_admin import get_application_admin
        self.parent_admin = parent_admin or get_application_admin()
        if admin:
            self.admin = admin(self.parent_admin, entity)
        else:
            self.admin = self.parent_admin.get_entity_admin(entity)
        self.entity = entity
        self.verbose_name = verbose_name
        self.icon = icon
        self.notification = notification

    def get_verbose_name(self):
        return unicode(self.verbose_name or self.admin.get_verbose_name_plural())

    def get_icon(self):
        return self.icon
        
    def is_notification(self):
        return self.notification
        
class TableViewAction(EntityAction):
    """An application action that opens a TableView for an Entity"""

    def run(self, parent):
        """:return: a table view that can be added to the workspace"""
        return self.admin.create_table_view(parent)
        
class NewViewAction(EntityAction):
    """An application action that opens a new view for an Entity"""

    def run(self, parent):
        """:return: a new view"""
        from camelot.view.workspace import show_top_level
        form = self.admin.create_new_view(parent=None)
        show_top_level( form, parent )
        return form
        
class OpenFileApplicationAction( ApplicationActionFromModelFunction, AbstractOpenFileAction ):
    """Application action used to open a file in the prefered application of the user.
    To be used for example to generate pdfs with reportlab and open them in
    the default pdf viewer.
    
    Set the suffix class attribute to the suffix the file should have
    eg: .txt or .pdf
    
    Overwrite the write file method to write the file wanted.
    """
    
    def __init__( self, name, icon = Icon( 'tango/22x22/actions/document-print.png' ) ):
        """
        """

        def model_function( options ):
            file_name = self.create_temp_file()
            self.write_file(file_name, options )
            self.open_file(file_name)

        ApplicationActionFromModelFunction.__init__( self, name, model_function, icon )

    def write_file( self, file_name, options ):
        """Overwrite this function to generate the file to be opened
    :param file_name: the name of the file to which should be written
    :param options: the options, if an Options class attribute was specified
        """
        file = open(file_name, 'w')
        file.write( 'Hello World' )
            
def structure_to_application_action(structure):
    """Convert a python structure to an ApplicationAction"""
    if isinstance(structure, (ApplicationAction,)):
        return structure
    return TableViewAction(structure)

