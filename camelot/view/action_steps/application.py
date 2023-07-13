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

import cProfile
from dataclasses import dataclass, field, InitVar
import json
import logging
import pstats
import typing

from ...admin.action.base import ActionStep, State, ModelContext
from ...admin.action.application_action import model_context_naming, model_context_counter
from ...admin.admin_route import AdminRoute, Route
from ...admin.application_admin import ApplicationAdmin
from ...admin.menu import MenuItem
from ...core.naming import initial_naming_context
from ...core.qt import QtCore, QtQuick, transferto
from ...core.serializable import DataclassSerializable
from ...model.authentication import AuthenticationMechanism
from .. import gui_naming_context
from camelot.view.qml_view import qml_action_step, get_qml_window, is_cpp_gui_context_name
from .open_file import OpenFile

LOGGER = logging.getLogger(__name__)

@dataclass
class Exit(ActionStep, DataclassSerializable):
    """
    Stop the event loop, and exit the application
    """

    return_code: int = 0
    blocking: bool = False

    @classmethod
    def gui_run(self, gui_context, serialized_step):
        from camelot.view.model_thread import get_model_thread
        model_thread = get_model_thread()
        if model_thread != None:
            model_thread.stop()
        qml_action_step(gui_context, 'Exit', serialized_step)


@dataclass
class SetThemeColors(ActionStep, DataclassSerializable):
    """
    This action step sets the theme colors.
    """

    primary_color: str
    accent_color: str
    blocking: bool = False


@dataclass
class Authenticate(ActionStep, DataclassSerializable):
    """
    Request client side credentials
    """

@dataclass
class MainWindow(ActionStep, DataclassSerializable):
    """
    This action step also takes care of other python stuff for now
    (e.g. stopping the model thread).
    """

    class MainWindowEventFilter(QtCore.QObject):

        def __init__(self, parent):
            super().__init__(parent)

        def eventFilter(self, qobject, event):
            if event.type() == QtCore.QEvent.Type.Close:
                from camelot.view.model_thread import get_model_thread
                model_thread = get_model_thread()
                LOGGER.info( 'closing mainwindow' )
                model_thread.stop()
                QtCore.QCoreApplication.exit(0)
            # allow events to propagate
            return False

    admin: InitVar[ApplicationAdmin]
    window_title: str = field(init=False)
    blocking: bool = False
    admin_route: Route = field(init=False)

    def __post_init__(self, admin):
        self.window_title = admin.get_name()
        self.admin_route = admin.get_admin_route()

    @classmethod
    def gui_run(cls, gui_context, serialized_step):
        LOGGER.info('installing event filter')
        qml_window = get_qml_window()
        event_filter = cls.MainWindowEventFilter(qml_window)
        # prevent garbage collection of the event_filter, by keeping it
        # out of the garbage collection cyle
        transferto(event_filter, event_filter)
        qml_window.installEventFilter(event_filter)
        qml_action_step(gui_context, 'MainWindow', serialized_step)


@dataclass
class NavigationPanel(ActionStep, DataclassSerializable):
    """
    Create a panel to navigate the application
    
    :param sections: a list of :class:`camelot.admin.section.Section'
        objects, with the sections of the navigation panel

    """

    # this could be non-blocking, but that causes unittest segmentation
    # fault issues which are not worth investigating
    menu: MenuItem
    model_context_name: Route = field(default_factory=list)
    action_states: typing.List[typing.Tuple[Route, State]] = field(default_factory=list)
    model_context: InitVar(ModelContext) = None
    blocking: bool = False

    # noinspection PyDataclass
    def __post_init__(self, model_context):
        self.menu = self._filter_items(self.menu, AuthenticationMechanism.get_current_authentication())
        self.model_context_name = model_context_naming.bind(str(next(model_context_counter)), model_context)
        self._add_action_states(model_context, self.menu.items, self.action_states)

    @classmethod
    def _filter_items(cls, menu: MenuItem, auth) -> MenuItem:
        """
        Create a new menu item with only child items with a role hold by
        the authentication
        """
        new_menu = MenuItem(
            verbose_name=menu.verbose_name,
            icon=menu.icon,
            role=menu.role,
            action_route=menu.action_route,
        )
        new_menu.items.extend(
            cls._filter_items(item, auth) for item in menu.items if (
                    (item.role is None) or auth.has_role(item.role)
            )
        )
        return new_menu

    @classmethod
    def _add_action_states(self, model_context, items, action_states):
        """
        Recurse through a menu and get the state for all actions in the menu
        """
        for item in items:
            self._add_action_states(model_context, item.items, action_states)
            action_route = item.action_route
            if action_route is not None:
                action = initial_naming_context.resolve(action_route)
                state = action.get_state(model_context)
                action_states.append((action_route, state))


