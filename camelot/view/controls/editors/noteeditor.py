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

import six

from ....core.qt import QtGui, QtCore
from camelot.view.art import ColorScheme
from .customeditor import AbstractCustomEditor

color = ColorScheme.yellow_1

class NoteEditor(QtGui.QLabel, AbstractCustomEditor):
    """An editor that behaves like a note, the editor hides itself when
    there is no text to display.  The default background color of the not
    is yellow, but can be changed through the `background_color` field
    attribute.
    """
    
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
        self.setContentsMargins(0, 0, 0, 0)
        self.setFrameStyle(QtGui.QFrame.Box)
        self.setLineWidth(2)
        palette = self.palette()
        palette.setColor(self.backgroundRole(), color)
        palette.setColor(QtGui.QPalette.Shadow, QtGui.QColor('black'))
        palette.setColor(QtGui.QPalette.Dark, QtGui.QColor('black'))
        self.setPalette(palette)
        self.setAutoFillBackground(True)

    def set_value( self, value ):
        value = super( NoteEditor, self ).set_value( value )
        self.setVisible( value != None )
        if value:
            self.setText( six.text_type( value ) )
    
    def set_field_attributes(self, **kwargs):
        kwargs['background_color'] = kwargs.get('background_color') or color
        super(NoteEditor, self).set_field_attributes(**kwargs)

