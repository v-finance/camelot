
class ApplicationAction(object):
    """An action that can be triggered by the user at the application level"""

    def run(self, parent):
        """Execute the action, called within the gui thread
        
:param parent: a QWidget that can be used as a parent for widgets during the 
execution of the action
    """
        raise NotImplemented()
    
    def get_verbose_name(self):
        """:return: the name of the action, as it can be shown to the user"""
        raise NotImplemented()

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
        tableview = self.admin.create_table_view(parent)
        return tableview

def structure_to_application_action(structure):
    """Convert a python structure to an ApplicationAction"""
    if isinstance(structure, (ApplicationAction,)):
        return structure
    return TableViewAction(structure)
