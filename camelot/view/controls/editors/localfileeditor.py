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

import os.path

import six

from ....core.qt import QtGui, QtCore, Qt
from .customeditor import CustomEditor, set_background_color_palette

from camelot.view.art import Icon
from camelot.core.utils import ugettext as _

from camelot.view.controls.decorated_line_edit import DecoratedLineEdit

class LocalFileEditor( CustomEditor ):
    """Widget for browsing local files and directories"""

    browse_icon =  Icon( 'tango/16x16/places/folder-saved-search.png' )

    def __init__(self, 
                 parent = None, 
                 field_name = 'local_file', 
                 directory = False, 
                 save_as = False,
                 file_filter = 'All files (*)',
                 **kwargs):
        CustomEditor.__init__(self, parent)
        self.setSizePolicy( QtGui.QSizePolicy.Preferred,
                            QtGui.QSizePolicy.Fixed )        
        self.setObjectName( field_name )
        self._directory = directory
        self._save_as = save_as
        self._file_filter = file_filter
        self.setup_widget()

    def setup_widget(self):
        """Called inside init, overwrite this method for custom
        file edit widgets"""
        layout = QtGui.QHBoxLayout()
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)

        browse_button = QtGui.QToolButton( self )
        browse_button.setFocusPolicy( Qt.ClickFocus )
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
            value = QtGui.QFileDialog.getExistingDirectory( self,
                                                            directory = current_directory )
        elif self._save_as:
            value = QtGui.QFileDialog.getSaveFileName( self,
                                                       filter = self._file_filter,
                                                       directory = current_directory )
        else:
            value = QtGui.QFileDialog.getOpenFileName( self,
                                                       filter = self._file_filter,
                                                       directory = current_directory )
        if value!='':
            value = os.path.abspath( six.text_type( value ) )
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
        return CustomEditor.get_value(self) or six.text_type( self.filename.text() )
    
    value = QtCore.qt_property( str, get_value, set_value )

    def set_field_attributes( self, **kwargs):
        super(LocalFileEditor, self).set_field_attributes(**kwargs)
        self.setEnabled(kwargs.get('editable', False))
        self._directory=kwargs.get('directory',False)
        if self.filename:
            set_background_color_palette(self.filename, kwargs.get('background_color', None))
            self.filename.setToolTip(six.text_type(kwargs.get('tooltip') or ''))

