from camelot.admin.admin_route import Route

class ProxyRegistry:
    """Registry to hold proxy objects"""

    _register = {}
    _last_id = 0

    @classmethod
    def register(cls, proxy) -> Route:
        """Register a proxy

        :return: The route with the id associated with the registered proxy.
        """
        next_id = cls._last_id + 1
        cls._register[next_id] = proxy
        cls._last_id = next_id
        return [str(next_id)]

    @staticmethod
    def is_valid_route(route: Route) -> bool:
        return isinstance(route, list) and len(route) == 1 and isinstance(route[0], str) and route[0].isdigit()

    @classmethod
    def get(cls, route: Route, default=None):
        assert cls.is_valid_route(route)
        return cls._register.get(int(route[0]), default)


    @classmethod
    def pop(cls, route: Route, default=None):
        assert cls.is_valid_route(route)
        return cls._register.pop(int(route[0]), default)
