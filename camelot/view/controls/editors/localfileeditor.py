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

import os.path

from ....core.qt import QtCore, QtWidgets, Qt
from .customeditor import CustomEditor, set_background_color_palette

from camelot.view.art import FontIcon
from camelot.core.utils import ugettext as _

from camelot.view.controls.decorated_line_edit import DecoratedLineEdit

class LocalFileEditor( CustomEditor ):
    """Widget for browsing local files and directories"""

    browse_icon =  FontIcon('columns') # 'tango/16x16/places/folder-saved-search.png'

    def __init__(self,
                 parent = None,
                 directory = False,
                 save_as = False,
                 file_filter = 'All files (*)',
                 field_name = 'local_file'):
        CustomEditor.__init__(self, parent)
        self.setSizePolicy( QtWidgets.QSizePolicy.Policy.Preferred,
                            QtWidgets.QSizePolicy.Policy.Fixed )
        self.setObjectName( field_name )
        self._directory = directory
        self._save_as = save_as
        self._file_filter = file_filter
        self.setup_widget()

    def setup_widget(self):
        """Called inside init, overwrite this method for custom
        file edit widgets"""
        layout = QtWidgets.QHBoxLayout()
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)

        browse_button = QtWidgets.QToolButton( self )
        browse_button.setFocusPolicy( Qt.FocusPolicy.ClickFocus )
        browse_button.setIcon( self.browse_icon.getQIcon() )
        browse_button.setToolTip( _('Browse') )
        browse_button.setAutoRaise( True )
        browse_button.clicked.connect( self.browse_button_clicked )

        self.filename = DecoratedLineEdit(self)
        self.filename.editingFinished.connect( self.filename_editing_finished )
        self.setFocusProxy( self.filename )

        layout.addWidget( self.filename )
        layout.addWidget( browse_button )
        self.setLayout( layout )

    @QtCore.qt_slot()
    def filename_editing_finished(self):
        self.valueChanged.emit()
        self.editingFinished.emit()

    @QtCore.qt_slot()
    def browse_button_clicked(self):
        current_directory = os.path.dirname( self.get_value() )
        if self._directory:
            value = QtWidgets.QFileDialog.getExistingDirectory(self,
                                                               directory = current_directory)
        elif self._save_as:
            value = QtWidgets.QFileDialog.getSaveFileName(self,
                                                          filter = self._file_filter,
                                                          directory = current_directory)
        else:
            value, _ = QtWidgets.QFileDialog.getOpenFileName(self,
                                                          directory = current_directory,
                                                          filter = self._file_filter)
        if value!='':
            value = os.path.abspath( str( value ) )
            self.filename.setText( value )
            self.valueChanged.emit()
            self.editingFinished.emit()

    def set_value(self, value):
        value = CustomEditor.set_value(self, value)
        if value:
            self.filename.setText( value )
        else:
            self.filename.setText( '' )
        self.valueChanged.emit()
        return value

    def get_value(self):
        return CustomEditor.get_value(self) or str( self.filename.text() )

    value = QtCore.qt_property( str, get_value, set_value )

    def set_tooltip(self, tooltip):
        super().set_tooltip(tooltip)
        if self.filename:
            self.filename.setToolTip(str(tooltip or ''))

    def set_background_color(self, background_color):
        super().set_background_color(background_color)
        if self.filename:
            set_background_color_palette(self.filename, background_color)

    def set_editable(self, editable):
        self.setEnabled(editable)

    def set_directory(self, directory):
        self._directory = directory
