import collections
import itertools
import logging

from ..core.exception import UserException
from ..core.utils import ugettext

LOGGER = logging.getLogger(__name__)


class ViewRegister(object):
    """
    Server side register of views being displayed on the client side,
    to enable caching of the resources needed to update a view.
    """

    _view_counter = itertools.count()
    _view_routes = collections.defaultdict(dict)
    _max_views = 10

    @classmethod
    def dump_routes(cls):
        for key, routes in cls._view_routes.items():
            LOGGER.info(key)
            for route in routes.keys():
                LOGGER.info(key + route)

    @classmethod
    def action_for(self, route):
        """
        Retrieve an action from its route

        :return: an 'Action' object
        """
        assert isinstance(route, tuple)

    @classmethod
    def register_view_route(cls, admin):
        """
        Register a new view

        :param admin: the admin class that is used to display this view

        :return: a route to a view, that can be used to register actions.

        Raises an exception if the maximum number of views has been reached.
        """
        if len(cls._view_routes) >= cls._max_views:
            raise UserException(
                ugettext('Maximum number of open views reached'),
                resolution=ugettext('Restart the application or close views')
            )
        next_view = cls._view_counter.__next__()
        view_route = ('view', str(next_view))
        cls._view_routes[view_route][('admin',)] = admin
        cls.dump_routes()
        return view_route

    @classmethod
    def unregister_view(cls, view_route):
        """
        Unregister an existing view, and release all its actions
        """
        assert isinstance(view_route, tuple)
        cls._view_routes.pop(view_route)

    @classmethod
    def register_action_route(cls, view_route):
        """
        Register the action as available for a view, returns a `route` to
        this action that can be used later on to retrieve the action.
        """
        assert isinstance(view_route, tuple)