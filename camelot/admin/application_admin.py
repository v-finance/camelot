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
import sys

logger = logging.getLogger('camelot.admin.application_admin')



from .action.base import Action
from .action.application_action import OpenTableView
from .admin_route import AdminRoute, register_list_actions, register_form_actions
from .entity_admin import EntityAdmin
from .menu import MenuItem
from .object_admin import ObjectAdmin
from ..core.orm import Entity
from ..core.qt import QtCore
from camelot.admin.action import application_action, form_action, list_action

#
# The translations data needs to be kept alive during the
# running of the application
#
_translations_data_ = []

class ApplicationAdmin(AdminRoute):
    """The ApplicationAdmin class defines how the application should look
like, it also ties Python classes to their associated 
:class:`camelot.admin.object_admin.ObjectAdmin` class or subclass.  It's
behaviour can be steered by overwriting its static attributes or it's
methods :

.. attribute:: name

    The name of the application, as it will appear in the title of the main
    window.

.. attribute:: application_url

    The url of the web site where the user can find more information on
    the application.

.. attribute:: help_url

    Points to either a local html file or a web site that contains the
    documentation of the application.

.. attribute:: author

    The name of the author of the application

.. attribute:: domain

    The domain name of the author of the application, eg 'mydomain.com', this
    domain will be used to store settings of the application.

.. attribute:: version

    A string with the version of the application

When the same action is returned in the :meth:`get_toolbar_actions` and 
:meth:`get_main_menu` method, it should be exactly the same object, to avoid
shortcut confusion and reduce the number of status updates.
    """

    application_url = None
    help_url = 'http://www.python-camelot.com/docs.html'
    author = 'Conceptive Engineering'

    version = '1.0'

    #
    # actions that will be shared between the toolbar and the main menu
    #
    list_toolbar_actions = [
        list_action.close_list,
        list_action.list_label,
    ]
    change_row_actions = [ list_action.to_first_row,
                           list_action.to_last_row ]
    edit_actions = [ list_action.add_new_object,
                     list_action.delete_selection,
                     list_action.duplicate_selection ]
    help_actions = []
    export_actions = [ list_action.export_spreadsheet ]
    form_toolbar_actions = [ form_action.close_form,
                             form_action.to_first_form,
                             form_action.to_previous_form,
                             form_action.to_next_form,
                             form_action.to_last_form,
                             application_action.refresh,
                             form_action.show_history ]
    onetomany_actions = [
        list_action.delete_selection,
        list_action.duplicate_selection,
        list_action.export_spreadsheet
    ]
    manytomany_actions = [
        list_action.remove_selection,
        list_action.export_spreadsheet
    ]

    def __init__(self, name=None, author=None, domain=None):
        #
        # Cache created ObjectAdmin objects
        #
        self._object_admin_cache = {}
        self._memento = None
        self.admins = {
            object: ObjectAdmin,
            Entity: EntityAdmin,
        }
        if name is not None:
            self.name = name
        if author is not None:
            self.author = author
        if domain is not None:
            self.domain = domain
        self._admin_route = super()._register_admin_route(self)
        self._main_menu = MenuItem()
        self._navigation_menu = MenuItem()

    def get_admin_route(self):
        return self._admin_route

    def register(self, entity, admin_class):
        """Associate a certain ObjectAdmin class with another class.  This
        ObjectAdmin will be used as default to render object the specified
        type.

        :param entity: :class:`class`
        :param admin_class: a subclass of 
            :class:`camelot.admin.object_admin.ObjectAdmin` or
            :class:`camelot.admin.entity_admin.EntityAdmin`
        """
        self.admins[entity] = admin_class

    def get_navigation_menu(self):
        """
        :return: a :class:`camelot.admin.menu.MenuItem` object
        """
        return self._navigation_menu

    def get_memento( self ):
        """Returns an instance of :class:`camelot.core.memento.SqlMemento` that
        can be used to store changes made to objects.  Overwrite this method to
        make it return `None` if no changes should be stored to the database, or
        to return another instance if the changes should be stored elsewhere.

        :return: `None` or an :class:`camelot.core.memento.SqlMemento` instance
        """
        from camelot.core.memento import SqlMemento
        if self._memento == None:
            self._memento = SqlMemento()
        return self._memento

    def get_application_admin( self ):
        """Get the :class:`ApplicationAdmin` class of this application, this
        method is here for compatibility with the :class:`ObjectAdmin`

        :return: this object itself
        """
        return self

    def get_related_admin(self, cls):
        """Get the default :class:`camelot.admin.object_admin.ObjectAdmin` class
        for a specific class, return None, if not known.  The ObjectAdmin
        should either be registered through the :meth:`register` method or be
        defined as an inner class with name :keyword:`Admin` of the entity.

        :param entity: a :class:`class`

        """
        return self.get_entity_admin( cls )

    def get_entity_admin(self, entity):
        """Get the default :class:`camelot.admin.object_admin.ObjectAdmin` class
        for a specific entity, return None, if not known.  The ObjectAdmin
        should either be registered through the :meth:`register` method or be
        defined as an inner class with name :keyword:`Admin` of the entity.

        :param entity: a :class:`class`

        deprecated : use get_related_admin instead
        """
        try:
            return self._object_admin_cache[entity]
        except KeyError:
            for cls in entity.__mro__:
                admin_class = self.admins.get(cls, None)
                if admin_class is None:
                    if hasattr(cls, 'Admin'):
                        admin_class = cls.Admin
                        break
                else:
                    break
            else:
                raise Exception('Could not construct a default admin class')
            admin = admin_class(self, entity)
            self._object_admin_cache[entity] = admin
            return admin

    def get_actions(self):
        """
        :return: a list of :class:`camelot.admin.action.base.Action` objects
            that should be displayed on the desktop of the user.
        """
        return []

    @register_list_actions('_admin_route')
    def get_related_toolbar_actions( self, direction ):
        """Specify the toolbar actions that should appear by default on every
        OneToMany editor in the application.

        :param direction: the direction of the relation : 'onetomany' or 
            'manytomany'
        :return: a list of :class:`camelot.admin.action.base.Action` objects
        """
        if direction == 'onetomany':
            return self.onetomany_actions
        if direction == 'manytomany':
            return self.manytomany_actions

    def get_form_actions( self ):
        """Specify the action buttons that should appear on each form in the
        application.  
        The :meth:`camelot.admin.object_admin.ObjectAdmin.get_form_actions`
        method will call this method and prepend the result to the actions
        of that specific form.

        :return: a list of :class:`camelot.admin.action.base.Action` objects
        """
        return []

    @register_form_actions('_admin_route', '_form_toolbar_actions')
    def get_form_toolbar_actions( self ):
        """
        :return: a list of :class:`camelot.admin.action.base.Action` objects
            that should be displayed on the toolbar of a form view.  return
            None if no toolbar should be created.
        """
        if sys.platform.startswith('darwin'):
            #
            # NOTE We remove the CloseForm from the toolbar action list
            #      on Mac because this regularly causes segfaults.
            #      The user can still close the form with the
            #      OS close button (i.e. "X").
            #
            return [action for action in self.form_toolbar_actions
                    if type(action) != form_action.CloseForm]
        return self.form_toolbar_actions

    @register_list_actions('_admin_route', '_toolbar_actions')
    def get_list_toolbar_actions( self ):
        """
        :return: a list of :class:`camelot.admin.action.base.Action` objects
            that should be displayed on the toolbar of the application.  return
            None if no toolbar should be created.
        """
        return self.list_toolbar_actions + \
               self.edit_actions + \
               self.change_row_actions + \
               self.export_actions

    @register_list_actions('_admin_route', '_select_toolbar_actions')
    def get_select_list_toolbar_actions( self ):
        """
        :return: a list of :class:`camelot.admin.action.base.Action` objects
            that should be displayed on the toolbar of the application.  return
            None if no toolbar should be created.
        """
        return self.list_toolbar_actions + self.change_row_actions

    def add_main_menu(self, verbose_name, icon=None, role=None, parent_menu=None):
        """
        add a new item to the main menu

        :return: a `MenuItem` object that can be used in subsequent calls to
            add other items as children of this item.
        """
        menu = MenuItem(verbose_name, icon, role=role)
        if parent_menu is None:
            parent_menu = self._main_menu
        parent_menu.items.append(menu)
        return menu

    def add_navigation_menu(self, verbose_name, icon=None, role=None, parent_menu=None):
        """
        add a new item to the navigation menu

        :return: a `MenuItem` object that can be used in subsequent calls to
            add other items as children of this item.
        """
        menu = MenuItem(verbose_name, icon, role=role)
        if parent_menu is None:
            parent_menu = self._navigation_menu
        parent_menu.items.append(menu)
        return menu

    def add_navigation_entity_table(self, entity, parent_menu, role=None, add_before=None):
        """
        Add an action to open a table view of an entity to the navigation menu
        """
        admin = self.get_related_admin(entity)
        return self.add_navigation_admin_table(admin, parent_menu, role=role, add_before=add_before)

    def add_navigation_admin_table(self, admin, parent_menu, role=None, add_before=None):
        """
        Add an action to open a table view for a specified admin
        """
        assert isinstance(add_before, (type(None), MenuItem,))
        assert isinstance(role, (type(None), str))
        action = OpenTableView(admin)
        action_route = self._register_action_route(admin._admin_route, action)
        menu = MenuItem(action_route=action_route, role=role)
        if add_before is None:
            parent_menu.items.append(menu)
        else:
            parent_menu.items.insert(parent_menu.items.index(add_before), menu)
        return menu

    def add_navigation_action(self, action, parent_menu, role=None, add_before=None):
        action_route = self._register_action_route(self._admin_route, action)
        menu = MenuItem(action_route=action_route, role=role)
        if add_before is None:
            parent_menu.items.append(menu)
        else:
            parent_menu.items.insert(parent_menu.items.index(add_before), menu)
        return menu

    def add_main_action(self, action, parent_menu=None):
        assert isinstance(action, Action)
        action_route = self._register_action_route(self._admin_route, action)
        if parent_menu is None:
            parent_menu = self._main_menu
        else:
            assert isinstance(parent_menu, MenuItem)
        parent_menu.items.append(MenuItem(action_route=action_route))

    def add_main_separator(self, parent_menu):
        assert isinstance(parent_menu, MenuItem)
        parent_menu.items.append(MenuItem())

    def get_main_menu(self) -> MenuItem:
        """
        :return: a :class:`camelot.admin.menu.MenuItem` object
        """
        return self._main_menu

    def get_name(self):
        return 'application'

    def get_version(self):
        """:return: string representing version of the application, by default this
                    is the class attribute verion"""
        return self.version

    def get_help_url(self):
        """:return: a :class:`QtCore.QUrl` pointing to the index page for help"""
        if self.help_url:
            return QtCore.QUrl( self.help_url )
