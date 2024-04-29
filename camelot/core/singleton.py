from .qt import QtCore

class Singleton(type):
    """
    Specialized metaclass that makes a class a 'true' singleton.
    A singleton is special in that it should be created only once, and a metaclass allows for easy customization of the class creation.
    This approach has advantages over other singleton implementations (decorator, module, base class, borg)
    in that it's a true class, includes state, auto-magically covers inheritance and uses metaclasses for what their designed to do.
    It also does not violate the 'Single Responsibility Principle', stating that each class should do only one thing.
    This metaclass enforces the singleton pattern without the created class and subclasses needing to be aware that they are singletons.

    :example:
        | class A(object):
        |     pass
        |
        | class B(object, metaclass=Singleton):
        |
        |   def __init__(self):
        |       self.a = A()
        |
        | assert B() == B()
        | assert B().a. == B().a
    """

    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]

class QSingleton(type(QtCore.QObject), Singleton):
    pass