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

from PyQt4.QtCore import Qt

from camelot.view.controls.editors import MonthsEditor
from camelot.view.controls.delegates.customdelegate import CustomDelegate, DocumentationMetaclass
from camelot.core.utils import variant_to_pyobject, ugettext
from camelot.view.proxy import ValueLoading

class MonthsDelegate(CustomDelegate):
    """MonthsDelegate

    custom delegate for showing and editing months and years
    """

    editor = MonthsEditor

    __metaclass__ = DocumentationMetaclass

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
        value = variant_to_pyobject( index.model().data( index, Qt.EditRole ) )
        
        value_str = u''
        if self._forever != None and value == self._forever:
            value_str = ugettext('Forever')
        elif value not in (None, ValueLoading):
            years, months = divmod( value, 12 )
            if years:
                value_str = value_str + ugettext('%i years ')%(years)
            if months:
                value_str = value_str + ugettext('%i months')%(months)        

        self.paint_text(painter, option, index, value_str)
        painter.restore()



