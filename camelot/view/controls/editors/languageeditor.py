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

from .customeditor import AbstractCustomEditor
from ....core.qt import QtCore, QtWidgets, py_to_variant, variant_to_py

class LanguageEditor(QtWidgets.QComboBox, AbstractCustomEditor):
    """A ComboBox that shows a list of languages, the editor takes
    as its value the ISO code of the language"""

    editingFinished = QtCore.qt_signal()
    language_choices = []
    
    def __init__(self, parent=None, languages=[], field_name='language', **kwargs):
        """
        :param languages: a list of ISO codes with languages
        that are allowed in the combo box, if the list is empty, all languages
        are allowed (the default)
        """
        QtWidgets.QComboBox.__init__(self, parent)
        AbstractCustomEditor.__init__(self)
        self.setObjectName( field_name )
        self.index_by_language = dict()
        languages = [QtCore.QLocale(lang).language() for lang in languages]
        if not self.language_choices:
            for i in range(QtCore.QLocale.C, QtCore.QLocale.Chewa + 1):
                if languages and (i not in languages):
                    continue
                language = QtCore.QLocale.Language(i)
                language_name = six.text_type(QtCore.QLocale.languageToString(language))
                self.language_choices.append( (language, language_name ) )
            self.language_choices.sort(key=lambda x:x[1])
        for i, (language, language_name) in enumerate( self.language_choices ):
            self.addItem( language_name, py_to_variant(language) )
            self.index_by_language[ language ] = i
        self.activated.connect( self._activated )

    @QtCore.qt_slot(int)
    def _activated(self, _index):
        self.editingFinished.emit()
            
    def set_field_attributes(self, **kwargs):
        super(LanguageEditor, self).set_field_attributes(**kwargs)
        self.setEnabled(kwargs.get('editable', False))
        
    def set_value(self, value):
        value = AbstractCustomEditor.set_value(self, value)
        if value:
            locale = QtCore.QLocale( value )
            self.setCurrentIndex( self.index_by_language[locale.language()] )
            
    def get_value(self):
        current_index = self.currentIndex()
        if current_index >= 0:
            language = variant_to_py(self.itemData(self.currentIndex()))
            locale = QtCore.QLocale( language )
            value = six.text_type( locale.name() )
        else:
            value = None
        return AbstractCustomEditor.get_value(self) or value




