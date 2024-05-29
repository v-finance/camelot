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

import itertools

from .customeditor import AbstractCustomEditor
from ....core.utils import ugettext
from ....core.qt import QtCore, QtGui, QtWidgets, Qt

class LanguageEditor(QtWidgets.QComboBox, AbstractCustomEditor):
    """A ComboBox that shows a list of languages, the editor takes
    as its value the ISO code of the language"""

    editingFinished = QtCore.qt_signal()
    actionTriggered = QtCore.qt_signal(list, object)
    
    def __init__(self, parent=None, field_name='language'):
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
            rows = itertools.count()
            localeModel = QtGui.QStandardItemModel(0, 1, app)
            localeModel.setObjectName('localeModel')
            if localeModel.rowCount() == 0:
                for language in QtCore.QLocale.Language._member_map_.values():
                    countries = set()
                    for locale in QtCore.QLocale.matchingLocales(language, QtCore.QLocale.Script.AnyScript, QtCore.QLocale.Country.AnyCountry):
                        country = locale.country()
                        if country not in countries:
                            countries.add(country)
                    localeModel.insertRows(localeModel.rowCount(), len(countries))
                    for country in countries:
                        language_name = QtCore.QLocale.languageToString(language)
                        country_name = QtCore.QLocale.countryToString(country)
                        row = next(rows)
                        localeModel.setData(localeModel.index(row, 0), '{} {}'.format(language_name, country_name))
                        localeModel.setData(localeModel.index(row, 0), language, Qt.ItemDataRole.UserRole)
                        localeModel.setData(localeModel.index(row, 0), country, Qt.ItemDataRole.UserRole+1)
        return localeModel

    @QtCore.qt_slot(int)
    def _activated(self, _index):
        self.editingFinished.emit()

    def set_editable(self, editable):
        self.setEnabled(editable)

    def set_value(self, value):
        self.setCurrentIndex(-1)
        if value is None:
            return
        if value.strip() == '':
            return
        locale = QtCore.QLocale(value)
        localeModel = self.get_locale_model()
        for row in range(localeModel.rowCount()):
            index = localeModel.index(row, 0)
            if localeModel.data(index, Qt.ItemDataRole.UserRole)==locale.language():
                if localeModel.data(index, Qt.ItemDataRole.UserRole+1)==locale.country():
                    self.setCurrentIndex(row)
                    return

    def get_value(self):
        current_index = self.currentIndex()
        if current_index >= 0:
            localeModel = self.get_locale_model()
            language = localeModel.data(localeModel.index(self.currentIndex(), 0), Qt.ItemDataRole.UserRole)
            country = localeModel.data(localeModel.index(self.currentIndex(), 0), Qt.ItemDataRole.UserRole+1)
            locale = QtCore.QLocale(language, country)
            return locale.name()
        return None
