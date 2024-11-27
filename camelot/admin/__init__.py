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
from typing import List, Union

from camelot.admin.admin_route import Route, AdminRoute
from camelot.core.item_model.proxy import AbstractModelProxy
from camelot.core.utils import ugettext_lazy

class AbstractAdmin(AdminRoute):

    def get_admin_route(self) -> Route:
        raise NotImplementedError

    def get_verbose_name_plural(self) -> Union[str, ugettext_lazy]:
        raise NotImplementedError

    def get_columns(self) -> List[str]:
        raise NotImplementedError

    def get_static_field_attributes(self, field_names):
        raise NotImplementedError

    def get_list_action(self) -> Route:
        raise NotImplementedError

    def get_proxy(self, objects) -> AbstractModelProxy:
        raise NotImplementedError

    def _get_search_fields(self, substring):
        raise NotImplementedError

    def get_list_actions(self):
        raise NotImplementedError

    def get_filters(self):
        raise NotImplementedError

    def get_list_toolbar_actions(self):
        raise NotImplementedError
