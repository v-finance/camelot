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


from ...core.qt import QtGui, QtWidgets, Qt


class FieldLabel(QtWidgets.QLabel):
    """A Label widget used to display the name of a field on a form.
    This label provides the user with the possibility to change the translation
    of the label and review its field attributes.
    """
    
    font_width = None
    font = None
    bold_font = None
    
    def __init__(self, text, parent):
        """
        :param text: user translatable string to be used as field label
        :param parent: the parent widget
        
        Field labels should be created with a parent since setting the
        field attributes might 'visualize' them, so they could appear as
        'ghost' windows when they have no parent
        """
        super().__init__(str(text), parent)
        if FieldLabel.font_width == None:
            FieldLabel.font = QtWidgets.QApplication.font()
            FieldLabel.bold_font = QtWidgets.QApplication.font()
            FieldLabel.bold_font.setBold(True)
            FieldLabel.font_width = QtGui.QFontMetrics(FieldLabel.font).size( Qt.TextFlag.TextSingleLine, 'A' ).width()

    def set_visible(self, visible):
        self.setVisible(visible)

    def set_nullable(self, nullable):
        if not nullable:
            self.setFont(self.bold_font)
        else:
            self.setFont(self.font)
