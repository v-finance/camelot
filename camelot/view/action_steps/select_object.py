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


from dataclasses import dataclass, InitVar, field

from camelot.core.exception import CancelRequest
from camelot.view.action_runner import hide_progress_dialog
from camelot.view.qml_view import qml_action_dispatch

from .item_view import OpenTableView, OpenQmlTableView

@dataclass
class SelectObjects(OpenTableView):
    """Select one or more object from a query.  The `yield` of this action step
    return a list of objects.

    :param admin: a :class:`camelot.admin.object_admin.ObjectAdmin` object
    :param search_text: a default string on which to search for in the selection
        dialog
    :param value: a query or a list of object from which the selection should
        be made.  If none is given, the default query from the admin is taken.
    """

    value: InitVar = None
    verbose_name_plural: str = field(init=False)

    def __post_init__(self, admin, value, proxy, search_text):
        if value is None:
            value = admin.get_query()
        super().__post_init__(admin, value, proxy, search_text)
        self.verbose_name_plural = str(admin.get_verbose_name_plural())
        self.actions = admin.get_list_actions().copy()
        self.actions.extend(admin.get_filters())
        self.actions.extend(admin.get_select_list_toolbar_actions())
        self.action_states = list()
        self._add_action_states(admin, admin.get_proxy(value), self.actions, self.action_states)

    @classmethod
    def gui_run(cls, gui_context, serialized_step):
        with hide_progress_dialog(gui_context):
            response, model = OpenQmlTableView.render(gui_context, 'SelectObjects', serialized_step)
            if not response['selection_count']:
                raise CancelRequest()
            return response

    @classmethod
    def deserialize_result(cls, gui_context, response):
        objects = []
        list_gui_context = qml_action_dispatch.get_context(response['gui_context_name'])
        model = list_gui_context.get_item_model()
        if model is not None:
            proxy = model.get_value()
            selected_rows = response['selected_rows']
            for i in range(len(selected_rows) // 2):
                first_row = selected_rows[2 * i]
                last_row = selected_rows[2 * i + 1]
                for obj in proxy[first_row:last_row + 1]:
                    objects.append(obj)
        return objects
