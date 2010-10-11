from PyQt4 import QtGui
from PyQt4 import QtCore

from customeditor import AbstractCustomEditor

class LanguageEditor(QtGui.QComboBox, AbstractCustomEditor):
    """A ComboBox that shows a list of languages, the editor takes
    as its value the ISO code of the language"""

    editingFinished = QtCore.pyqtSignal()
    language_choices = []
    
    def __init__(self, parent=None, **kwargs):
        QtGui.QComboBox.__init__(self, parent)
        AbstractCustomEditor.__init__(self)
        self.index_by_language = dict()
        if not self.language_choices:
            for language in range(QtCore.QLocale.C, QtCore.QLocale.Chewa + 1):
                self.language_choices.append( (language, unicode( QtCore.QLocale.languageToString( language )) ) )
            self.language_choices.sort(key=lambda x:x[1])
        for i, (language, language_name) in enumerate( self.language_choices ):
            self.addItem( language_name, QtCore.QVariant(language) )
            self.index_by_language[ language ] = i
        self.activated.connect( self._activated )

    @QtCore.pyqtSlot(int)
    def _activated(self, _index):
        self.editingFinished.emit()
            
    def set_value(self, value):
        value = AbstractCustomEditor.set_value(self, value)
        if value:
            locale = QtCore.QLocale( value )
            self.setCurrentIndex( self.index_by_language[locale.language()] )
            
    def get_value(self):
        from camelot.core.utils import variant_to_pyobject
        current_index = self.currentIndex()
        if current_index >= 0:
            language = variant_to_pyobject(self.itemData(self.currentIndex()))
            locale = QtCore.QLocale( language )
            value = unicode( locale.name() )
        else:
            value = None
        return AbstractCustomEditor.get_value(self) or value