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

from ....core.qt import Qt, variant_to_py, qtranslate
from camelot.view.controls.editors import MonthsEditor
from camelot.view.controls.delegates.customdelegate import CustomDelegate, DocumentationMetaclass
from camelot.core.utils import ugettext
from camelot.view.proxy import ValueLoading

@six.add_metaclass(DocumentationMetaclass)
class MonthsDelegate(CustomDelegate):
    """MonthsDelegate

    custom delegate for showing and editing months and years
    """

    editor = MonthsEditor

    def __init__(self, parent=None, forever=200*12, **kwargs):
        """
        :param forever: number of months that will be indicated as Forever, set
        to None if not appliceable
        """
        super(MonthsDelegate, self).__init__(parent=parent, **kwargs)
        self._forever = forever
        
    def sizeHint(self, option, index):
        q = MonthsEditor(None)
        return q.sizeHint()

    def paint(self, painter, option, index):
        painter.save()
        self.drawBackground(painter, option, index)
        value = variant_to_py( index.model().data( index, Qt.EditRole ) )
        
        value_str = u''
        if self._forever != None and value == self._forever:
            value_str = ugettext('Forever')
        elif value not in (None, ValueLoading):
            years, months = divmod( value, 12 )
            if years:
                value_str = qtranslate('%n years', n=years) + u' '
            if months:
                value_str = value_str + qtranslate('%n months', n=months)

        self.paint_text(painter, option, index, value_str)
        painter.restore()

