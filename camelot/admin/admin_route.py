from dataclasses import dataclass
import itertools
import logging
import typing

from ..admin.action.base import RenderHint
from ..core.naming import AlreadyBoundException, initial_naming_context, NamingContext, NameNotFoundException
from ..core.serializable import DataclassSerializable

LOGGER = logging.getLogger(__name__)

Route = typing.Tuple[str, ...]


@dataclass
class RouteWithRenderHint(DataclassSerializable):
    """
    A :class:`camelot.admin.admin_route.Route` with associated :class:`camelot.admin.action.base.RenderHint`.
    """

    route: Route
    render_hint: RenderHint

    @staticmethod
    def from_dict(data):
        return RouteWithRenderHint(tuple(data['route']), RenderHint(data['render_hint']))


class AdminRoute(object):
    """
    Server side register of admins being used on the client side.
    """

    _admin_counter = itertools.count()
    _admin_routes = initial_naming_context.bind_new_context('admin')

    @classmethod
    def _register_admin_route(cls, admin) -> Route:
        """
        Register a new admin

        :param admin: the admin class that is used to display this view

        :return: a route to a admin, that can be used to register actions.

        """
        next_admin = cls._admin_counter.__next__()
        try:
            cls._admin_routes.resolve_context(admin.get_name())
        except NameNotFoundException:
            cls._admin_routes.bind_new_context(admin.get_name())
        admin_context = cls._admin_routes.bind_new_context((admin.get_name(), str(next_admin)))
        admin_route = cls._admin_routes.bind((admin.get_name(), str(next_admin)), admin)
        LOGGER.debug('Registered admin route: {} -> {}'.format(admin_route, admin))
        # Create and bind subcontexts for the different type of admin's actions:
        admin_context.bind_new_context('actions')
        admin_context.bind_new_context('field')
        admin_context.bind_new_context('form').bind_new_context('actions')
        admin_context.bind_new_context('list').bind_new_context('actions')
        return admin_route

    @staticmethod
    def _validate_action_name(action) -> bool:
        """
        Check to make sure that each action in an inheritance hierarchy has a different name.
        """
        names = set()
        success = True
        for cls in action.__class__.mro():
            if not hasattr(cls, 'name'):
                continue
            if cls.name in names:
                success = False
                break
            names.add(cls.name)
        if not success:
            LOGGER.error('Action name validation failed, each action in an inheritance hierarchy should have a different name:')
            for cls in action.__class__.mro():
                if not hasattr(cls, 'name'):
                    continue
                LOGGER.error('{} has name: {}'.format(cls, cls.name))
            return False
        return True


    @classmethod
    def _register_field_action_route(cls, admin_route, field_name, action) -> Route:
        assert cls._validate_action_name(action)
        assert isinstance(admin_route, tuple)
        assert isinstance(field_name, str)
        assert admin_route in initial_naming_context
        field_context = initial_naming_context.resolve_context((*admin_route, 'field'))
        try:
            context = field_context.resolve_context((field_name, 'actions'))
        except NameNotFoundException:
            context = field_context.bind_new_context(field_name).bind_new_context('actions')
        try:
            action_route = context.bind(action.get_name(), action)
        except AlreadyBoundException:
            action_route = context.get_qual_name(action.get_name())
            assert action == context.resolve(action.get_name()), NamingContext.verbose_name(action_route) + ' registered before with a different action : ' + type(action).__name__
        LOGGER.debug('Registered field action route: {} -> {}'.format(action_route, action))
        return action_route

    @classmethod
    def _register_list_action_route(cls, admin_route, action) -> Route:
        assert cls._validate_action_name(action)
        assert isinstance(admin_route, tuple)
        assert admin_route in initial_naming_context
        context = initial_naming_context.resolve_context((*admin_route, 'list', 'actions'))
        try:
            action_route = context.bind(action.get_name(), action)
        except AlreadyBoundException:
            action_route = context.get_qual_name(action.get_name())
            assert action == context.resolve(action.get_name()), NamingContext.verbose_name(action_route) + ' registered before with a different action : ' + type(action).__name__
        LOGGER.debug('Registered list action route: {} -> {}'.format(action_route, action))
        return action_route

    @classmethod
    def _register_form_action_route(cls, admin_route, action) -> Route:
        assert cls._validate_action_name(action)
        assert isinstance(admin_route, tuple)
        assert admin_route in initial_naming_context
        context = initial_naming_context.resolve_context((*admin_route, 'form', 'actions'))
        try:
            action_route = context.bind(action.get_name(), action)
        except AlreadyBoundException:
            action_route = context.get_qual_name(action.get_name())
            assert action == context.resolve(action.get_name()), NamingContext.verbose_name(action_route) + ' registered before with a different action : ' + type(action).__name__
        LOGGER.debug('Registered form action route: {} -> {}'.format(action_route, action))
        return action_route

    @classmethod
    def _register_action_route(cls, admin_route, action) -> Route:
        assert cls._validate_action_name(action)
        assert isinstance(admin_route, tuple)
        assert admin_route in initial_naming_context
        context = initial_naming_context.resolve_context((*admin_route, 'actions'))
        try:
            action_route = context.bind(action.get_name(), action)
        except AlreadyBoundException:
            action_route = context.get_qual_name(action.get_name())
            assert action == context.resolve(action.get_name()), NamingContext.verbose_name(action_route) + ' registered before with a different action : ' + type(action).__name__
        LOGGER.debug('Registered action route: {} -> {}'.format(action_route, action))
        return action_route

def _register_actions_decorator(register_func, attr_admin_route, attr_cache):
    def decorator(func):
        def wrapper(self, *args, **kwargs):
            # check for existing cahed attribute
            if attr_cache is not None:
                if hasattr(self, attr_cache) and getattr(self, attr_cache) is not None:
                    return getattr(self, attr_cache)
            # register actions
            assert hasattr(self, attr_admin_route)
            admin_route = getattr(self, attr_admin_route)
            assert isinstance(admin_route, tuple)
            actions = func(self, *args, **kwargs)
            result = []
            for action in actions:
                if isinstance(action, RouteWithRenderHint):
                    result.append(action) # action is already registered
                else:
                    result.append(RouteWithRenderHint(register_func(admin_route, action), action.render_hint))
            if attr_cache is not None:
                setattr(self, attr_cache, result)
            return result
        return wrapper
    return decorator


def register_list_actions(attr_admin_route, attr_cache=None):
    """
    Function decorator that registers list actions.

    :param str attr_admin_route: Name of the attribute that contains the AdminRoute.
    :param str attr_cache: Name of the attribute to cache the registered actions.
                           If this is None, no caching will be done.
    """
    return _register_actions_decorator(AdminRoute._register_list_action_route, attr_admin_route, attr_cache)

def register_form_actions(attr_admin_route, attr_cache=None):
    """
    Function decorator that registers form actions.

    :param str attr_admin_route: Name of the attribute that contains the AdminRoute.
    :param str attr_cache: Name of the attribute to cache the registered actions.
                           If this is None, no caching will be done.
    """
    return _register_actions_decorator(AdminRoute._register_form_action_route, attr_admin_route, attr_cache)
