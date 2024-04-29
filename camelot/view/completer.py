

class AbstractCompleter:
    """
    Completers can have a state which is set by set_state.
    """

    completers = dict()

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        cls.completers[cls.__name__] = cls

    @classmethod
    def get_completer(cls, completer_type, parent=None):
        if completer_type is None:
            return None
        return cls.completers[completer_type](parent)

    def set_state(self, state):
        pass
