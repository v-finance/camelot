'''
Some helper functions and classes related
to threading issues
'''

from PyQt4 import QtCore

def synchronized( original_function ):
    """Decorator for synchronized access to an object, the object should
    have an attribute _mutex which is of type QMutex
    """

    from functools import wraps

    @wraps( original_function )
    def wrapper(self, *args, **kwargs):
        locker = QtCore.QMutexLocker(self._mutex)
        result = original_function(self, *args, **kwargs)
        locker.unlock()
        return result

    return wrapper
