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

from ...core.qt import QtCore, QtGui, QtWidgets, Qt
from camelot.core.utils import ugettext as _
from camelot.admin.action.field_action import (ShowFieldAttributes,
                                               FieldActionGuiContext)
from .user_translatable_label import UserTranslatableLabel


class FieldLabel(UserTranslatableLabel):
    """A Label widget used to display the name of a field on a form.
    This label provides the user with the possibility to change the translation
    of the label and review its field attributes.
    """
    
    font_width = None
    font = None
    bold_font = None
    
    def __init__(self, field_name, text, admin, parent=None):
        """
        :param field_name: the name of the field
        :param text: user translatable string to be used as field label
        :param admin: the admin of the object of the field
        """
        super(FieldLabel, self).__init__(text, parent)
        if FieldLabel.font_width == None:
            FieldLabel.font = QtWidgets.QApplication.font()
            FieldLabel.bold_font = QtWidgets.QApplication.font()
            FieldLabel.bold_font.setBold(True)
            FieldLabel.font_width = QtGui.QFontMetrics(FieldLabel.font).size( Qt.TextSingleLine, 'A' ).width()
        show_field_attributes_action = QtWidgets.QAction(_('View attributes'), self)
        show_field_attributes_action.triggered.connect( self.show_field_attributes )
        self.addAction(show_field_attributes_action)
        self._field_name = field_name
        self._admin = admin
        self._field_attributes = dict()
        
    def sizeHint( self ):
        size_hint = super(FieldLabel, self).sizeHint()
        size_hint.setWidth( self.font_width * max( 20, len( self._field_name ) ) )
        return size_hint
    
    def get_value(self):
        return None
    
    def get_field_attributes(self):
        return self._field_attributes
    
    def set_field_attributes(self, **kwargs):
        self._field_attributes = kwargs
        # required fields font is bold
        nullable = kwargs.get('nullable', True)
        if not nullable:
            self.setFont(self.bold_font)
        else:
            self.setFont(self.font)

    @QtCore.qt_slot()
    def show_field_attributes(self):
        action = ShowFieldAttributes()
        gui_context = FieldActionGuiContext()
        gui_context.editor = self
        gui_context.admin = self._admin
        action.gui_run(gui_context)





