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
import datetime

import six

from ....core.qt import QtWidgets
from .customeditor import AbstractCustomEditor, set_background_color_palette
from camelot.core import constants

class TimeEditor(QtWidgets.QTimeEdit, AbstractCustomEditor):
  
    def __init__(self, 
                 parent,
                 editable = True,
                 field_name = 'time',
                 format = constants.camelot_time_format, **kwargs):
        QtWidgets.QTimeEdit.__init__(self, parent)
        AbstractCustomEditor.__init__(self)
        self.setObjectName( field_name )
        self.setDisplayFormat(format)
        self.setEnabled(editable)

    def set_value(self, value):
        value = AbstractCustomEditor.set_value(self, value)
        if value:
            self.setTime(value)
        else:
            self.setTime(self.minimumTime())
            
    def get_value(self):
        value = self.time()
        value = datetime.time(hour=value.hour(),
                              minute=value.minute(),
                              second=value.second())
        return AbstractCustomEditor.get_value(self) or value
        
    def set_field_attributes(self, **kwargs):
        super(TimeEditor, self).set_field_attributes(**kwargs)
        self.set_enabled(kwargs.get('editable', False))
        self.setToolTip(six.text_type(kwargs.get('tooltip') or ''))
      
    def set_enabled(self, editable=True):
        self.setEnabled(editable)

    def set_background_color( self, background_color ):
        set_background_color_palette( self.lineEdit(), background_color )




