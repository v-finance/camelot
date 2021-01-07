import collections
import itertools
import logging

from ..core.exception import UserException
from ..core.utils import ugettext

LOGGER = logging.getLogger(__name__)


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
    def _register_admin_route(cls, admin):
        """
        Register a new admin

        :param admin: the admin class that is used to display this view

        :return: a route to a admin, that can be used to register actions.

        """
        next_admin = cls._admin_counter.__next__()
        admin_route = ('admin', admin.get_name(), str(next_admin))
        cls._admin_routes[admin_route] = admin
        return admin_route
