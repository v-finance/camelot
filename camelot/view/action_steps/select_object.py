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

from camelot.core.exception import CancelRequest
from camelot.core.naming import initial_naming_context
from camelot.view.action_runner import hide_progress_dialog

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

    verbose_name: str = field(init=False)
    single: bool = field(init=False)

    blocking: bool = True

    def __post_init__(self, value, admin, proxy, search_text):
        super().__post_init__(value, admin, proxy, search_text)
        self.single = False
        self.verbose_name = str(admin.get_verbose_name_plural())
        self.action_states = list()
        self._add_action_states(
            initial_naming_context.resolve(self.model_context_name),
            self.actions,
            self.action_states
        )
        # Allow custom column settings for SelectObjects
        self.group.append('SelectObjects')

    @staticmethod
    def _add_actions(admin, actions):
        actions.extend(admin.get_list_actions())
        actions.extend(admin.get_filters())
        actions.extend(admin.get_select_list_toolbar_actions())

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
        model_context = initial_naming_context.resolve(tuple(response['model_context_name']))
        proxy = model_context.proxy
        if proxy is not None:
            selected_rows = response['selected_rows']
            for i in range(len(selected_rows) // 2):
                first_row = selected_rows[2 * i]
                last_row = selected_rows[2 * i + 1]
                for obj in proxy[first_row:last_row + 1]:
                    objects.append(obj)
        return objects

@dataclass
class SelectObject(SelectObjects):

    def __post_init__(self, value, admin, proxy, search_text):
        super().__post_init__(value, admin, proxy, search_text)
        self.single = True
        self.verbose_name = str(admin.get_verbose_name())

    @classmethod
    def deserialize_result(cls, gui_context, response):
        objects = super().deserialize_result(gui_context, response)
        if objects:
            return objects[0]
