#  ============================================================================
#
#  Copyright (C) 2007-2013 Conceptive Engineering bvba. All rights reserved.
#  www.conceptive.be / info@conceptive.be
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
#  visit www.python-camelot.com or contact info@conceptive.be
#
#  This file is provided AS IS with NO WARRANTY OF ANY KIND, INCLUDING THE
#  WARRANTY OF DESIGN, MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE.
#
#  For use of this library in commercial applications, please contact
#  info@conceptive.be
#
#  ============================================================================

from ...core.qt import QtCore, QtGui, Qt
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
    
    def __init__(self, field_name, text, field_attributes, admin, parent=None):
        """
        :param field_name: the name of the field
        :param text: user translatable string to be used as field label
        :param field_attributes: the field attributes associated with the field for which
        this is a label
        :param admin: the admin of the object of the field
        """
        super(FieldLabel, self).__init__(text, parent)
        if FieldLabel.font_width == None:
            FieldLabel.font_width = QtGui.QFontMetrics( QtGui.QApplication.font() ).size( Qt.TextSingleLine, 'A' ).width()
        show_field_attributes_action = QtGui.QAction(_('View attributes'), self)
        show_field_attributes_action.triggered.connect( self.show_field_attributes )
        self.addAction(show_field_attributes_action)
        self._field_name = field_name
        self._admin = admin
        self._field_attributes = field_attributes
        
    def sizeHint( self ):
        size_hint = super(FieldLabel, self).sizeHint()
        size_hint.setWidth( self.font_width * max( 20, len( self._field_name ) ) )
        return size_hint
    
    def get_value(self):
        return None
    
    def get_field_attributes(self):
        return self._field_attributes
    
    @QtCore.qt_slot()
    def show_field_attributes(self):
        action = ShowFieldAttributes()
        gui_context = FieldActionGuiContext()
        gui_context.editor = self
        gui_context.admin = self._admin
        action.gui_run(gui_context)




