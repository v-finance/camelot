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

from ....core.qt import QtCore, Qt, QtWidgets
from .customeditor import AbstractCustomEditor

class BoolEditor(QtWidgets.QCheckBox, AbstractCustomEditor):
    """Widget for editing a boolean field"""

    editingFinished = QtCore.qt_signal()
    actionTriggered = QtCore.qt_signal(list, object)
    
    def __init__(self,
                 parent=None,
                 field_name = 'boolean'):
        QtWidgets.QCheckBox.__init__(self, parent)
        AbstractCustomEditor.__init__(self)
        self.setObjectName( field_name )
        self.clicked.connect( self._state_changed )

    def set_value(self, value):
        value = AbstractCustomEditor.set_value(self, value)
        if value:
            self.setCheckState(Qt.CheckState.Checked)
        else:
            self.setCheckState(Qt.CheckState.Unchecked)

    def get_value(self):
        value_loading = AbstractCustomEditor.get_value(self)
        if value_loading is not None:
            return value_loading
        state = self.checkState()
        if state==Qt.CheckState.Unchecked:
            return False
        return True

    def set_editable(self, editable):
        self.setDisabled( not editable )
        
    @QtCore.qt_slot( bool )
    def _state_changed(self, value=None):
        if not self.hasFocus():
            """
            Mac OS X's behaviour is not to move focus to a checkbox when it's
            state is changed. Therefore, the text_input_editing_finished method
            will not be called on a TextLineEditor when a checkbox is clicked
            after a text line has been changed, thus leading to a loss of the
            changes made in the text line. This issue is resolved by forcing
            the focus to the checkbox here.
            """
            self.setFocus()
        self.editingFinished.emit()

    def sizeHint(self):
        size = QtWidgets.QComboBox().sizeHint()
        return size


