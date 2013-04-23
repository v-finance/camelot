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

from ....core.qt import variant_to_py, QtCore, Qt
from .customdelegate import CustomDelegate, DocumentationMetaclass, ValueLoading
from camelot.view.controls import editors

import six

class DateTimeDelegate( six.with_metaclass( DocumentationMetaclass,
                                            CustomDelegate) ):
    
    editor = editors.DateTimeEditor
    
    def __init__(self, parent=None, editable=True, **kwargs):
        CustomDelegate.__init__(self, parent, editable=editable, **kwargs)
        locale = QtCore.QLocale()
        self.datetime_format = locale.dateTimeFormat(locale.ShortFormat)
        
    def paint(self, painter, option, index):
        painter.save()
        self.drawBackground(painter, option, index)
        value = variant_to_py( index.model().data( index, Qt.EditRole ) )
        
        value_str = u''
        if value not in (None, ValueLoading):
            date_time = QtCore.QDateTime(
                value.year, 
                value.month, 
                value.day,
                value.hour, 
                value.minute, 
                value.second
            )
            value_str = date_time.toString(self.datetime_format)
            
        self.paint_text(painter, option, index, value_str, horizontal_align=Qt.AlignRight)
        painter.restore()



