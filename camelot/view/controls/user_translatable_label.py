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

from ...core.qt import QtCore, QtWidgets, Qt
from camelot.core.utils import ugettext_lazy
from camelot.core.utils import ugettext as _
from camelot.view.art import Icon

class TranslateLabelAction(QtWidgets.QAction):

    translate_icon = Icon( 'tango/16x16/apps/preferences-desktop-locale.png' )

    def __init__(self, parent):
        super(TranslateLabelAction, self).__init__(_('Change translation'), parent)
        self.setIcon(self.translate_icon.getQIcon())

class UserTranslatableLabel(QtWidgets.QLabel):
    """A QLabel that allows the user to translate the text contained
within by right clicking on it and selecting the appropriate submenu.
"""

    def __init__ (self, text, parent=None):
        """:param text: the text to be displayed within the label, this can
        be either a normal string or a ugettext_lazy string, only in the last
        case, the label will be translatable"""
        super(UserTranslatableLabel, self).__init__(six.text_type(text),
                                                    parent)
        self.setContextMenuPolicy(Qt.ActionsContextMenu)
        if isinstance(text, (ugettext_lazy)):
            self._text = text
            translate_action = TranslateLabelAction(self)
            translate_action.triggered.connect( self.change_translation )
            self.addAction(translate_action)
        else:
            self._text = None

    @QtCore.qt_slot()
    def change_translation(self):
        if self._text:
            new_translation, ok = QtWidgets.QInputDialog.getText(self,
                                                                 _('Change translation'),
                                                                 _('Translation'),
                                                                 QtWidgets.QLineEdit.Normal,
                                                                 six.text_type(self._text))
            # when the user presses ok in a blank dialog, the labels
            # should not disappear
            new_translation = six.text_type( new_translation ).strip()
            if ok and new_translation:
                from camelot.core.utils import set_translation
                self.setText(new_translation)
                set_translation(self._text._string_to_translate, new_translation)
                from camelot.view.model_thread import post
                post(self.create_update_translation_table(self._text._string_to_translate,
                                                          six.text_type(QtCore.QLocale().name()),
                                                          six.text_type(new_translation)))

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