@dataclass
class MainMenu(ActionStep, DataclassSerializable):
    """
    Create a main menu for the application window.
    
    :param menu: a list of :class:`camelot.admin.menu.Menu' objects

    """

    blocking = False
    menu: MenuItem
    model_context_name: Route = field(default_factory=list)
    action_states: typing.List[typing.Tuple[Route, State]] = field(default_factory=list)
    model_context: InitVar(ModelContext) = None

    def __post_init__(self, model_context):
        self.model_context_name = model_context_naming.bind(str(next(model_context_counter)), model_context)
        self._add_action_states(model_context, self.menu.items, self.action_states)

    @classmethod
    def _add_action_states(self, model_context, items, action_states):
        """
        Recurse through a menu and get the state for all actions in the menu
        """
        for item in items:
            self._add_action_states(model_context, item.items, action_states)
            action_route = item.action_route
            if action_route is not None:
                action = initial_naming_context.resolve(action_route)
                state = action.get_state(model_context)
                action_states.append((action_route, state))


@dataclass
class InstallTranslator(ActionStep, DataclassSerializable):
    """
    Install a translator in the application.  Ownership of the translator will
    be moved to the application.

    :param language: The two-letter, ISO 639 language code (e.g. 'nl').
    """

    blocking = False
    language: str


@dataclass
class RemoveTranslators(ActionStep, DataclassSerializable):
    """
    Unregister all previously installed translators from the application.

    :param admin: a :class:`camelot.admin.application_admin.ApplicationAdmin'
        object
    """

    admin: InitVar[ApplicationAdmin]
    admin_route: AdminRoute = field(init=False)

    def __post_init__(self, admin):
        self.admin_route = admin.get_admin_route()

@dataclass
class UpdateActionsState(ActionStep, DataclassSerializable):
    """
    Update the the state of a list of `Actions`

    :param action_states: a `dict` mapping the action_routes to their
        updated state.

    """

    model_context: InitVar[ModelContext]
    actions_state: InitVar[dict]

    action_states: typing.List[typing.Tuple[Route, State]] = field(init=False)

    # noinspection PyDataclass
    def __post_init__(self, model_context, actions_state):
        self.action_states = []
        if actions_state is not None:
            for action, state in actions_state.items():
                action_route = AdminRoute._register_list_action_route(model_context.admin.get_admin_route(), action)
                self.action_states.append((action_route, state._to_dict()))

    @classmethod
    def gui_run(cls, gui_context_name, serialized_step):
        if is_cpp_gui_context_name(gui_context_name):
            return qml_action_step(gui_context_name, 'UpdateActionsState', serialized_step)
        gui_context = gui_naming_context.resolve(gui_context_name)
        step = json.loads(serialized_step)
        for action_route, action_state in step['action_states']:
            action = initial_naming_context.resolve(tuple(action_route))
            rendered_action_route = gui_context.action_routes.get(action)
            if rendered_action_route is None:
                LOGGER.warn('Cannot update rendered action, rendered_action_route is unknown')
                continue
            qobject = gui_context.view.findChild(QtCore.QObject, rendered_action_route)
            if qobject is None:
                LOGGER.warn('Cannot update rendered action, QObject child {} not found'.format(rendered_action_route))
                continue
            if isinstance(qobject, QtQuick.QQuickItem):
                qobject.setProperty('state', action_state._to_dict())
            else:
                qobject.set_state(action_state)

@dataclass
class StartProfiler(ActionStep, DataclassSerializable):
    """Start profiling of the gui
    """

    @classmethod
    def gui_run(cls, gui_context, serialized_step):
        gui_profile = cProfile.Profile()
        gui_naming_context.bind(('gui_profile',), gui_profile)
        gui_profile.enable()
        LOGGER.info('Gui profiling started')

@dataclass
class StopProfiler(ActionStep, DataclassSerializable):
    """Start profiling of the gui
    """

    @classmethod
    def gui_run(cls, gui_context, serialized_step):
        gui_profile = gui_naming_context.resolve(('gui_profile',))
        gui_profile.disable()
        cls.write_profile(gui_profile, 'gui')

    @classmethod
    def write_profile(cls, profile, suffix):
        stats = pstats.Stats(profile)
        stats.sort_stats('cumulative')
        LOGGER.info('Begin {} profile info'.format(suffix))
        stats.print_stats()
        LOGGER.info('End {} profile info'.format(suffix))
        filename = OpenFile.create_temporary_file('-{0}.prof'.format(suffix))
        stats.dump_stats(filename)