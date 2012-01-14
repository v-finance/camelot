#  ============================================================================
#
#  Copyright (C) 2007-2012 Conceptive Engineering bvba. All rights reserved.
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
from camelot.view.model_thread import model_function

class Section(object):
    """A Section as displayed in the left pane of the application.  Each Section
contains a list of SectionItems the user can click on.  Sections should be used
in the definition of the Application admin:

.. literalinclude:: ../../../../camelot_example/application_admin.py
   :start-after: begin section with action
   :end-before: end section with action

.. image:: /_static/controls/navigation_pane.png
    """
        
    def __init__( self, 
                  verbose_name,
                  application_admin,
                  icon=None, 
                  items=[] ):
        self.verbose_name = verbose_name
        self.icon = icon
        self.items = structure_to_section_items( items, application_admin )
        self.admin = application_admin

    def get_verbose_name(self):
        return self.verbose_name

    def get_icon(self):
        from camelot.view.art import Icon
        return self.icon or Icon('tango/32x32/apps/system-users.png')

    @model_function
    def get_items(self):
        return self.items

class SectionItem(object):
    """An item inside a section, the user can click on and trigger an action."""

    def __init__( self,
                  action, 
                  application_admin,
                  verbose_name = None ):
        from camelot.admin.action.application_action import structure_to_application_action
        self.verbose_name = verbose_name
        self.action = structure_to_application_action(action, application_admin)
        self.state = self.action.get_state( None )

    def get_verbose_name(self):
        return self.verbose_name or self.state.verbose_name

    def get_action(self):
        return self.action
        
    def get_icon(self):
        return self.state.icon
    
    def get_tooltip(self):
        return self.state.tooltip

    def get_modes(self):
        return self.state.modes
    
def structure_to_section_items(structure, application_admin):

    def rule(element):
        if isinstance(element, (SectionItem,)):
            return element
        return SectionItem(element, application_admin)

    return [rule(item) for item in structure]

