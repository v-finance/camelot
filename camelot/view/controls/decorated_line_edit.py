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



from ...core.qt import QtCore, QtGui, QtWidgets
from ..art import ColorScheme


class DecoratedLineEdit(QtWidgets.QLineEdit):
    """
    A QLineEdit with additional decorations :
    
     * a validity, which will trigger the background color

    """
      
    arrow_down_key_pressed = QtCore.qt_signal()
    
    _font_metrics = None
    _background_color = None
      
    def __init__(self, parent = None):
        super( DecoratedLineEdit, self ).__init__( parent = parent )
        if self._font_metrics is None:
            self._font_metrics = QtGui.QFontMetrics(QtWidgets.QApplication.font())
            self._background_color = self.palette().color(self.backgroundRole())
        self.textChanged.connect(self.text_changed)

    def set_minimum_width(self, width):
        """Set the minimum width of the line edit, measured in number of 
        characters.  Use a number of characters the content of the editor
        is unknown, but a sample string can be used if the input pattern
        is known (such as a formatted date or a code) for greater accuracy.
        
        :param width: the number of characters that should be visible in the
            editor or a string that should fit in the editor
        """
        if isinstance( width, str ):
            self.setMinimumWidth( self._font_metrics.horizontalAdvance( width ) )
        else:
            self.setMinimumWidth( self._font_metrics.averageCharWidth() )

    @QtCore.qt_slot(str)
    def text_changed(self, text):
        self._update_background_color()

    def setValidator(self, validator):
        if self.validator() != validator:
            super(DecoratedLineEdit, self).setValidator(validator)
        # updating the bg color should only be needed when the validat did
        # actually change, however this seems to break the virtualaddresseditor
        # when the existing input is invalid
        self._update_background_color()

    def _update_background_color(self):
        palette = self.palette()
        if self.hasAcceptableInput():
            palette.setColor(self.backgroundRole(), self._background_color)
        else:
            palette.setColor(self.backgroundRole(), ColorScheme.orange_2)
        self.setPalette(palette)
        
    def keyPressEvent(self, e):
        if e.key() == QtCore.Qt.Key.Key_Down:
            self.arrow_down_key_pressed.emit()
        
        QtWidgets.QLineEdit.keyPressEvent(self, e)


