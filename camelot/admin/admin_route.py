from dataclasses import dataclass
import itertools
import logging
import typing

from ..admin.action.base import RenderHint
from ..core.exception import UserException
from ..core.naming import InitialNamingContext, NamingContext, NamingException
from ..core.utils import ugettext
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

naming_context = InitialNamingContext()

class AdminRoute(object):
    """
    Server side register of admins being used on the client side.
    """

    _admin_counter = itertools.count()
    _admin_routes = naming_context.bind_new_context(('admin',))

    @classmethod
    def admin_for(cls, route):
        """
        Retrieve an admin from its route

        :return: an 'Admin' object
        """
        assert isinstance(route, tuple)
        try:
            #admin = cls._admin_routes.resolve(route)
            admin = naming_context.resolve(route)
        except KeyError:
            cls._admin_routes.dump_names()
            raise UserException(
                ugettext('Admin no longer available'),
                resolution=ugettext('Restart the application'),
                detail='/'.join(route),
            )
        return admin

    @classmethod
    def _register_admin_route(cls, admin) -> Route:
        """
        Register a new admin

        :param admin: the admin class that is used to display this view

        :return: a route to a admin, that can be used to register actions.

        """
        next_admin = cls._admin_counter.__next__()
        # Try to resolve 
        try:
            cls._admin_routes.resolve((admin.get_name(),))
        except NamingException as exc:
            if exc.message == NamingException.Message.not_found:
                cls._admin_routes.bind_new_context((admin.get_name(),))
            else:
                raise exc
        # Context 
        admin_context = cls._admin_routes.bind_new_context((admin.get_name(), str(next_admin)))
        
        LOGGER.debug('Register admin route: {} -> {}'.format((*admin_context.get_name(), action.get_name()), admin))
        admin_route = admin_context.bind(admin_context, admin)
        # put name of the admin in the last part of the route, so it can
        # be used as a reference to store settings        
        #admin_route = ('admin', str(next_admin), admin.get_name())
        #LOGGER.debug('Register admin route: {} -> {}'.format(admin_route, admin))
        #cls._admin_routes.bind(admin_route, admin)
        return admin_route

    @classmethod
    def action_for(cls, route):
        """
        Retrieve an action from its route

        :return: an 'Action' object
        """
        assert isinstance(route, tuple)
        try:
            admin = naming_context.resolve(route)
            #admin = cls._admin_routes.resolve(route)
        except KeyError:
            cls._admin_routes.dump_names()
            raise UserException(
                ugettext('Action no longer available'),
                resolution=ugettext('Restart the application'),
                detail='/'.join(route),
            )
        return admin

    @staticmethod
    def _validate_action_name(action) -> bool:
        """
        Check to make sure that each action in an inheritance hierarchy has a different name.
        """
        names = set(action.name)
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
        assert admin_route in cls._admin_routes
        admin_context = cls._admin_routes.resolve(admin_route)
        try:
            actions_context = admin_context.resolve(('fields', field_name, 'actions'))
        except NamingException as exc:
            if exc.message == NamingException.Message.not_found:
                actions_context = admin_context.bind_new_context('fields').bind_new_context(field_name).bind_new_context('actions')
        assert action.get_name() not in actions_context, NamingContext.verbose_name((*actions_context.get_name(), action.get_name())) + ' registered before'
        LOGGER.debug('Registered field action route: {} -> {}'.format(action_route, action))
        action_route = actions_context.bind(action.get_name(), action)
        #action_route = (*admin_route, 'fields', field_name, 'actions', action.get_name())
        #assert action_route not in cls._admin_routes, NamingContext.verbose_name(action_route) + ' registered before'
        #LOGGER.debug('Register field action route: {} -> {}'.format(action_route, action))
        #cls._admin_routes.bind(action_route, action)
        return action_route

    @classmethod
    def _register_list_action_route(cls, admin_route, action) -> Route:
        assert cls._validate_action_name(action)
        assert isinstance(admin_route, tuple)
        assert admin_route in cls._admin_routes
        
        admin_context = cls._admin_routes.resolve(admin_route)
        try:
            actions_context = admin_context.resolve(('list', 'actions'))
        except NamingException as exc:
            if exc.message == NamingException.Message.not_found:
                actions_context = admin_context.bind_new_context('list').bind_new_context('actions')
        assert (action.get_name() not in actions_context) or (actions_context.resolve(action.get_name())==action), NamingContext.verbose_name(action_route) + ' registered before with a different action : ' + type(action).__name__
        LOGGER.debug('Registered field action route: {} -> {}'.format(action_route, action))        
        action_route = actions_context.rebind(action.get_name(), action)
        #action_route = (*admin_route, 'list', 'actions', action.get_name())
        #assert (action_route not in cls._admin_routes) or (cls._admin_routes.resolve(action_route)==action), NamingContext.verbose_name(action_route) + ' registered before with a different action : ' + type(action).__name__
        #LOGGER.debug('Register list action route: {} -> {}'.format(action_route, action))
        #cls._admin_routes.bind(action_route, action)
        return action_route

    @classmethod
    def _register_form_action_route(cls, admin_route, action) -> Route:
        assert cls._validate_action_name(action)
        assert isinstance(admin_route, tuple)
        assert admin_route in cls._admin_routes
        action_route = (*admin_route, 'form', 'actions', action.get_name())
        assert (action_route not in cls._admin_routes) or (cls._admin_routes.resolve(action_route)==action), NamingContext.verbose_name(action_route) + ' registered before with a different action : ' + type(action).__name__
        LOGGER.debug('Register list action route: {} -> {}'.format(action_route, action))
        cls._admin_routes.bind(action_route, action)
        return action_route

    @classmethod
    def _register_action_route(cls, admin_route, action) -> Route:
        assert cls._validate_action_name(action)
        assert isinstance(admin_route, tuple)
        assert admin_route in cls._admin_routes
        action_route = (*admin_route, 'actions', action.get_name())
        assert (action_route not in cls._admin_routes) or (cls._admin_routes.resolve(action_route)==action), NamingContext.verbose_name(action_route) + ' registered before with a different action : ' + type(action).__name__
        LOGGER.debug('Register action route: {} -> {}'.format(action_route, action))
        cls._admin_routes.bind(action_route, action)
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
