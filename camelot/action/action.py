
class Action(object):
  """An action that can be triggered by the user"""
  
  def run(self, parent_admin, parent):
    """
:param parent_admin: the admin interface to be used to lookup Admin classes
:param parent: the parent QT object that a GUI element created during the action can inherit
"""

class TableViewAction(Action):
  
  def __init__(self, entity, admin=None, verbose_name=None, parent_admin=None):
    from camelot.admin.application_admin import get_application_admin
    self.parent_admin = parent_admin or get_application_admin()
    if admin:
      self.admin = admin(self.parent_admin, entity)
    else:
      self.admin = self.parent_admin.getEntityAdmin(entity)
    self.entity = entity
    self.verbose_name = verbose_name
  
  def get_verbose_name(self):
    return self.verbose_name or self.admin.get_verbose_name_plural()
    
  def run(self, parent):
    tableview = self.admin.createTableView(parent)
    return tableview
    
def structure_to_action(structure):
  if isinstance(structure, (Action,)):
    return structure
  return TableViewAction(structure)