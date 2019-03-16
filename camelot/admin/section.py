#  ============================================================================
#
#  Copyright (C) 2007-2016 Conceptive Engineering bvba.
#  www.conceptive.be / info@conceptive.be
#
#  Redistribution and use in source and binary forms, with or without
#  modification, are permitted provided that the following conditions are met:
#      * Redistributions of source code must retain the above copyright
#        notice, this list of conditions and the following disclaimer.
#      * Redistributions in binary form must reproduce the above copyright
#        notice, this list of conditions and the following disclaimer in the
#        documentation and/or other materials provided with the distribution.
#      * Neither the name of Conceptive Engineering nor the
#        names of its contributors may be used to endorse or promote products
#        derived from this software without specific prior written permission.
#  
#  THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
#  ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
#  WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
#  DISCLAIMED. IN NO EVENT SHALL <COPYRIGHT HOLDER> BE LIABLE FOR ANY
#  DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
#  (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
#  LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
#  ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
#  (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
#  SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#
#  ============================================================================

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

    def get_items(self):
        return self.items

    def get_modes(self):
        return []

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
        if isinstance(element, (SectionItem, Section)):
            return element
        return SectionItem(element, application_admin)

    return [rule(item) for item in structure]



