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

import logging

import six

from ....core.qt import py_to_variant
from ....core.item_model import PreviewRole
from .. import editors
from .customdelegate import CustomDelegate, DocumentationMetaclass

logger = logging.getLogger('camelot.view.controls.delegates.many2onedelegate')

class Many2OneDelegate( six.with_metaclass( DocumentationMetaclass,
                                            CustomDelegate ) ):
    """Custom delegate for many 2 one relations

  .. image:: /_static/manytoone.png

  Once an item has been selected, it is represented by its unicode representation
  in the editor or the table.  So the related classes need an implementation of
  their __unicode__ method.
  """

    editor = editors.Many2OneEditor

    def __init__(self,
                 parent=None,
                 admin=None,
                 editable=True,
                 **kwargs):
        logger.debug('create many2onecolumn delegate')
        assert admin != None
        CustomDelegate.__init__(self, parent, editable, **kwargs)
        self.admin = admin
        self._kwargs = kwargs
        self._width = self._width * 2

    @classmethod
    def get_standard_item(cls, locale, value, fa_values):
        item = super(Many2OneDelegate, cls).get_standard_item(locale, value, fa_values)
        if value is not None:
            value_str = fa_values['admin'].get_verbose_identifier(value)
            item.setData(py_to_variant(value_str), PreviewRole)
        return item

    def createEditor(self, parent, option, index):
        editor = editors.Many2OneEditor( self.admin,
                                         parent,
                                         editable=self.editable,
                                         **self._kwargs )
        if option.version != 5:
            editor.setAutoFillBackground(True)
        editor.editingFinished.connect( self.commitAndCloseEditor )
        return editor


