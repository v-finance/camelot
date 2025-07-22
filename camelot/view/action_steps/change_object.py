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
import typing
from dataclasses import dataclass, field
from typing import List, Union

from camelot.admin.icon import Icon
from camelot.core.naming import initial_naming_context
from camelot.core.utils import ugettext_lazy, ugettext_lazy as _
from .form_view import OpenFormView
from .item_view import UpdateTableView
from ...admin.admin_route import AdminRoute


@dataclass
class ChangeObject(OpenFormView):
    """
    Pop up a form for the user to change an object

    :param obj: the object to change
    :param admin: an instance of an admin class to use to edit the object

    .. attribute:: accept

        The text shown in the accept button

    .. attribute:: reject

        The text shown in the reject button

    """

    subtitle: typing.Union[str, ugettext_lazy, None] = field(init=False, default_factory=lambda: _('Complete the form and press the OK button'))
    accept: typing.Union[str, ugettext_lazy] = field(init=False, default_factory=lambda: _('OK'))
    reject: typing.Union[str, ugettext_lazy] = field(init=False, default_factory=lambda: _('Cancel'))
    blocking: bool = True

    def __post_init__(self, value, admin, proxy):
        super().__post_init__(value, admin, proxy)
        self.title = admin.get_verbose_name()
        self.qml = True

    @staticmethod
    def _add_actions(admin, actions):
        actions.extend(admin.get_form_actions(None))

    def get_object( self ):
        """Use this method to get access to the object to change in unit tests

        :return: the object to change
        """
        return self.get_objects()[0]


@dataclass
class ChangeObjects(UpdateTableView):
    """
    Pop up a list for the user to change objects

    :param objects: a list of objects to change
    :param admin: an instance of an admin class to use to edit the objects.
    :param validate: validate all objects before allowing the user to change
        them.  If objects are not validated before showing them, only the
        visible objects will be validated.  But validation of all  objects might
        take a lot of time.

    .. image:: /_static/listactions/import_from_file_preview.png

    This action step can be customised using these attributes :

    .. attribute:: window_title

        the window title of the dialog shown

    .. attribute:: title

        the title of the dialog shown

    .. attribute:: subtitle

        the subtitle of the dialog shown

    .. attribute:: icon

        the :class:`camelot.admin.icon.Icon` in the top right corner of
        the dialog

    """

    validate: bool = True
    qml: bool = False

    invalid_rows: List = field(init=False, default_factory=list)
    admin_route: AdminRoute = field(init=False)
    window_title: str = field(init=False)
    title: Union[str, ugettext_lazy] = field(init=False, default_factory=lambda: _('Data Preview'))
    subtitle: Union[str, ugettext_lazy] = field(init=False, default_factory=lambda: _('Please review the data below.'))
    icon: typing.Union[Icon, None] = field(init=False, default_factory=lambda: Icon('file-excel'))

    def __post_init__( self, value, admin, proxy, search_text):
        super().__post_init__(value, admin, proxy, search_text)
        self.admin_route = admin.get_admin_route()
        self.window_title = admin.get_verbose_name_plural()
        self.qml = True
        if self.validate:
            validator = admin.get_validator()
            for row, obj in enumerate(value):
                for _message in validator.validate_object(obj):
                    self.invalid_rows.append(row)
                    break

    @staticmethod
    def _add_actions(admin, actions):
        actions.extend(admin.get_related_toolbar_actions('onetomany'))

    def get_admin(self):
        """Use this method to get access to the admin in unit tests"""
        return initial_naming_context.resolve(self.admin_route)

@dataclass
class QmlChangeObjects(ChangeObjects):
    pass
