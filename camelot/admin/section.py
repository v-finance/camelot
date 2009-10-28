from camelot.view.model_thread import model_function
from camelot.core.utils import ugettext as _

class Section(object):
    """A Section as displayed in the left pane of the application.  Each Section
  contains a list of SectionItems the user can click on.  Sections should be used
  in the definition of the ApplicationAdmin.

    class MyApplicationAdmin(ApplicationAdmin):
      sections = [Section('configuration')]

  .. image:: ../_static/configuration_section.png

    """

    def __init__(self, name, icon=None, items=[], verbose_name=None):
        self.name = name
        self.verbose_name = verbose_name
        self.icon = icon
        self.items = structure_to_section_items(items)

    def get_name(self):
        return self.name

    def get_verbose_name(self):
        return self.verbose_name or unicode(_(self.name)).capitalize()

    def get_icon(self):
        from camelot.view.art import Icon
        return self.icon or Icon('tango/32x32/apps/system-users.png')

    @model_function
    def get_items(self):
        return self.items

def structure_to_sections(structure):
    """Convert a list of python objects to a list of sections, using
  applying these rules on each of the elements in the list :

    - if the element is a instance of Section, leave it as it is
    - if the element is an instance of a basestr, construct a Section
      for it"""

    def rule(element):
        if isinstance(element, (Section,)):
            return element
        else:
            return Section(element)

    return [rule(section) for section in structure]

class SectionItem(object):
    """An item inside a section, the user can click on and trigger an action
  """

    def __init__(self, action, verbose_name=None):
        from camelot.admin.application_action import structure_to_application_action
        self.action = structure_to_application_action(action)
        self.verbose_name = verbose_name

    def get_verbose_name(self):
        return self.verbose_name or unicode(_(self.action.get_verbose_name())).capitalize()

    def get_action(self):
        return self.action

def structure_to_section_items(structure):

    def rule(element):
        if isinstance(element, (SectionItem,)):
            return element
        return SectionItem(element)

    return [rule(item) for item in structure]
