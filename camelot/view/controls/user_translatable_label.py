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

from PyQt4 import QtGui, QtCore
from PyQt4.QtCore import Qt

from camelot.core.utils import ugettext_lazy
from camelot.core.utils import ugettext as _
from camelot.view.art import Icon

class TranslateLabelAction(QtGui.QAction):
    
    translate_icon = Icon( 'tango/16x16/apps/preferences-desktop-locale.png' )
    
    def __init__(self, parent):
        super(TranslateLabelAction, self).__init__(_('Change translation'), parent)
        self.setIcon(self.translate_icon.getQIcon())

class UserTranslatableLabel(QtGui.QLabel):
    """A QLabel that allows the user to translate the text contained 
within by right clicking on it and selecting the appropriate submenu.
"""

    def __init__ (self, text, parent=None):
        """:param text: the text to be displayed within the label, this can
        be either a normal string or a ugettext_lazy string, only in the last
        case, the label will be translatable"""
        super(UserTranslatableLabel, self).__init__(unicode(text), 
                                                    parent)
        self.setContextMenuPolicy(Qt.ActionsContextMenu)
        if isinstance(text, (ugettext_lazy)):
            self._text = text
            translate_action = TranslateLabelAction(self)
            translate_action.triggered.connect( self.change_translation )
            self.addAction(translate_action)
        else:
            self._text = None
            
    @QtCore.pyqtSlot()
    def change_translation(self):
        if self._text:
            new_translation, ok = QtGui.QInputDialog.getText(self, 
                                                             _('Change translation'),
                                                             _('Translation'),
                                                             QtGui.QLineEdit.Normal,
                                                             unicode(self._text))
            # when the user presses ok in a blank dialog, the labels
            # should not disappear
            new_translation = unicode( new_translation ).strip()
            if ok and new_translation:
                from camelot.core.utils import set_translation
                self.setText(new_translation)
                set_translation(self._text._string_to_translate, new_translation)
                from camelot.view.model_thread import post
                post(self.create_update_translation_table(self._text._string_to_translate,
                                                          unicode(QtCore.QLocale().name()),
                                                          unicode(new_translation)))
                
    def create_update_translation_table(self, source, language, value):
        
        def update_translation_table():
            from camelot.model.i18n import Translation
            from sqlalchemy.orm.session import Session
            t = Translation.get_by(source=source, language=language)
            if not t:
                t = Translation(source=source, language=language)
            t.value = value
            Session.object_session( t ).flush( [t] )
            
        return update_translation_table
                



