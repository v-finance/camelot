import collections
import itertools
import logging
import typing

from ..core.exception import UserException
from ..core.utils import ugettext

LOGGER = logging.getLogger(__name__)

Route = typing.Tuple[str, ...]

class AdminRoute(object):
    """
    Server side register of admins being used on the client side.
    """

    _admin_counter = itertools.count()
    _admin_routes = collections.defaultdict(dict)

    @classmethod
    def verbose_route(cls, route):
        return '/'.join(route)

    @classmethod
    def dump_routes(cls):
        for route in cls._admin_routes.keys():
            LOGGER.info(cls.verbose_route(route))

    @classmethod
    def admin_for(cls, route):
        """
        Retrieve an admin from its route

        :return: an 'Admin' object
        """
        assert isinstance(route, tuple)
        try:
            admin = cls._admin_routes[route]
        except KeyError:
            cls.dump_routes()
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
        # put name of the admin in the last part of the route, so it can
        # be used as a reference to store settings
        admin_route = ('admin', str(next_admin), admin.get_name())
        cls._admin_routes[admin_route] = admin
        return admin_route

    @classmethod
    def action_for(cls, route):
        """
        Retrieve an action from its route

        :return: an 'Action' object
        """
        assert isinstance(route, tuple)
        try:
            admin = cls._admin_routes[route]
        except KeyError:
            cls.dump_routes()
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
        action_route = (*admin_route, 'fields', field_name, 'actions', action.get_name())
        assert action_route not in cls._admin_routes, cls.verbose_route(action_route) + ' registered before'
        cls._admin_routes[action_route] = action
        return action_route

    @classmethod
    def _register_list_action_route(cls, admin_route, action) -> Route:
        assert cls._validate_action_name(action)
        assert isinstance(admin_route, tuple)
        assert admin_route in cls._admin_routes
        action_route = (*admin_route, 'list', 'actions', action.get_name())
        assert (action_route not in cls._admin_routes) or (cls._admin_routes[action_route]==action), cls.verbose_route(action_route) + ' registered before with a different action : ' + type(action).__name__
        cls._admin_routes[action_route] = action
        return action_route

    @classmethod
    def _register_action_route(cls, admin_route, action) -> Route:
        assert cls._validate_action_name(action)
        assert isinstance(admin_route, tuple)
        assert admin_route in cls._admin_routes
        action_route = (*admin_route, 'actions', action.get_name())
        assert (action_route not in cls._admin_routes) or (cls._admin_routes[action_route]==action), cls.verbose_route(action_route) + ' registered before with a different action : ' + type(action).__name__
        cls._admin_routes[action_route] = action
        return action_route


def register_list_actions(attr_cache, attr_admin_route):
    """
    Function decorator that registers list actions.

    :param str attr_cache: Name of the attribute to cache the registered actions
    :param str attr_admin_route: Name of the attribute that contains the AdminRoute.
    """
    def decorator(func):
        def wrapper(self, *args, **kwargs):
            # check for existing attribute
            if hasattr(self, attr_cache) and getattr(self, attr_cache) is not None:
                return getattr(self, attr_cache)
            # register actions
            assert hasattr(self, attr_admin_route)
            admin_route = getattr(self, attr_admin_route)
            actions = func(self, *args, **kwargs)
            result = []
            for action in actions:
                if isinstance(action, tuple):
                    result.append(action) # action is already registered
                else:
                    result.append((AdminRoute._register_list_action_route(admin_route, action), action.render_hint))
            setattr(self, attr_cache, result)
            return result
        return wrapper
    return decorator
