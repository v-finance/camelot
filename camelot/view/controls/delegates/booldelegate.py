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

from ....core.qt import variant_to_py, Qt, QtCore, QtWidgets
from .customdelegate import CustomDelegate, DocumentationMetaclass
from camelot.view.controls import editors
from camelot.view.proxy import ValueLoading

@six.add_metaclass(DocumentationMetaclass)
class BoolDelegate(CustomDelegate):
    """Custom delegate for boolean values"""

    editor = editors.BoolEditor

    def paint(self, painter, option, index):
        painter.save()
        self.drawBackground( painter, option, index )
        checked = variant_to_py(index.model().data(index, Qt.EditRole))

        check_option = QtWidgets.QStyleOptionButton()

        rect = QtCore.QRect(option.rect.left(),
                            option.rect.top(),
                            option.rect.width(),
                            option.rect.height())

        check_option.rect = rect
        check_option.palette = option.palette
        if (option.state & QtWidgets.QStyle.State_Selected):
            painter.fillRect(option.rect, option.palette.highlight())
        elif not self.editable:
            painter.fillRect(option.rect, option.palette.window())

        if checked in (ValueLoading, None):
            check_option.state = option.state | QtWidgets.QStyle.State_Off
        elif checked:
            check_option.state = option.state | QtWidgets.QStyle.State_On
        else:
            check_option.state = option.state | QtWidgets.QStyle.State_Off


        QtWidgets.QApplication.style().drawControl(QtWidgets.QStyle.CE_CheckBox,
                                               check_option,
                                               painter)

        painter.restore()


