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

from camelot.view.art import ColorScheme
from customeditor import AbstractCustomEditor

class NoteEditor(QtGui.QLabel, AbstractCustomEditor):
    """An editor that behaves like a note, the editor hides itself when
    there is no text to display"""
    
    editingFinished = QtCore.pyqtSignal()
    
    def __init__( self, 
                  parent = None,
                  field_name = 'note',
                  **kwargs ):
        QtGui.QLabel.__init__( self, parent )
        AbstractCustomEditor.__init__( self )
        self.setObjectName( field_name )
        self.setTextFormat( QtCore.Qt.RichText )  
        self.setSizePolicy( QtGui.QSizePolicy.Expanding,
                            QtGui.QSizePolicy.Minimum )
        style = """
        QLabel {
          margin: 0px;
          padding: 3px;
          border: 1px solid black;
          color: black;
          background-color: %s;
        }
        """%(ColorScheme.yellow_1.name())
        self.setStyleSheet( style );
        
    def set_value( self, value ):
        value = super( NoteEditor, self ).set_value( value )
        self.setVisible( value != None )
        if value:
            self.setText( unicode( value ) )
