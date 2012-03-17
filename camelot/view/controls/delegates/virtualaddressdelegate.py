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

from customdelegate import CustomDelegate, DocumentationMetaclass
from camelot.view.controls import editors
from camelot.view.proxy import ValueLoading
# from camelot.view.art import Icon
from camelot.core.utils import variant_to_pyobject

class VirtualAddressDelegate(CustomDelegate):
    """
  """
  
    __metaclass__ = DocumentationMetaclass
  
    editor = editors.VirtualAddressEditor
  
    def __init__(self, parent=None, editable=True, address_type=None, **kwargs):
        super(VirtualAddressDelegate, self).__init__(parent=parent,
                                                     editable = editable,
                                                     address_type = address_type,
                                                     **kwargs )
        self._address_type = address_type
        
    def paint(self, painter, option, index):
        painter.save()
        self.drawBackground(painter, option, index)
        virtual_address = variant_to_pyobject(index.model().data(index, Qt.EditRole))
  
        if virtual_address and virtual_address!=ValueLoading:
            if virtual_address[0]:
                if not self._address_type:
                    self.paint_text(painter, option, index, u'%s : %s'%(virtual_address[0], virtual_address[1]), margin_left=0, margin_right=18)
                else:
                    self.paint_text(painter, option, index, u'%s'%virtual_address[1], margin_left=0, margin_right=18)

        painter.restore()



