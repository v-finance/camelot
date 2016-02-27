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

from ....core.qt import QtGui, QtCore, QtWidgets
from camelot.view.art import ColorScheme
from .customeditor import AbstractCustomEditor

color = ColorScheme.yellow_1

class NoteEditor(QtWidgets.QLabel, AbstractCustomEditor):
    """An editor that behaves like a note, the editor hides itself when
    there is no text to display.  The default background color of the not
    is yellow, but can be changed through the `background_color` field
    attribute.
    """
    
    editingFinished = QtCore.qt_signal()
    
    def __init__( self, 
                  parent = None,
                  field_name = 'note',
                  **kwargs ):
        QtWidgets.QLabel.__init__( self, parent )
        AbstractCustomEditor.__init__( self )
        self.setObjectName( field_name )
        self.setTextFormat( QtCore.Qt.RichText )
        self.setSizePolicy( QtGui.QSizePolicy.Expanding,
                            QtGui.QSizePolicy.Minimum )
        self.setContentsMargins(0, 0, 0, 0)
        self.setFrameStyle(QtWidgets.QFrame.Box)
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


