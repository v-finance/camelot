
from camelot.core.utils import ugettext_lazy as _

class ApplicationAction(object):
    """An action that can be triggered by the user at the application level"""

    def run(self, parent):
        """Execute the action, called within the gui thread
        
:param parent: a QWidget that can be used as a parent for widgets during the 
execution of the action
    """
        raise NotImplemented
    
    def get_verbose_name(self):
        """:return: the name of the action, as it can be shown to the user"""
        raise NotImplemented
    
    def get_icon(self):
        """:return: a camelot.view.art.Icon object"""
        raise NotImplemented
        
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

class TableViewAction(ApplicationAction):
    """An application action that opens a TableView for an Entity"""

    def __init__(self, entity, admin=None, verbose_name=None, parent_admin=None):
        from camelot.admin.application_admin import get_application_admin
        self.parent_admin = parent_admin or get_application_admin()
        if admin:
            self.admin = admin(self.parent_admin, entity)
        else:
            self.admin = self.parent_admin.get_entity_admin(entity)
        self.entity = entity
        self.verbose_name = verbose_name

    def get_verbose_name(self):
        return unicode(self.verbose_name or self.admin.get_verbose_name_plural())

    def run(self, parent):
        """:return: a table view that can be added to the workspace"""
        return self.admin.create_table_view(parent)
        
def structure_to_application_action(structure):
    """Convert a python structure to an ApplicationAction"""
    if isinstance(structure, (ApplicationAction,)):
        return structure
    return TableViewAction(structure)
