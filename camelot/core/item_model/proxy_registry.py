class ProxyRegistry:
    """Registry to hold proxy objects"""

    _register = {}
    _last_id = 0

    @classmethod
    def register(cls, proxy):
        """Register a proxy

        :return: The id associated with the registered proxy.
        """
        next_id = cls._last_id + 1
        cls._register[next_id] = proxy
        cls._last_id = next_id
        return next_id

    @classmethod
    def get(cls, key, default=None):
        return cls._register.get(key, default)

    @classmethod
    def pop(cls, key, default=None):
        return cls._register.pop(key, default)
