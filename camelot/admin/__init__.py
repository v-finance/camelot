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
from abc import ABC, abstractmethod
from typing import List, Optional, Tuple, Union

from camelot.admin.action import State
from camelot.admin.admin_route import AdminRoute, Route, RouteWithRenderHint
from camelot.core.item_model.proxy import AbstractModelProxy
from camelot.core.utils import ugettext_lazy

class AbstractAdmin(AdminRoute, ABC):

    @abstractmethod
    def get_admin_route(self) -> Route:
        """Return the admin route for this admin."""

    @abstractmethod
    def get_verbose_name(self) -> Union[str, ugettext_lazy]:
        """Return the verbose name for this admin."""

    @abstractmethod
    def get_verbose_name_plural(self) -> Union[str, ugettext_lazy]:
        """Return the verbose name plural for this admin."""

    @abstractmethod
    def get_columns(self) -> List[str]:
        """Return the list of column field names for this admin."""

    @abstractmethod
    def get_static_field_attributes(self, field_names):
        """Return the static field attributes for the given field names."""

    @abstractmethod
    def get_list_action(self) -> Route:
        """Return the list action route for this admin."""

    @abstractmethod
    def get_proxy(self, objects) -> AbstractModelProxy:
        """Return a model proxy for the given objects."""

    @abstractmethod
    def _get_search_fields(self, substring):
        """Return the fields to search for the given substring."""

    @abstractmethod
    def get_list_actions(self):
        """Return the list actions for this admin."""

    @abstractmethod
    def get_filters(self):
        """Return the filters for this admin."""

    @abstractmethod
    def get_list_toolbar_actions(self):
        """Return the list toolbar actions for this admin."""

    @abstractmethod
    def _set_search_filter(self, proxy: AbstractModelProxy, actions: List[RouteWithRenderHint], search_text: Optional[str]):
        """Set the search filter on the given proxy based on the search text."""

    @abstractmethod
    def _set_filters(self, action_states:List[Tuple[Route, State]], proxy: AbstractModelProxy):
        """Set the filters on the given proxy based on the action states."""
