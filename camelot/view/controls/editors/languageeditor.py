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

from .customeditor import AbstractCustomEditor
from ....core.utils import ugettext
from ....core.qt import QtCore, QtGui, QtWidgets, Qt

class LanguageEditor(QtWidgets.QComboBox, AbstractCustomEditor):
    """A ComboBox that shows a list of languages, the editor takes
    as its value the ISO code of the language"""

    editingFinished = QtCore.qt_signal()
    
    def __init__(self, parent=None, field_name='language', **kwargs):
        """
        :param languages: a list of ISO codes with languages
        that are allowed in the combo box, if the list is empty, all languages
        are allowed (the default)
        """
        QtWidgets.QComboBox.__init__(self, parent)
        self.setEditable(True)
        AbstractCustomEditor.__init__(self)
        self.setObjectName(field_name)
        self.setModel(self.get_locale_model())
        self.lineEdit().setPlaceholderText(ugettext('Search'))
        self.setCurrentIndex(-1)
        self.activated.connect( self._activated )

    @staticmethod
    def get_locale_model():
        app = QtCore.QCoreApplication.instance()
        localeModel = app.findChild(QtGui.QStandardItemModel, 'localeModel')
        if localeModel is None:
            localeModel = QtGui.QStandardItemModel(0, 1, app)
            localeModel.setObjectName('localeModel')
            if localeModel.rowCount() == 0:
                localeModel.insertRows(0, QtCore.QLocale.Chewa + 1-QtCore.QLocale.C)
                for language in range(QtCore.QLocale.C, QtCore.QLocale.Chewa + 1):
                    names = set()
                    for locale in QtCore.QLocale.matchingLocales(language, QtCore.QLocale.AnyScript, QtCore.QLocale.AnyCountry):
                        locale_name = locale.name()
                        if locale_name not in names:
                            language_name = QtCore.QLocale.languageToString(locale.language())
                            names.add(locale_name)
                            localeModel.setData(localeModel.index(language-QtCore.QLocale.C, 0), '{} ({})'.format(language_name, locale_name))
                            localeModel.setData(localeModel.index(language-QtCore.QLocale.C, 0), language, Qt.UserRole)
        return localeModel

    @QtCore.qt_slot(int)
    def _activated(self, _index):
        self.editingFinished.emit()

    def set_field_attributes(self, **kwargs):
        super(LanguageEditor, self).set_field_attributes(**kwargs)
        self.setEnabled(kwargs.get('editable', False))

    def set_value(self, value):
        if value is None:
            self.setCurrentIndex(-1)
        else:
            locale = QtCore.QLocale(value)
            self.setCurrentIndex(locale.language()-QtCore.QLocale.C)

    def get_value(self):
        current_index = self.currentIndex()
        if current_index >= 0:
            localeModel = self.get_locale_model()
            language = localeModel.data(localeModel.index(self.currentIndex(), 0), Qt.UserRole)
            locale = QtCore.QLocale(language)
            return locale.name()
        return None
