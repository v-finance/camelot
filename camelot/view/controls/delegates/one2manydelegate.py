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

from dataclasses import dataclass, field
from typing import Optional, List
import itertools

from ....admin.admin_route import Route, RouteWithRenderHint
from ....admin.action.application_action import model_context_naming, model_context_counter
from ....admin.model_context import ObjectsModelContext
from ....core.naming import initial_naming_context
from ....core.qt import Qt
from camelot.view.controls import editors
from .customdelegate import CustomDelegate, DocumentationMetaclass

import logging
logger = logging.getLogger( 'camelot.view.controls.delegates.one2manydelegate' )

transient = initial_naming_context.resolve_context('transient')
transient_counter = itertools.count()

@dataclass
class One2ManyDelegate(CustomDelegate, metaclass=DocumentationMetaclass):
    """Custom delegate for many 2 one relations

  .. image:: /_static/onetomany.png
  """

    admin_route: Optional[Route] = None
    column_width: Optional[int] = None
    columns: List[str] = field(default_factory=list)
    rows: int = 5
    action_routes: List[Route] = field(default_factory=list)
    list_actions: List[RouteWithRenderHint] = field(default_factory=list)
    list_action: Optional[Route] = None

    def __post_init__(self, parent):
        super().__post_init__(parent)
        logger.debug( 'create one2manycolumn delegate' )

    @classmethod
    def get_standard_item(cls, locale, model_context):
        item = super().get_standard_item(locale, model_context)
        if model_context.value is not None:
            admin = model_context.field_attributes['admin']
            one2many_model_context = ObjectsModelContext(
                admin, admin.get_proxy(model_context.value), locale
            )
            one2many_model_context_name = model_context_naming.bind(str(next(model_context_counter)), one2many_model_context)
            item.roles[Qt.ItemDataRole.EditRole] = one2many_model_context_name
        return item

    def createEditor( self, parent, option, index ):
        logger.debug( 'create a one2many editor' )
        editor = editors.One2ManyEditor(parent, self.admin_route, self.column_width, self.columns,
                                        self.rows, self.action_routes, self.list_actions,
                                        self.list_action)
        editor.editingFinished.connect(self.commitAndCloseEditor)
        return editor

    def setEditorData( self, editor, index ):
        logger.debug( 'set one2many editor data' )
        if index.model() is None:
            return
        value = index.data(Qt.ItemDataRole.EditRole)
        editor.set_value(value)
        self.set_default_editor_data(editor, index)
        # update field actions
        self.update_field_action_states(editor, index)

    def setModelData( self, editor, model, index ):
        pass
