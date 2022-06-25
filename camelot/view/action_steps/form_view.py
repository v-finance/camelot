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

"""
Various ``ActionStep`` subclasses to create and manipulate a form view in the
context of the `Qt` model-view-delegate framework.
"""
from typing import Dict
from dataclasses import dataclass, field
import json

from ..controls.formview import FormView
from ..forms import AbstractForm
from ..proxy.collection_proxy import CollectionProxy
from ..workspace import show_top_level
from ...admin.action.base import ActionStep, RenderHint
from ...admin.admin_route import AdminRoute
from ...core.item_model import AbstractModelProxy, ProxyRegistry
from ...core.naming import initial_naming_context
from ...core.qt import is_deleted
from ...core.serializable import DataclassSerializable
from .item_view import AbstractCrudView


@dataclass
class OpenFormView(AbstractCrudView):
    """Open the form view for a list of objects, in a non blocking way.

    :param object: the object to display in the form view.
    :param proxy: a model proxy that represents the underlying collection where the given object is part of.
    :param admin: the admin class to use to display the form

    .. attribute:: row

        Which object to display when opening the form, defaults to the first
        object, so row is 0 by default

    .. attribute:: actions

        A list of `camelot.admin.action.base.Action` objects to be displayed
        at the side of the form, this defaults to the ones returned by the
        admin

    .. attribute:: top_toolbar_actions

        A list of `camelot.admin.action.base.Action` objects to be displayed
        at the top toolbar of the form, this defaults to the ones returned by the
        admin

    """

    fields: Dict[str, dict] = field(init=False)
    form: AbstractForm = field(init=False)
    admin_route: AdminRoute = field(init=False)
    row: int = field(init=False)
    form_state: str = field(init=False)

    def __post_init__(self, admin, value, proxy):
        assert value is not None
        assert (proxy is None) or (isinstance(proxy, AbstractModelProxy))
        self.fields = dict((f, {
            'hide_title':fa.get('hide_title', False),
            'verbose_name':str(fa['name']),
            }) for f, fa in admin.get_fields())
        self.form = admin.get_form_display()
        self.admin_route = admin.get_admin_route()
        if proxy is None:
            proxy = admin.get_proxy([value])
        self.row = proxy.index(value)
        self.close_route = AdminRoute._register_action_route(
            self.admin_route, admin.form_close_action
        )
        self.title = admin.get_verbose_name()
        self.form_state = admin.form_state
        self.actions = admin.get_form_actions(None).copy()
        self.actions.extend(admin.get_form_toolbar_actions())
        super().__post_init__(admin, value, proxy)

    def get_objects(self):
        """Use this method to get access to the objects to change in unit tests

        :return: the list of objects to display in the form view
        """
        return ProxyRegistry.get(self.proxy_route).get_model()

    def get_admin(self):
        """Use this method to get access to the admin in unit tests"""
        return initial_naming_context.resolve(self.admin_route)

    @classmethod
    def render(self, gui_context, step):
        model = CollectionProxy(tuple(step['admin_route']))
        list(model.add_columns((fn for fn, fa in step['fields'].items())))
        model.set_value(step['proxy_route'])
        form = FormView(
            title=step['title'], admin_route=step['admin_route'],
            close_route=tuple(step['close_route']), model=model,
            fields=step['fields'], form_display=step['form'],
            index=step['row']
        )
        form.set_actions([(rwr['route'], RenderHint._value2member_map_[rwr['render_hint']]) for rwr in step['actions']])
        for action_route, action_state in step['action_states']:
            form.set_action_state(form, tuple(action_route), action_state)
        return form

    @classmethod
    def gui_run(cls, gui_context, serialized_step):
        step = json.loads(serialized_step)
        window = gui_context.get_window()
        formview = cls.render(gui_context, step)
        if formview is not None:
            formview.setObjectName('form.{}.{}'.format(
                step['admin_route'], id(formview)
            ))
            show_top_level(formview, window, step['form_state'])


@dataclass
class ChangeFormIndex(ActionStep, DataclassSerializable):

    def gui_run( self, gui_context ):
        # a pending request might change the number of rows, and therefor
        # the new index
        # submit all pending requests to the model thread
        if is_deleted(gui_context.widget_mapper):
            return
        gui_context.widget_mapper.model().timeout_slot()
        # wait until they are handled
        super(ChangeFormIndex, self).gui_run(gui_context)

class ToFirstForm(ChangeFormIndex):
    """
    Show the first object in the collection in the current form
    """

    def gui_run( self, gui_context ):
        super(ToFirstForm, self).gui_run(gui_context)
        gui_context.widget_mapper.toFirst()

class ToNextForm(ChangeFormIndex):
    """
    Show the next object in the collection in the current form
    """

    def gui_run( self, gui_context ):
        super(ToNextForm, self).gui_run(gui_context)
        gui_context.widget_mapper.toNext()
        
class ToLastForm(ChangeFormIndex):
    """
    Show the last object in the collection in the current form
    """

    def gui_run( self, gui_context ):
        super(ToLastForm, self).gui_run(gui_context)
        gui_context.widget_mapper.toLast()
        
class ToPreviousForm(ChangeFormIndex):
    """
    Show the previous object in the collection in the current form
    """

    def gui_run( self, gui_context ):
        super(ToPreviousForm, self).gui_run(gui_context)
        gui_context.widget_mapper.toPrevious()

