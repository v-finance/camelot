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

import six

from camelot.view.model_thread import post
from .choiceseditor import ChoicesEditor

no_choice = [(None, '')]

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
        choices = [(o, six.text_type(o)) for o in self._target.query.all()]
        # even if the field is required, the editor should be able to
        # handle None as a choice, for user convenience, None is put at
        # the end when required
        if self._nullable:
            return no_choice + choices
        else:
            return choices + no_choice

    def set_field_attributes(self, **fa):
        """Makes sure choices are not reset when changing the
        field attributes"""
        fa['choices'] = None
        super(OneToManyChoicesEditor, self).set_field_attributes(**fa)

    def set_value(self, value):
        # post to make sure the set value occurs after the set choices
        post( lambda:value, super( OneToManyChoicesEditor, self ).set_value )


