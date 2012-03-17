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
from camelot.view.model_thread import post
from choiceseditor import ChoicesEditor

class OneToManyChoicesEditor(ChoicesEditor):
  
    def __init__(self, 
                 parent, 
                 target=None, 
                 nullable=True, 
                 field_name='onetomanychoices',
                 **kwargs):
        super(OneToManyChoicesEditor, self).__init__(parent, **kwargs)
        self.setObjectName( field_name )
        assert target!=None
        self._target = target
        self._nullable = nullable
        post(self.get_choices, self.set_choices)

    def get_choices(self):
        additional_choices = []
        if self._nullable:
            additional_choices = [(None, '')]
        return additional_choices + [(o, unicode(o)) for o in self._target.query.all()]
        
    def set_field_attributes(self, editable=True, **kwargs):
        """Makes sure choices are not reset when changing the
        field attributes"""
        self.setEnabled(editable!=False)
        
    def set_value(self, value):
        # post to make sure the set value occurs after the set choices
        post( lambda:value, super( OneToManyChoicesEditor, self ).set_value )
