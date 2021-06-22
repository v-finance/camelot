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

    @classmethod
    def _register_field_action_route(cls, admin_route, field_name, action) -> Route:
        assert isinstance(admin_route, tuple)
        assert isinstance(field_name, str)
        assert admin_route in cls._admin_routes
        action_route = (*admin_route, 'fields', field_name, 'actions', action.get_name())
        assert action_route not in cls._admin_routes, cls.verbose_route(action_route) + ' registered before'
        cls._admin_routes[action_route] = action
        return action_route

    @classmethod
    def _register_list_action_route(cls, admin_route, action) -> Route:
        assert isinstance(admin_route, tuple)
        assert admin_route in cls._admin_routes
        action_route = (*admin_route, 'list', 'actions', action.get_name())
        assert (action_route not in cls._admin_routes) or (cls._admin_routes[action_route]==action), cls.verbose_route(action_route) + ' registered before with a different action : ' + type(action).__name__
        cls._admin_routes[action_route] = action
        return action_route

    @classmethod
    def _register_action_route(cls, admin_route, action) -> Route:
        assert isinstance(admin_route, tuple)
        assert admin_route in cls._admin_routes
        action_route = (*admin_route, 'actions', action.get_name())
        assert (action_route not in cls._admin_routes) or (cls._admin_routes[action_route]==action), cls.verbose_route(action_route) + ' registered before with a different action : ' + type(action).__name__
        cls._admin_routes[action_route] = action
        return action_route