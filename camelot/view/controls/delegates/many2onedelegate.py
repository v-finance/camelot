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

import logging

import six

from ....core.qt import py_to_variant, variant_to_py
from ....core.item_model import PreviewRole
from .. import editors
from .customdelegate import CustomDelegate, DocumentationMetaclass

logger = logging.getLogger('camelot.view.controls.delegates.many2onedelegate')

@six.add_metaclass(DocumentationMetaclass)
class Many2OneDelegate(CustomDelegate):
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
            admin = fa_values['admin']
            verbose_name = admin.get_verbose_object_name(value)
            item.setData(py_to_variant(verbose_name), PreviewRole)
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

    def setEditorData(self, editor, index):
        super(Many2OneDelegate, self).setEditorData(editor, index)
        if index.model() is None:
            return
        verbose_name = variant_to_py(index.model().data(index, PreviewRole))
        editor.set_verbose_name(verbose_name)



