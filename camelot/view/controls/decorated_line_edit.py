#  ============================================================================
#
#  Copyright (C) 2007-2008 Conceptive Engineering bvba. All rights reserved.
#  www.conceptive.be / project-camelot@conceptive.be
#
#  This file is part of the Camelot Library.
#
#  This file may be used under the terms of the GNU General Public
#  License version 2.0 as published by the Free Software Foundation
#  and appearing in the file LICENSE.GPL included in the packaging of
#  this file.  Please review the following information to ensure GNU
#  General Public Licensing requirements will be met:
#  http://www.trolltech.com/products/qt/opensource.html
#
#  If you are unsure which license is appropriate for your use, please
#  review the following information:
#  http://www.trolltech.com/products/qt/licensing.html or contact
#  project-camelot@conceptive.be.
#
#  This file is provided AS IS with NO WARRANTY OF ANY KIND, INCLUDING THE
#  WARRANTY OF DESIGN, MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE.
#
#  For use of this library in commercial applications, please contact
#  project-camelot@conceptive.be
#
#  ============================================================================

from PyQt4 import QtGui

class DecoratedLineEdit(QtGui.QLineEdit):
    """
    A QLineEdit with additional decorations :
    
     * a background text, visible when there the line edit doesn't contain any text
    
    Use the user_input method to get the text that was entered by the user. 
    """
        
    def __init__(self, parent = None):
        QtGui.QLineEdit.__init__(self, parent)
        self._foreground_color = self.palette().color(self.foregroundRole())
        self._showing_background_text = False
        self._background_text = None

    def set_background_text(self, background_text):
        """Set the text to be displayed in the background when the line
        input does not contain any text
        :param background_text: the text to be shown, None if no text should be shown
        """
        self._hide_background_text()
        self._background_text = background_text
        if not self.hasFocus() and background_text!=None:
            self._show_background_text()
            
    def _show_background_text(self):
        if not self._showing_background_text and self.text().isEmpty() and self._background_text!=None:
            self._showing_background_text = True
            self._update_foreground_color()
            self.setText(unicode(self._background_text))

    def _hide_background_text(self):
        if self._showing_background_text and self._background_text!=None:
            self._showing_background_text = False
            self._update_foreground_color()
            self.setText('')
            
    def _update_foreground_color(self):
        from camelot.view.art import ColorScheme
        palette = self.palette()
        if self._showing_background_text:
            palette.setColor(self.foregroundRole(), ColorScheme.aluminium_1)
        else:
            palette.setColor(self.foregroundRole(), self._foreground_color)
        self.setPalette(palette)
            
    def focusInEvent(self, e):
        self._hide_background_text()
        QtGui.QLineEdit.focusInEvent(self, e)

    def focusOutEvent(self, e):
        self._show_background_text()
        QtGui.QLineEdit.focusOutEvent(self, e)
        
    def user_input(self):
        if self._showing_background_text:
            return u''
        return self.text()
    
    def set_user_input(self, text):
        if text!=None:
            self._hide_background_text()
            self.setText(text)
        else:
            if not self.hasFocus() and not self._showing_background_text:
                self.setText('')
                self._show_background_text()
