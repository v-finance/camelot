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
from camelot.core.utils import variant_to_pyobject, create_constant_function
from camelot.view.proxy import ValueLoading

import logging
logger = logging.getLogger('camelot.view.controls.delegates.many2onedelegate')


class Many2OneDelegate(CustomDelegate):
    """Custom delegate for many 2 one relations

  .. image:: /_static/manytoone.png

  Once an item has been selected, it is represented by its unicode representation
  in the editor or the table.  So the related classes need an implementation of
  their __unicode__ method.
  """

    __metaclass__ = DocumentationMetaclass

    editor = editors.Many2OneEditor

    def __init__(self,
                 parent=None,
                 admin=None,
                 embedded=False,
                 editable=True,
                 **kwargs):
        logger.debug('create many2onecolumn delegate')
        assert admin != None
        CustomDelegate.__init__(self, parent, editable, **kwargs)
        self.admin = admin
        self._embedded = embedded
        self._kwargs = kwargs
        self._width = self._width * 2

    def paint(self, painter, option, index):
        painter.save()
        self.drawBackground(painter, option, index)
        value = index.data(Qt.DisplayRole).toString()
        self.paint_text(painter, option, index, unicode(value) )
        painter.restore()

    def createEditor(self, parent, option, index):
        if self._embedded:
            editor = editors.EmbeddedMany2OneEditor( self.admin, 
                                                     parent,
                                                     editable = self.editable,
                                                     **self._kwargs )
        else:
            editor = editors.Many2OneEditor( self.admin, 
                                             parent,
                                             editable=self.editable,
                                             **self._kwargs )
        if option.version != 5:
            editor.setAutoFillBackground(True)
        editor.editingFinished.connect( self.commitAndCloseEditor )
        return editor

    def setEditorData(self, editor, index):
        value = variant_to_pyobject(index.data(Qt.EditRole))
        if value != ValueLoading:
            field_attributes = variant_to_pyobject(index.data(Qt.UserRole))
            editor.set_value(create_constant_function(value))
            editor.set_field_attributes(**field_attributes)
        else:
            editor.set_value(ValueLoading)

    def setModelData(self, editor, model, index):
        if editor.entity_instance_getter:
            model.setData(index, editor.entity_instance_getter)

#  def sizeHint(self, option, index):
#    return self._dummy_editor.sizeHint()



