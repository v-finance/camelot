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

from dataclasses import dataclass, field, InitVar
import json
import logging
import typing

from ..controls.action_widget import ActionAction
from ...admin.action.base import ActionStep, State, ModelContext
from ...admin.admin_route import AdminRoute, Route
from ...admin.application_admin import ApplicationAdmin
from ...admin.menu import MenuItem
from ...core.qt import QtCore, Qt, QtWidgets
from ...core.serializable import DataclassSerializable
from ...model.authentication import get_current_authentication

LOGGER = logging.getLogger(__name__)

@dataclass
class Exit(ActionStep, DataclassSerializable):
    """
    Stop the event loop, and exit the application
    """

    return_code: int = 0

    @classmethod
    def gui_run(self, gui_context, serialized_step):
        from camelot.view.model_thread import get_model_thread
        model_thread = get_model_thread()
        # we might exit the application when the workspace is not even there
        if gui_context.workspace != None:
            gui_context.workspace.close_all_views()
        if model_thread != None:
            model_thread.stop()
        QtCore.QCoreApplication.exit(self.return_code)

@dataclass
class MainWindow(ActionStep):
    """
    Open a top level application window
    
    :param admin: a :class:`camelot.admin.application_admin.ApplicationAdmin'
        object

    .. attribute:: window_title

        The title of the main window, defaults to the application name if `None`
        is given

    """

    admin: ApplicationAdmin
    window_title: str = field(init=False)

    def __post_init__(self):
        self.window_title = self.admin.get_name()

    def render(self, gui_context):
        """create the main window. this method is used to unit test
        the action step."""
        from ..mainwindowproxy import MainWindowProxy

        main_window_context = gui_context.copy()
        main_window_context.progress_dialog = None
        main_window_context.admin = self.admin

        # Check if a QMainWindow already exists
        window = None
        app = QtWidgets.QApplication.instance()
        for widget in app.allWidgets():
            if isinstance(widget, QtWidgets.QMainWindow):
                # Make sure a QMainWindow is reused only once
                if not hasattr(widget, '_reused_by_view_action_steps_application'):
                    widget._reused_by_view_action_steps_application = True
                    window = widget
                    break

        main_window_proxy = MainWindowProxy(
            gui_context=main_window_context, window=window
        )

        gui_context.workspace = main_window_context.workspace
        main_window_proxy.parent().setWindowTitle(self.window_title)
        return main_window_proxy.parent()

    def gui_run(self, gui_context):
        main_window = self.render(gui_context)
        if main_window.statusBar() is not None:
            main_window.statusBar().hide()
        main_window.show()


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
    action_states: typing.List[typing.Tuple[Route, State]] = field(default_factory=list)
    model_context: InitVar(ModelContext) = None

    # noinspection PyDataclass
    def __post_init__(self, model_context):
        self.menu = self._filter_items(self.menu, get_current_authentication())
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
                action = AdminRoute.action_for(action_route)
                state = action.get_state(model_context)
                action_states.append((action_route, state))

    @classmethod
    def render(self, gui_context, step):
        """create the navigation panel.
        this method is used to unit test the action step."""
        from ..controls.section_widget import NavigationPane
        navigation_panel = NavigationPane(
            gui_context,
            gui_context.workspace
        )
        navigation_panel.set_sections(
            step["menu"]["items"], step["action_states"]
        )
        return navigation_panel

    @classmethod
    def gui_run(self, gui_context, serialized_step):
        step = json.loads(serialized_step)
        navigation_panel = self.render(gui_context, step)
        gui_context.workspace.parent().addDockWidget(
            Qt.LeftDockWidgetArea, navigation_panel
        )


@dataclass
class MainMenu(ActionStep, DataclassSerializable):
    """
    Create a main menu for the application window.
    
    :param menu: a list of :class:`camelot.admin.menu.Menu' objects

    """

    blocking = False
    menu: MenuItem

    @classmethod
    def render(cls, gui_context, items, parent_menu):
        """
        :return: a :class:`QtWidgets.QMenu` object
        """
        for item in items:
            if (item["verbose_name"] is None) and (item["action_route"] is None):
                parent_menu.addSeparator()
                continue
            elif item["verbose_name"] is not None:
                menu = QtWidgets.QMenu(item["verbose_name"], parent_menu)
                parent_menu.addMenu(menu)
                cls.render(gui_context, item["items"], menu)
            elif item["action_route"] is not None:
                action = AdminRoute.action_for(tuple(item["action_route"]))
                qaction = ActionAction(action, gui_context, parent_menu)
                parent_menu.addAction(qaction)
            else:
                raise Exception('Cannot handle menu item {}'.format(item))

    @classmethod
    def gui_run(self, gui_context, serialized_step):
        from ..controls.busy_widget import BusyWidget
        if gui_context.workspace is None:
            return
        main_window = gui_context.workspace.parent()
        if main_window is None:
            return
        step = json.loads(serialized_step)
        menu_bar = main_window.menuBar()
        self.render(gui_context, step["menu"]["items"], menu_bar)
        menu_bar.setCornerWidget(BusyWidget())


class InstallTranslator(ActionStep):
    """
    Install a translator in the application.  Ownership of the translator will
    be moved to the application.

    :param admin: a :class:`camelot.admin.application_admin.ApplicationAdmin'
        object

    """

    def __init__(self, admin):
        self.admin = admin

    def gui_run(self, gui_context):
        app = QtCore.QCoreApplication.instance()
        translator = self.admin.get_translator()
        if isinstance(translator, list):
            for t in translator:
                t.setParent(app)
                app.installTranslator(t)
        else:
            app.installTranslator(translator)


class RemoveTranslators(ActionStep):
    """
    Unregister all previously installed translators from the application.

    :param admin: a :class:`camelot.admin.application_admin.ApplicationAdmin'
        object
    """

    def __init__(self, admin):
        self.admin = admin

    def gui_run(self, gui_context):
        app = QtCore.QCoreApplication.instance()
        for active_translator in app.findChildren(QtCore.QTranslator):
            app.removeTranslator(active_translator)


class UpdateActionsState(ActionStep):
    """
    Update the the state of a list of `Actions`

    :param action_states: a `dict` mapping the action_routes to their
        updated state.

    """

    def __init__(self, actions_state):
        self.actions_state = actions_state

    def gui_run(self, gui_context):
        for action_route, action_state in self.actions_state.items():
            rendered_action_route = gui_context.action_routes.get(action_route)
            if rendered_action_route is None:
                LOGGER.warn('Cannot update rendered action, rendered_action_route is unknown')
                continue
            qobject = gui_context.view.findChild(QtCore.QObject, rendered_action_route)
            if qobject is None:
                LOGGER.warn('Cannot update rendered action, QObject child {} not found'.format(rendered_action_route))
                continue
            qobject.set_state(action_state)
